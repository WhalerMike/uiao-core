"""OAuth2 client-credentials provider.

Targets Entra ID / Azure AD v2.0 endpoints. Transport uses `urllib` so
the scaffold carries no runtime dependencies. Swap in `httpx` (already
a candidate for `uiao-impl`) before the agency cutover if richer
retry/backoff behavior is needed.
"""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from .base import CredentialProvider, ResolvedCredential


TokenFetcher = Callable[[str, dict[str, str]], dict]


def _default_token_fetcher(token_endpoint: str, form: dict[str, str]) -> dict:
    body = urllib.parse.urlencode(form).encode("utf-8")
    req = urllib.request.Request(
        token_endpoint,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        raise RuntimeError(f"token endpoint returned {e.code}: {body}") from e


@dataclass
class OAuth2ClientCredentialsProvider(CredentialProvider):
    """Standard OAuth2 client-credentials grant.

    Reads `client_id`, `client_secret`, and `token_endpoint` from the
    config (values may be literal or `env:FOO` references). Caches the
    resulting access token until it's within 60s of expiration.
    """
    profile: str = "oauth2"
    token_endpoint: str = ""
    client_id: str = ""
    client_secret_env: str | None = None
    scope: str = ""
    # Injected for testability. Production: leave as None → stdlib impl.
    token_fetcher: TokenFetcher | None = None

    _cached: ResolvedCredential | None = field(default=None, init=False, repr=False, compare=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False, compare=False)

    def resolve(self, system: str) -> ResolvedCredential:
        with self._lock:
            if self._cached and not self._cached.is_expired():
                return self._cached
            self._cached = self._mint(system)
            return self._cached

    def _mint(self, system: str) -> ResolvedCredential:
        if not self.token_endpoint or not self.client_id or not self.client_secret_env:
            raise RuntimeError(
                f"oauth2 profile for {system} requires token_endpoint, client_id, client_secret_env"
            )
        secret = os.environ.get(self.client_secret_env, "")
        if not secret:
            raise RuntimeError(f"oauth2 profile for {system}: ${self.client_secret_env} is empty")
        form = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": secret,
        }
        if self.scope:
            form["scope"] = self.scope
        fetcher = self.token_fetcher or _default_token_fetcher
        payload = fetcher(self.token_endpoint, form)
        access_token = payload.get("access_token")
        if not access_token:
            raise RuntimeError(f"oauth2 response for {system} did not include access_token: {payload}")
        expires_in = int(payload.get("expires_in", 3600))
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return ResolvedCredential(
            system=system,
            profile=self.profile,
            headers={"Authorization": f"Bearer {access_token}"},
            expires_at=expires_at,
            metadata={
                "token_type": payload.get("token_type", "Bearer"),
                "scope": payload.get("scope", self.scope),
                "endpoint": self.token_endpoint,
            },
        )
