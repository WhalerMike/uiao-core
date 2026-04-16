"""Deliver a `BridgeEvent` to a Microsoft Logic App HTTP trigger."""
from __future__ import annotations

import abc
import hmac
import hashlib
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .sentinel import BridgeEvent


@dataclass(frozen=True)
class DeliveryResult:
    ok: bool
    status_code: int
    detail: str
    response_body: dict[str, Any] = field(default_factory=dict)


class LogicAppTransport(abc.ABC):
    """Abstract transport. A real deployment uses `HttpTransport`; the
    test suite and CI use `StubTransport` so no real Logic App is needed."""

    @abc.abstractmethod
    def post(self, url: str, headers: dict[str, str], body: bytes) -> DeliveryResult:
        raise NotImplementedError


class HttpTransport(LogicAppTransport):
    """stdlib-backed transport. Targets the Logic App HTTP trigger URL."""

    def __init__(self, timeout_seconds: float = 10.0) -> None:
        self.timeout_seconds = timeout_seconds

    def post(self, url: str, headers: dict[str, str], body: bytes) -> DeliveryResult:
        req = urllib.request.Request(url, data=body, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                try:
                    payload = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    payload = {"raw": raw}
                return DeliveryResult(True, resp.status, "ok", payload)
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace") if e.fp else ""
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {"raw": raw}
            return DeliveryResult(False, e.code, f"HTTPError: {e.reason}", payload)
        except urllib.error.URLError as e:
            return DeliveryResult(False, 0, f"URLError: {e.reason}")


class StubTransport(LogicAppTransport):
    """In-memory transport for tests and pre-agency CI runs. Records all
    delivery attempts so assertions can inspect the request bytes."""

    def __init__(self, response: DeliveryResult | None = None) -> None:
        self.calls: list[tuple[str, dict[str, str], bytes]] = []
        self.response = response or DeliveryResult(True, 202, "accepted", {"stubbed": True})

    def post(self, url: str, headers: dict[str, str], body: bytes) -> DeliveryResult:
        self.calls.append((url, dict(headers), body))
        return self.response


def _sign_body(body: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256)
    return "sha256=" + mac.hexdigest()


def deliver(
    event: BridgeEvent,
    url: str,
    *,
    transport: LogicAppTransport | None = None,
    hmac_secret_env: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> DeliveryResult:
    """Serialize `event`, add `X-UIAO-Signature` (when `hmac_secret_env`
    is provided and the env var is set), and POST via `transport`.

    The signature covers the exact bytes sent. Logic Apps can verify it
    with the shared secret before processing the event.
    """
    if not url:
        return DeliveryResult(False, 0, "logic app URL is empty")
    body = event.to_json().encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "uiao-core-bridge/0.1",
        "X-UIAO-Event-Id": event.event_id,
        "X-UIAO-Source": event.source,
        "X-UIAO-Fingerprint": event.fingerprint(),
        "X-UIAO-Sent-At": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    if hmac_secret_env:
        secret = os.environ.get(hmac_secret_env, "").strip()
        if secret:
            headers["X-UIAO-Signature"] = _sign_body(body, secret)
    if extra_headers:
        headers.update(extra_headers)
    transport = transport or HttpTransport()
    return transport.post(url, headers, body)
