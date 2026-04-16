"""Compose the Sentinel parser + Logic App transport into a single entry point."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .logic_app import DeliveryResult, LogicAppTransport, deliver
from .sentinel import BridgeEvent, SentinelPayloadError, parse_incident_payload


@dataclass
class BridgePipeline:
    """Stateless facade over the bridge steps. Holds the Logic App target
    URL + optional HMAC secret env var so callers can construct once and
    invoke per incoming webhook."""
    logic_app_url: str
    hmac_secret_env: str | None = None
    min_severity: str = "medium"  # drop info/low by default

    # Sentinel severity order; greater-than-or-equal to min_severity is
    # forwarded, everything below is dropped with `ok=False, status=204`
    # so the caller can log the drop.
    _SEVERITY_ORDER = ("info", "low", "medium", "high", "critical")

    def run(
        self,
        payload: dict[str, Any],
        *,
        transport: LogicAppTransport | None = None,
    ) -> tuple[BridgeEvent | None, DeliveryResult]:
        try:
            event = parse_incident_payload(payload)
        except SentinelPayloadError as e:
            return None, DeliveryResult(False, 400, f"malformed payload: {e}")
        if not self._severity_ok(event.severity):
            return event, DeliveryResult(False, 204, f"dropped below min_severity={self.min_severity}")
        result = deliver(
            event,
            self.logic_app_url,
            transport=transport,
            hmac_secret_env=self.hmac_secret_env,
        )
        return event, result

    def _severity_ok(self, sev: str) -> bool:
        try:
            return self._SEVERITY_ORDER.index(sev) >= self._SEVERITY_ORDER.index(self.min_severity)
        except ValueError:
            # Unknown severity → forward (fail-open for safety).
            return True


def run_bridge(
    payload: dict[str, Any],
    logic_app_url: str,
    *,
    hmac_secret_env: str | None = None,
    transport: LogicAppTransport | None = None,
    min_severity: str = "medium",
) -> tuple[BridgeEvent | None, DeliveryResult]:
    """Functional wrapper — parse + deliver in one call."""
    return BridgePipeline(
        logic_app_url=logic_app_url,
        hmac_secret_env=hmac_secret_env,
        min_severity=min_severity,
    ).run(payload, transport=transport)
