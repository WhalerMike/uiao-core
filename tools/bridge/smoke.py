#!/usr/bin/env python3
"""
tools/bridge/smoke.py — Pre-agency smoke test for the Sentinel → Logic App bridge.

Exercises the full bridge path end-to-end using `StubTransport` so nothing
leaves the runner. Loads one or more Sentinel incident fixture payloads,
runs them through `BridgePipeline`, and asserts that:

  1. Every fixture parses without error (or is explicitly tagged as
     `expect_parse_failure: true`).
  2. Fixtures at or above `min_severity` reach the transport.
  3. Fixtures below `min_severity` are dropped with HTTP 204.
  4. The HMAC signature appears iff `UIAO_BRIDGE_HMAC_SECRET` is set.

Exit codes:
  0  all fixtures behaved as expected
  1  one or more mismatches — CI should fail
  2  fixture directory missing / malformed JSON in fixture

USAGE:
    python3 tools/bridge/smoke.py                          # uses default fixtures
    python3 tools/bridge/smoke.py --fixture-dir path/to/
    UIAO_BRIDGE_HMAC_SECRET=xxx python3 tools/bridge/smoke.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Local-import the package so the tool is runnable as `python tools/bridge/smoke.py`
# without requiring the project to be installed.
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from tools.bridge import BridgePipeline, StubTransport  # noqa: E402
from tools.bridge.sentinel import SentinelPayloadError  # noqa: E402


DEFAULT_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "sentinel_incidents"
HMAC_ENV = "UIAO_BRIDGE_HMAC_SECRET"


@dataclass
class FixtureResult:
    name: str
    ok: bool
    detail: str


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_one(fixture: dict[str, Any], name: str, pipeline: BridgePipeline) -> FixtureResult:
    expectations = fixture.get("_expect") or {}
    payload = fixture.get("payload") or fixture
    expect_forward = bool(expectations.get("forward", True))
    expect_parse_failure = bool(expectations.get("parse_failure", False))
    expected_severity = expectations.get("severity")

    transport = StubTransport()
    try:
        event, result = pipeline.run(payload, transport=transport)
    except SentinelPayloadError as e:
        if expect_parse_failure:
            return FixtureResult(name, True, f"expected parse failure: {e}")
        return FixtureResult(name, False, f"unexpected parse failure: {e}")

    if expect_parse_failure:
        if event is None:
            return FixtureResult(name, True, f"parse failure reported (status={result.status_code})")
        return FixtureResult(name, False, "expected parse failure, but parsing succeeded")

    if event is None:
        return FixtureResult(name, False, f"parse returned None: {result.detail}")

    if expected_severity and event.severity != expected_severity:
        return FixtureResult(
            name, False,
            f"severity mismatch: got '{event.severity}', expected '{expected_severity}'",
        )

    if expect_forward:
        if not result.ok:
            return FixtureResult(name, False, f"expected forward, got status={result.status_code}: {result.detail}")
        if len(transport.calls) != 1:
            return FixtureResult(name, False, f"expected 1 delivery, recorded {len(transport.calls)}")
        _url, headers, body = transport.calls[0]
        if os.environ.get(HMAC_ENV) and "X-UIAO-Signature" not in headers:
            return FixtureResult(name, False, "HMAC secret set but signature header missing")
        if not os.environ.get(HMAC_ENV) and "X-UIAO-Signature" in headers:
            return FixtureResult(name, False, "HMAC secret unset but signature header present")
        if b'"title":' not in body:
            return FixtureResult(name, False, "delivered body missing normalized 'title' field")
        return FixtureResult(name, True, f"forwarded (severity={event.severity}, fp={event.fingerprint()[:8]})")
    else:
        if result.status_code != 204 or transport.calls:
            return FixtureResult(name, False, f"expected drop, got status={result.status_code}, calls={len(transport.calls)}")
        return FixtureResult(name, True, f"dropped as expected (severity={event.severity})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Smoke-test the Sentinel → Logic App bridge end-to-end")
    ap.add_argument("--fixture-dir", type=Path, default=DEFAULT_FIXTURE_DIR, help="Directory of *.json fixture files")
    ap.add_argument("--min-severity", default="medium", help="Pipeline minimum severity gate (default: medium)")
    ap.add_argument("--logic-app-url", default="https://stub.logic.invalid/api/trigger", help="Stub URL (never contacted)")
    args = ap.parse_args()

    if not args.fixture_dir.is_dir():
        print(f"ERROR: fixture directory not found: {args.fixture_dir}", file=sys.stderr)
        return 2

    fixtures = sorted(args.fixture_dir.glob("*.json"))
    if not fixtures:
        print(f"ERROR: no *.json fixtures in {args.fixture_dir}", file=sys.stderr)
        return 2

    pipeline = BridgePipeline(
        logic_app_url=args.logic_app_url,
        hmac_secret_env=HMAC_ENV,
        min_severity=args.min_severity,
    )

    results: list[FixtureResult] = []
    for path in fixtures:
        try:
            fx = load_fixture(path)
        except json.JSONDecodeError as e:
            results.append(FixtureResult(path.name, False, f"malformed JSON: {e}"))
            continue
        results.append(run_one(fx, path.name, pipeline))

    print(f"bridge smoke — fixtures={len(results)} dir={args.fixture_dir}")
    for r in results:
        mark = "OK  " if r.ok else "FAIL"
        print(f"  [{mark}] {r.name}: {r.detail}")
    failures = [r for r in results if not r.ok]
    print(f"  passed={len(results) - len(failures)} failed={len(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
