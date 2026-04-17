"""Abstract credential provider + uniform result shape."""
from __future__ import annotations

import abc
import ssl
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ResolvedCredential:
    """Outcome of credential resolution for a target system.

    `headers` are applied to every outgoing HTTP request. `tls_context`,
    when present, is the `ssl.SSLContext` to use for mTLS.
    `expires_at` is None for credentials that never rotate (static
    tokens, certs) and a datetime for bearer tokens.
    """
    system: str
    profile: str  # "service-account" | "oauth2" | "mtls"
    headers: dict[str, str] = field(default_factory=dict)
    tls_context: ssl.SSLContext | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self, skew_seconds: int = 60) -> bool:
        if self.expires_at is None:
            return False
        now = datetime.now(timezone.utc)
        return (self.expires_at - now).total_seconds() < skew_seconds

    def redacted(self) -> dict[str, Any]:
        """JSON-safe summary suitable for logging. Never emits secrets."""
        safe_headers = {}
        for k, v in self.headers.items():
            if k.lower() in ("authorization", "x-api-key", "cookie"):
                safe_headers[k] = f"<redacted {len(v)} chars>"
            else:
                safe_headers[k] = v
        return {
            "system": self.system,
            "profile": self.profile,
            "headers": safe_headers,
            "tls_context": "present" if self.tls_context else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }


class CredentialProvider(abc.ABC):
    """Abstract base. Concrete providers mint a `ResolvedCredential`."""

    profile: str = "abstract"

    @abc.abstractmethod
    def resolve(self, system: str) -> ResolvedCredential:
        """Return a fresh ResolvedCredential. Providers SHOULD cache and
        refresh internally so callers don't have to reason about TTL."""
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        """Non-secret description of the provider for audit logs."""
        return {"profile": self.profile, "class": type(self).__name__}
