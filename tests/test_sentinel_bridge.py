"""
Unit tests for tools.bridge — Sentinel → Logic App webhook bridge.

Fully mocked: no network I/O, no real Sentinel payloads. Fixture
payloads shaped from the Sentinel Logic Apps connector webhook schema.
"""
from __future__ import annotations

import hmac
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    "tools.bridge",
    ROOT / "tools" / "bridge" / "__init__.py",
    submodule_search_locations=[str(ROOT / "tools" / "bridge")],
)
assert spec and spec.loader
bridge = importlib.util.module_from_spec(spec)
sys.modules["tools.bridge"] = bridge
spec.loader.exec_module(bridge)


# --- Sample Sentinel incident payloads ---

SENTINEL_HIGH_INCIDENT = {
    "id": "/subscriptions/sub/providers/Microsoft.SecurityInsights/incidents/abc-123",
    "object": {
        "id": "abc-123",
        "properties": {
            "title": "Atlas: Privileged Leaver Detected",
            "severity": "High",
            "status": "New",
            "tactics": ["InitialAccess", "PrivilegeEscalation"],
            "incidentUrl": "https://portal.azure.com/#/incident/abc-123",
            "incidentNumber": 42,
            "createdTimeUtc": "2026-04-16T14:30:00Z",
            "entities": [
                {
                    "kind": "Account",
                    "name": "jane.doe@agency.gov",
                    "properties": {"upnSuffix": "agency.gov"},
                }
            ],
        },
    },
}


SENTINEL_INFO_INCIDENT = {
    "object": {
        "properties": {
            "title": "Atlas: Noise event",
            "severity": "Informational",
            "status": "new",
            "tactics": [],
            "createdTimeUtc": "2026-04-16T15:00:00Z",
        }
    }
}


# --- parse_incident_payload ---

def test_parse_high_incident():
    e = bridge.parse_incident_payload(SENTINEL_HIGH_INCIDENT)
    assert e.source == "sentinel"
    assert e.title == "Atlas: Privileged Leaver Detected"
    assert e.severity == "high"
    assert e.status == "new"
    assert e.tactics == ["InitialAccess", "PrivilegeEscalation"]
    assert e.event_id == "42"
    assert e.incident_url.startswith("https://")
    assert e.observed_at == "2026-04-16T14:30:00Z"
    assert e.entities[0]["kind"] == "Account"


def test_parse_missing_title_raises():
    with pytest.raises(bridge.sentinel.SentinelPayloadError):
        bridge.parse_incident_payload({"object": {"properties": {}}})


def test_parse_tactics_as_comma_string():
    p = {"properties": {"title": "t", "tactics": "DefenseEvasion, Persistence"}}
    e = bridge.parse_incident_payload(p)
    assert e.tactics == ["DefenseEvasion", "Persistence"]


def test_parse_non_object_payload_raises():
    with pytest.raises(bridge.sentinel.SentinelPayloadError):
        bridge.parse_incident_payload([1, 2, 3])  # type: ignore[arg-type]


def test_event_fingerprint_is_stable():
    e1 = bridge.parse_incident_payload(SENTINEL_HIGH_INCIDENT)
    e2 = bridge.parse_incident_payload(SENTINEL_HIGH_INCIDENT)
    assert e1.fingerprint() == e2.fingerprint()


# --- deliver / transport ---

def test_deliver_uses_stub_transport_and_sets_headers(monkeypatch):
    event = bridge.parse_incident_payload(SENTINEL_HIGH_INCIDENT)
    stub = bridge.StubTransport()
    result = bridge.deliver(event, "https://logic.example/api/trigger", transport=stub)
    assert result.ok
    assert result.status_code == 202
    assert len(stub.calls) == 1
    url, headers, body = stub.calls[0]
    assert url == "https://logic.example/api/trigger"
    assert headers["Content-Type"] == "application/json"
    assert headers["X-UIAO-Event-Id"] == "42"
    assert headers["X-UIAO-Source"] == "sentinel"
    assert headers["X-UIAO-Fingerprint"] == event.fingerprint()
    decoded = json.loads(body.decode("utf-8"))
    assert decoded["title"] == event.title


def test_deliver_signs_body_when_secret_set(monkeypatch):
    monkeypatch.setenv("UIAO_BRIDGE_HMAC", "shared-secret")
    event = bridge.parse_incident_payload(SENTINEL_HIGH_INCIDENT)
    stub = bridge.StubTransport()
    bridge.deliver(
        event,
        "https://logic.example/api/trigger",
        transport=stub,
        hmac_secret_env="UIAO_BRIDGE_HMAC",
    )
    _url, headers, body = stub.calls[0]
    assert "X-UIAO-Signature" in headers
    expected = "sha256=" + hmac.new(b"shared-secret", body, hashlib.sha256).hexdigest()
    assert headers["X-UIAO-Signature"] == expected


def test_deliver_skips_signature_when_secret_env_unset(monkeypatch):
    monkeypatch.delenv("UIAO_BRIDGE_HMAC", raising=False)
    event = bridge.parse_incident_payload(SENTINEL_HIGH_INCIDENT)
    stub = bridge.StubTransport()
    bridge.deliver(
        event,
        "https://logic.example/api/trigger",
        transport=stub,
        hmac_secret_env="UIAO_BRIDGE_HMAC",
    )
    _url, headers, _body = stub.calls[0]
    assert "X-UIAO-Signature" not in headers


def test_deliver_empty_url_returns_error():
    event = bridge.parse_incident_payload(SENTINEL_HIGH_INCIDENT)
    result = bridge.deliver(event, "", transport=bridge.StubTransport())
    assert result.ok is False
    assert result.status_code == 0


# --- pipeline ---

def test_pipeline_drops_below_min_severity():
    stub = bridge.StubTransport()
    pipeline = bridge.BridgePipeline(logic_app_url="https://logic.example/x", min_severity="high")
    event, result = pipeline.run(SENTINEL_INFO_INCIDENT, transport=stub)
    assert event is not None and event.severity == "info"
    assert result.ok is False
    assert result.status_code == 204
    assert stub.calls == []


def test_pipeline_forwards_high_incident():
    stub = bridge.StubTransport()
    pipeline = bridge.BridgePipeline(logic_app_url="https://logic.example/x", min_severity="medium")
    event, result = pipeline.run(SENTINEL_HIGH_INCIDENT, transport=stub)
    assert event.severity == "high"
    assert result.ok
    assert len(stub.calls) == 1


def test_pipeline_malformed_payload_returns_400():
    pipeline = bridge.BridgePipeline(logic_app_url="https://logic.example/x")
    event, result = pipeline.run({"not": "a sentinel payload"})
    assert event is None
    assert result.status_code == 400


def test_run_bridge_convenience_wrapper():
    stub = bridge.StubTransport()
    event, result = bridge.run_bridge(
        SENTINEL_HIGH_INCIDENT,
        logic_app_url="https://logic.example/x",
        transport=stub,
        min_severity="low",
    )
    assert result.ok
    assert event.title.startswith("Atlas:")
