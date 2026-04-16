"""Parse Microsoft Sentinel incident webhook payloads into a canonical shape."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


SENTINEL_SEVERITY_MAP = {
    "informational": "info",
    "low": "low",
    "medium": "medium",
    "high": "high",
    # Sentinel doesn't emit "critical"; reserved for future vendor alignment.
}


@dataclass(frozen=True)
class BridgeEvent:
    """Canonical shape passed to every downstream transport.

    Stable across Sentinel, future third-party sources (e.g. Splunk), and
    unit tests. Every field is JSON-serializable; no datetime objects
    cross the boundary to the transport layer.
    """
    event_id: str
    source: str  # e.g. "sentinel"
    title: str
    severity: str
    status: str
    tactics: list[str]
    incident_url: str | None
    observed_at: str  # ISO 8601 UTC
    entities: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Deterministic JSON encoding (sorted keys) for HMAC stability."""
        return json.dumps(self.__dict__, sort_keys=True, separators=(",", ":"))

    def fingerprint(self) -> str:
        """Content hash for deduplication at the Logic App side."""
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()


class SentinelPayloadError(ValueError):
    """Raised when a Sentinel incident payload lacks required fields."""


def _pick(d: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def parse_incident_payload(payload: dict[str, Any]) -> BridgeEvent:
    """Normalise a Sentinel incident/alert webhook body into `BridgeEvent`.

    The Sentinel webhook shape evolves; this parser accepts both the
    Logic Apps connector shape (object.properties.*) and the raw
    `Microsoft.SecurityInsights/incidents` shape. Unknown fields are
    preserved in `raw`.
    """
    if not isinstance(payload, dict):
        raise SentinelPayloadError("payload is not a JSON object")

    props = payload.get("object", {}).get("properties") or payload.get("properties") or payload

    title = _pick(props, "title", "displayName", "IncidentName")
    if not title:
        raise SentinelPayloadError("incident payload missing title/displayName")

    severity_raw = str(_pick(props, "severity", "Severity", default="medium")).strip().lower()
    severity = SENTINEL_SEVERITY_MAP.get(severity_raw, severity_raw or "medium")

    status = str(_pick(props, "status", "IncidentStatus", default="new")).lower()

    tactics = _pick(props, "tactics", "Tactics", default=[]) or []
    if isinstance(tactics, str):
        tactics = [t.strip() for t in tactics.split(",") if t.strip()]
    tactics = list(tactics)

    incident_url = _pick(props, "incidentUrl", "IncidentUrl")
    if not incident_url:
        incident_url = payload.get("object", {}).get("id") or payload.get("id")

    observed_at_raw = _pick(props, "createdTimeUtc", "TimeGenerated", "firstActivityTimeUtc")
    observed_at = _coerce_iso8601(observed_at_raw)

    entities_raw = _pick(props, "entities", "Entities", default=[]) or []
    entities = [_normalise_entity(e) for e in entities_raw if isinstance(e, dict)]

    event_id = str(
        _pick(props, "incidentNumber", "IncidentID", "name")
        or payload.get("id")
        or "unknown"
    )

    return BridgeEvent(
        event_id=event_id,
        source="sentinel",
        title=str(title),
        severity=severity,
        status=status,
        tactics=tactics,
        incident_url=incident_url,
        observed_at=observed_at,
        entities=entities,
        raw=payload,
    )


def _coerce_iso8601(raw: Any) -> str:
    if not raw:
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    if isinstance(raw, str):
        # Normalise trailing "Z"
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        except ValueError:
            return raw
    if isinstance(raw, (int, float)):
        dt = datetime.fromtimestamp(float(raw), tz=timezone.utc)
        return dt.isoformat(timespec="seconds").replace("+00:00", "Z")
    return str(raw)


def _normalise_entity(e: dict[str, Any]) -> dict[str, Any]:
    kind = e.get("kind") or e.get("Type") or "unknown"
    return {
        "kind": kind,
        "name": e.get("name") or e.get("friendlyName") or e.get("Entity"),
        "properties": e.get("properties") or {},
    }
