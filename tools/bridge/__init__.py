"""
tools.bridge — Sentinel → Logic App webhook bridge (mock-driven scaffold).

The v1.1 enforcement loop requires Microsoft Sentinel incidents to drive
Logic App workflows in GCC-Moderate (e.g. ServiceNow change tickets,
Intune device isolation, Entra user disablement). This package is the
shape of that bridge, intentionally minimal:

  sentinel.parse_incident_payload  → normalise Sentinel incident JSON into
                                     the canonical `BridgeEvent` shape
  logic_app.deliver               → POST the event to a Logic App trigger
                                     URL with optional HMAC signature
  pipeline.run_bridge             → tie them together; testable via the
                                     injected transport hook

The real sender and the mock are both exercised by the test suite. Until
the agency provisions the Logic App, CI runs the pipeline with a
`StubTransport` so the contract stays verified.
"""
from __future__ import annotations

from .logic_app import DeliveryResult, LogicAppTransport, StubTransport, deliver
from .pipeline import BridgePipeline, run_bridge
from .sentinel import BridgeEvent, parse_incident_payload

__all__ = [
    "BridgeEvent",
    "BridgePipeline",
    "DeliveryResult",
    "LogicAppTransport",
    "StubTransport",
    "deliver",
    "parse_incident_payload",
    "run_bridge",
]
