"""
Smoke tests for tools/verify_canon_sync_roundtrip.py.

These exercise the no-token and stubbed-API paths without ever calling
the real GitHub API. CI cannot and should not hold a PAT during unit
tests, so the real-world checks live in the weekly workflow run.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "verify_canon_sync_roundtrip.py"

spec = importlib.util.spec_from_file_location("verify_canon_sync_roundtrip", TOOL)
assert spec and spec.loader
verifier = importlib.util.module_from_spec(spec)
sys.modules["verify_canon_sync_roundtrip"] = verifier
spec.loader.exec_module(verifier)


def test_no_token_returns_exit_code_2(monkeypatch, capsys):
    monkeypatch.delenv(verifier.TOKEN_ENV_VAR, raising=False)
    monkeypatch.setattr(sys, "argv", ["verify_canon_sync_roundtrip.py", "--skip-dispatch-check", "--json"])
    rc = verifier.main()
    assert rc == 2
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["token_present"] is False
    assert payload["exit_code"] == 2
    assert any(c["name"] == "token-present" and c["ok"] is False for c in payload["checks"])


def test_stubbed_token_happy_path(monkeypatch, capsys):
    """Simulate a well-scoped PAT by stubbing the two stdlib API calls."""
    monkeypatch.setenv(verifier.TOKEN_ENV_VAR, "ghp_stub")

    def fake_api_get(path, token):
        assert token == "ghp_stub"
        if path == "/user":
            return (
                200,
                {"github-authentication-token-expiration": "2099-01-01 00:00:00 UTC"},
                {"login": "stub-user"},
            )
        if path.startswith("/repos/"):
            if path.count("/") == 2:  # /repos/{owner}/{repo}
                return 200, {}, {"permissions": {"push": True, "admin": False}}
            return 200, {}, {}
        return 200, {}, {}

    monkeypatch.setattr(verifier, "_api_get", fake_api_get)
    monkeypatch.setattr(sys, "argv", ["verify_canon_sync_roundtrip.py", "--skip-dispatch-check", "--json"])
    rc = verifier.main()
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["token_present"] is True
    assert payload["token_expires_at"] == "2099-01-01 00:00:00 UTC"
    assert payload["exit_code"] == 0
    names = {c["name"] for c in payload["checks"]}
    assert "token-identity" in names
    assert any(n.startswith("repo-access[") for n in names)


def test_stubbed_token_near_expiration_warns(monkeypatch, capsys):
    monkeypatch.setenv(verifier.TOKEN_ENV_VAR, "ghp_stub_expiring")

    from datetime import datetime, timezone, timedelta
    soon = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S UTC")

    def fake_api_get(path, token):
        if path == "/user":
            return 200, {"github-authentication-token-expiration": soon}, {"login": "stub-user"}
        return 200, {}, {"permissions": {}}

    monkeypatch.setattr(verifier, "_api_get", fake_api_get)
    monkeypatch.setattr(sys, "argv", ["verify_canon_sync_roundtrip.py", "--skip-dispatch-check", "--json"])
    rc = verifier.main()
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert any(c["name"] == "token-expiration-warning" and c["ok"] is False for c in payload["checks"])
