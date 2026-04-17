"""
Unit tests for tools.auth — the v1.1 credential resolver scaffold.

No network I/O. OAuth2 uses an injected token_fetcher; mTLS exercises
only the config-level error path (building a real SSLContext requires
on-disk cert material, out of scope for these tests).
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Import the package — executes tools/auth/__init__.py
spec = importlib.util.spec_from_file_location(
    "tools.auth",
    ROOT / "tools" / "auth" / "__init__.py",
    submodule_search_locations=[str(ROOT / "tools" / "auth")],
)
assert spec and spec.loader
auth = importlib.util.module_from_spec(spec)
sys.modules["tools.auth"] = auth
spec.loader.exec_module(auth)


def test_service_account_basic(monkeypatch):
    monkeypatch.setenv("SN_SVC_USER", "atlas_svc")
    monkeypatch.setenv("SN_SVC_PASS", "supersecret")
    cfg = {
        "systems": {
            "servicenow": {
                "profile": "service-account",
                "username_env": "SN_SVC_USER",
                "password_env": "SN_SVC_PASS",
            }
        }
    }
    cred = auth.resolve_credentials("servicenow", cfg)
    assert cred.profile == "service-account"
    assert cred.headers["Authorization"].startswith("Basic ")
    # redacted() must not leak the token
    assert "supersecret" not in str(cred.redacted())


def test_service_account_api_key(monkeypatch):
    monkeypatch.setenv("PANORAMA_API_KEY", "K3Y-PAN")
    cfg = {
        "systems": {
            "panorama": {
                "profile": "service-account",
                "api_key_env": "PANORAMA_API_KEY",
                "api_key_header": "X-PAN-KEY",
            }
        }
    }
    cred = auth.resolve_credentials("panorama", cfg)
    assert cred.headers == {"X-PAN-KEY": "K3Y-PAN"}


def test_service_account_missing_env_raises(monkeypatch):
    monkeypatch.delenv("MISSING_PASS", raising=False)
    monkeypatch.setenv("MISSING_USER", "x")
    cfg = {
        "systems": {
            "sys": {
                "profile": "service-account",
                "username_env": "MISSING_USER",
                "password_env": "MISSING_PASS",
            }
        }
    }
    with pytest.raises(RuntimeError, match="MISSING_PASS"):
        auth.resolve_credentials("sys", cfg)


def test_oauth2_client_credentials_caches_token(monkeypatch):
    monkeypatch.setenv("CLIENT_SECRET", "shh")
    calls = []

    def fake_fetcher(endpoint, form):
        calls.append(form)
        return {"access_token": "TOK", "expires_in": 3600, "token_type": "Bearer"}

    provider = auth.OAuth2ClientCredentialsProvider(
        token_endpoint="https://login.example/token",
        client_id="cid",
        client_secret_env="CLIENT_SECRET",
        scope="https://api/.default",
        token_fetcher=fake_fetcher,
    )
    c1 = provider.resolve("entra")
    c2 = provider.resolve("entra")
    assert c1.headers == {"Authorization": "Bearer TOK"}
    assert c1.expires_at is not None and c1.expires_at > datetime.now(timezone.utc)
    # Second call reuses the cached token — fetcher invoked once only.
    assert len(calls) == 1
    assert c1 is c2


def test_oauth2_refresh_when_expired(monkeypatch):
    monkeypatch.setenv("CLIENT_SECRET", "shh")
    tokens = iter([
        {"access_token": "OLD", "expires_in": 10, "token_type": "Bearer"},
        {"access_token": "NEW", "expires_in": 3600, "token_type": "Bearer"},
    ])

    provider = auth.OAuth2ClientCredentialsProvider(
        token_endpoint="https://login.example/token",
        client_id="cid",
        client_secret_env="CLIENT_SECRET",
        token_fetcher=lambda e, f: next(tokens),
    )
    c1 = provider.resolve("entra")
    assert c1.headers["Authorization"] == "Bearer OLD"
    # Force expiration
    provider._cached = auth.ResolvedCredential(
        system="entra",
        profile="oauth2",
        headers=c1.headers,
        expires_at=datetime(2000, 1, 1, tzinfo=timezone.utc),
    )
    c2 = provider.resolve("entra")
    assert c2.headers["Authorization"] == "Bearer NEW"


def test_oauth2_missing_secret_raises(monkeypatch):
    monkeypatch.delenv("CLIENT_SECRET", raising=False)
    provider = auth.OAuth2ClientCredentialsProvider(
        token_endpoint="https://login.example/token",
        client_id="cid",
        client_secret_env="CLIENT_SECRET",
        token_fetcher=lambda e, f: {"access_token": "x"},
    )
    with pytest.raises(RuntimeError, match="CLIENT_SECRET"):
        provider.resolve("entra")


def test_mtls_missing_cert_raises():
    provider = auth.MTLSClientProvider(
        cert_path="/no/such/cert.crt",
        key_path="/no/such/key.key",
    )
    with pytest.raises(RuntimeError, match="cert_path"):
        provider.resolve("cyberark")


def test_resolver_unknown_profile_raises():
    cfg = {"systems": {"x": {"profile": "magic"}}}
    with pytest.raises(auth.AuthConfigError, match="magic"):
        auth.resolve_credentials("x", cfg)


def test_resolver_unknown_system_raises():
    cfg = {"systems": {"known": {"profile": "service-account", "api_key_env": "K"}}}
    with pytest.raises(auth.AuthConfigError, match="unknown"):
        auth.resolve_credentials("unknown", cfg)


def test_load_auth_config_roundtrips_example(tmp_path, monkeypatch):
    # Drop a minimal config that uses the example shape
    cfg_path = tmp_path / "auth.yaml"
    cfg_path.write_text(
        "systems:\n"
        "  servicenow:\n"
        "    profile: service-account\n"
        "    username_env: U\n"
        "    password_env: P\n"
    )
    cfg = auth.load_auth_config(cfg_path)
    monkeypatch.setenv("U", "user")
    monkeypatch.setenv("P", "pass")
    cred = auth.resolve_credentials("servicenow", cfg)
    assert cred.profile == "service-account"
    assert cred.system == "servicenow"


def test_resolved_credential_redacts_authorization():
    cred = auth.ResolvedCredential(
        system="sys",
        profile="oauth2",
        headers={"Authorization": "Bearer secret-token-value"},
    )
    red = cred.redacted()
    assert "secret-token-value" not in str(red)
    assert red["headers"]["Authorization"].startswith("<redacted")
