"""
tools.auth — Unified credential-resolution scaffold for UIAO adapters.

Today the Modernization Atlas stack authenticates to downstream systems
(ServiceNow, Entra ID, InfoBlox, CyberArk, Palo Alto, Sentinel, ...) with
long-lived service-account credentials pulled from `.env` (see
`.env.example`). The v1.1 roadmap calls for replacing those with OAuth2
client-credentials tokens and/or mTLS client certificates, but the
cutover cannot happen before Agency GCC-Moderate provisions the required
app registrations and PKI. See RELEASE_NOTES.md §"Next Steps (v1.1)".

This package is the code-side scaffold for that cutover:

  - `ResolvedCredential` captures the outcome of credential resolution
    in a uniform shape (headers + optional TLS context) so downstream
    HTTP clients don't care which profile was used.
  - `CredentialProvider` is the abstract contract; three providers ship:
    `ServiceAccountProvider`, `OAuth2ClientCredentialsProvider`,
    `MTLSClientProvider`.
  - `resolve_credentials(system, config)` picks a provider based on
    `config/auth.yaml` (see `config/auth.example.yaml` for the shape)
    and returns a `ResolvedCredential`.

No network calls occur at import time. Providers are lazy — a token is
minted only when `ResolvedCredential.headers()` is first called, and
the provider caches it until `expires_at`.

The scaffold is intentionally stdlib-only. When the agency environment
comes online, swap in a richer HTTP client (e.g. httpx) in the OAuth2
provider — the interface does not change.
"""
from __future__ import annotations

from .base import CredentialProvider, ResolvedCredential
from .resolver import AuthConfigError, load_auth_config, resolve_credentials
from .service_account import ServiceAccountProvider
from .oauth2 import OAuth2ClientCredentialsProvider
from .mtls import MTLSClientProvider

__all__ = [
    "CredentialProvider",
    "ResolvedCredential",
    "AuthConfigError",
    "ServiceAccountProvider",
    "OAuth2ClientCredentialsProvider",
    "MTLSClientProvider",
    "resolve_credentials",
    "load_auth_config",
]
