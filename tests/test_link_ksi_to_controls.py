"""
Unit tests for tools/link_ksi_to_controls.py.

These operate on temp directories so they never touch the real control-library
tree. They cover:
  - Fresh linking (no ksi block present → appended, original bytes preserved)
  - Idempotency (running twice produces no change)
  - Drift refresh (existing ksi block with stale severity is updated in place)
  - Malformed file handling (top-level non-mapping → reported, not written)
"""
from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "link_ksi_to_controls.py"

spec = importlib.util.spec_from_file_location("link_ksi_to_controls", TOOL)
assert spec and spec.loader
linker = importlib.util.module_from_spec(spec)
sys.modules["link_ksi_to_controls"] = linker
spec.loader.exec_module(linker)


CROSSWALK = textwrap.dedent(
    """
    version: "1.0"
    control_to_ksi:
      AC-2:
        ksi_id: KSI-AC-02
        ksi_title: Account Management
        category: iam
        family: AC
        severity: critical
        file: rules/ksi/iam/ksi-ac-02.yaml
      AC-3:
        ksi_id: KSI-AC-03
        ksi_title: Access Enforcement
        category: iam
        family: AC
        severity: critical
        file: rules/ksi/iam/ksi-ac-03.yaml
    """
).strip() + "\n"


AC2_CONTROL = textwrap.dedent(
    """
    control-id: AC-2
    title: Account Management
    narrative: |
      Multiline content
      preserved verbatim.
    related_controls:
      - AC-3
    """
).strip() + "\n"


@pytest.fixture
def fake_core(tmp_path: Path) -> Path:
    (tmp_path / "rules" / "ksi").mkdir(parents=True)
    (tmp_path / "rules" / "ksi" / "uiao-control-to-ksi-mapping.yaml").write_text(CROSSWALK)
    ac_dir = tmp_path / "data" / "control-library" / "ac"
    ac_dir.mkdir(parents=True)
    (ac_dir / "AC-2.yml").write_text(AC2_CONTROL)
    return tmp_path


def _run(core: Path, extra_argv: list[str]) -> int:
    argv = [
        "link_ksi_to_controls.py",
        "--core-root", str(core),
        "--family", "ac",
        *extra_argv,
    ]
    old = sys.argv
    sys.argv = argv
    try:
        return linker.main()
    finally:
        sys.argv = old


def test_fresh_link_appends_block(fake_core: Path, capsys):
    rc = _run(fake_core, ["--write"])
    assert rc == 1  # files changed
    body = (fake_core / "data/control-library/ac/AC-2.yml").read_text()
    assert body.startswith(AC2_CONTROL)  # original bytes preserved
    assert body.endswith(
        "ksi:\n"
        "  ksi_id: KSI-AC-02\n"
        "  ksi_title: Account Management\n"
        "  category: iam\n"
        "  family: AC\n"
        "  severity: critical\n"
        "  rule_path: rules/ksi/iam/ksi-ac-02.yaml\n"
    )


def test_idempotent_second_run(fake_core: Path, capsys):
    _run(fake_core, ["--write"])
    first = (fake_core / "data/control-library/ac/AC-2.yml").read_text()
    rc2 = _run(fake_core, ["--write"])
    second = (fake_core / "data/control-library/ac/AC-2.yml").read_text()
    assert rc2 == 0
    assert first == second


def test_drift_refresh_updates_in_place(fake_core: Path, capsys):
    path = fake_core / "data/control-library/ac/AC-2.yml"
    path.write_text(
        AC2_CONTROL
        + "ksi:\n"
        "  ksi_id: KSI-AC-02\n"
        "  ksi_title: Account Management\n"
        "  category: iam\n"
        "  family: AC\n"
        "  severity: low\n"  # stale — crosswalk says critical
        "  rule_path: rules/ksi/iam/ksi-ac-02.yaml\n"
        "  operator_note: keep me\n"  # user-added field — must survive
    )
    rc = _run(fake_core, ["--write"])
    assert rc == 1
    body = path.read_text()
    assert "severity: critical" in body
    assert "severity: low" not in body
    assert "operator_note: keep me" in body  # user key preserved


def test_malformed_file_reports_without_writing(fake_core: Path, capsys):
    path = fake_core / "data/control-library/ac/AC-9.yml"
    path.write_text("- not: a mapping\n- just a sequence\n")
    rc = _run(fake_core, ["--write", "--json"])
    out = capsys.readouterr().out
    assert rc == 2
    assert "malformed" in out
    # File untouched
    assert path.read_text() == "- not: a mapping\n- just a sequence\n"


def test_check_only_reports_drift_without_writing(fake_core: Path, capsys):
    rc = _run(fake_core, ["--check-only"])
    body = (fake_core / "data/control-library/ac/AC-2.yml").read_text()
    assert rc == 1
    assert body == AC2_CONTROL  # unchanged on disk


def test_no_mapping_skips_file(fake_core: Path, capsys):
    path = fake_core / "data/control-library/ac/AC-99.yml"
    path.write_text("control-id: AC-99\ntitle: Nonexistent\n")
    rc = _run(fake_core, ["--write", "--json"])
    out = capsys.readouterr().out
    assert "no-mapping" in out
    assert "AC-99" in out
    # AC-2 still gets linked, so rc=1; but AC-99 is untouched.
    assert rc == 1
    assert path.read_text() == "control-id: AC-99\ntitle: Nonexistent\n"
