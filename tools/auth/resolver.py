"""Resolve a `CredentialProvider` for a named target system from YAML config."""
from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - hit only when tooling deps missing
    raise RuntimeError("PyYAML required; run `pip install -r tools/requirements.txt`")

from .base import CredentialProvider, ResolvedCredential
from .mtls import MTLSClientProvider
from .oauth2 import OAuth2ClientCredentialsProvider
from .service_account import ServiceAccountProvider


PROVIDER_CLASSES: dict[str, type[CredentialProvider]] = {
    "service-account": ServiceAccountProvider,
    "oauth2": OAuth2ClientCredentialsProvider,
    "mtls": MTLSClientProvider,
}


class AuthConfigError(ValueError):
    """Raised when the auth config is missing, malformed, or references an unknown profile."""


def load_auth_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise AuthConfigError(f"auth config not found at {path}")
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise AuthConfigError(f"{path}: top-level must be a mapping")
    if "systems" not in data or not isinstance(data["systems"], dict):
        raise AuthConfigError(f"{path}: missing 'systems' block")
    return data


def build_provider(system: str, spec: dict[str, Any]) -> CredentialProvider:
    profile = spec.get("profile")
    if profile not in PROVIDER_CLASSES:
        raise AuthConfigError(
            f"system '{system}': profile '{profile}' is not one of {sorted(PROVIDER_CLASSES)}"
        )
    cls = PROVIDER_CLASSES[profile]
    kwargs = {k: v for k, v in spec.items() if k != "profile"}
    try:
        return cls(**kwargs)
    except TypeError as e:
        raise AuthConfigError(f"system '{system}': invalid fields for profile '{profile}': {e}") from e


def resolve_credentials(system: str, config: dict[str, Any]) -> ResolvedCredential:
    """Resolve credentials for one system. Typical callers:

        cfg = load_auth_config(Path("config/auth.yaml"))
        cred = resolve_credentials("servicenow", cfg)
        headers = cred.headers

    Providers are not cached across calls because a fresh resolution is
    cheap (env read + optional token refresh); callers that want cross-
    call caching should hold a provider instance themselves.
    """
    systems = config.get("systems") or {}
    spec = systems.get(system)
    if not spec:
        raise AuthConfigError(f"no auth config for system '{system}'")
    provider = build_provider(system, spec)
    return provider.resolve(system)
