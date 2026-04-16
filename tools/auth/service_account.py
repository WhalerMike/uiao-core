"""Service-account provider — the current (pre-agency) credential path."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from .base import CredentialProvider, ResolvedCredential


@dataclass
class ServiceAccountProvider(CredentialProvider):
    """Reads a username/password, API key, or bearer token from env vars.

    One of the following field groups must be set on the config:
      - `username_env` + `password_env`  → HTTP Basic
      - `api_key_env`                    → X-API-Key header
      - `bearer_token_env`               → Authorization: Bearer
    """
    profile: str = "service-account"
    username_env: str | None = None
    password_env: str | None = None
    api_key_env: str | None = None
    api_key_header: str = "X-API-Key"
    bearer_token_env: str | None = None

    def resolve(self, system: str) -> ResolvedCredential:
        headers: dict[str, str] = {}
        if self.username_env and self.password_env:
            u = os.environ.get(self.username_env, "")
            p = os.environ.get(self.password_env, "")
            if not u or not p:
                raise RuntimeError(
                    f"service-account for {system} requires {self.username_env} and {self.password_env}"
                )
            token = base64.b64encode(f"{u}:{p}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        elif self.api_key_env:
            key = os.environ.get(self.api_key_env, "")
            if not key:
                raise RuntimeError(f"service-account for {system} requires {self.api_key_env}")
            headers[self.api_key_header] = key
        elif self.bearer_token_env:
            tok = os.environ.get(self.bearer_token_env, "")
            if not tok:
                raise RuntimeError(f"service-account for {system} requires {self.bearer_token_env}")
            headers["Authorization"] = f"Bearer {tok}"
        else:
            raise RuntimeError(
                f"service-account profile for {system} has no credential source configured"
            )
        return ResolvedCredential(
            system=system,
            profile=self.profile,
            headers=headers,
            metadata={"source": "env-var"},
        )
