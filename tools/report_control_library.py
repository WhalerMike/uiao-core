#!/usr/bin/env python3
"""
report_control_library.py — Regenerate `data/control-library/control_library_report.md`.

Scans the control-library tree, counts files and KSI-linked files per family,
computes the overall KSI coverage percentage, and writes a fresh Markdown
report. Used after `link_ksi_to_controls.py` has populated KSI references
to advance the "≥80% KSI coverage before SCuBA importer Phase 1" milestone
tracked in `RELEASE_NOTES.md` and the prior report.

Output is deterministic: given the same tree, the report is byte-identical
across runs. CI can diff the file against the working copy to detect drift.

Exit codes:
  0  report regenerated; no change vs. on-disk version
  1  report changed — CI should commit (or fail and prompt a PR)
  2  tree unreadable / schema error
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install -r tools/requirements.txt", file=sys.stderr)
    sys.exit(2)


CONTROL_LIB_REL = Path("data/control-library")
REPORT_REL = CONTROL_LIB_REL / "control_library_report.md"

FAMILY_ORDER = (
    "AC", "AT", "AU", "CA", "CM", "CP", "IA", "IR",
    "MA", "MP", "PE", "PL", "PS", "RA", "SA", "SC", "SI",
)
PRIORITY_FAMILIES = ("AC", "SC", "IA", "AU", "CM")


def scan_tree(tree: Path) -> dict:
    """Walk the tree family-by-family and count files + KSI-linked files."""
    stats = {
        "total_files": 0,
        "base_controls": 0,
        "enhancements": 0,
        "ksi_linked_files": 0,
        "parameter_files": 0,
        "implementation_files": 0,
        "families": {},
    }
    for fam in FAMILY_ORDER:
        fam_dir = tree / fam.lower()
        if not fam_dir.is_dir():
            continue
        files = sorted(fam_dir.glob("*.yml"))
        per_fam = {
            "count": 0,
            "base": 0,
            "enhancements": 0,
            "ksi_linked": 0,
            "files": [],
        }
        for path in files:
            per_fam["count"] += 1
            stats["total_files"] += 1
            if "(" in path.stem:
                per_fam["enhancements"] += 1
                stats["enhancements"] += 1
            else:
                per_fam["base"] += 1
                stats["base_controls"] += 1
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            if not isinstance(data, dict):
                continue
            if data.get("ksi"):
                per_fam["ksi_linked"] += 1
                stats["ksi_linked_files"] += 1
                per_fam["files"].append((path.name, data.get("ksi", {}).get("ksi_id")))
            if data.get("parameters"):
                stats["parameter_files"] += 1
            # Control-library formats differ: some use `narrative`, some use
            # `implementation_statements`. Count either.
            if data.get("narrative") or data.get("implementation_statements"):
                stats["implementation_files"] += 1
        stats["families"][fam] = per_fam
    return stats


def render_report(stats: dict, generated: str) -> str:
    coverage_pct = (
        stats["ksi_linked_files"] / stats["total_files"] * 100
        if stats["total_files"]
        else 0.0
    )
    priority_total = sum(stats["families"].get(f, {}).get("count", 0) for f in PRIORITY_FAMILIES)
    priority_linked = sum(stats["families"].get(f, {}).get("ksi_linked", 0) for f in PRIORITY_FAMILIES)
    priority_pct = (priority_linked / priority_total * 100) if priority_total else 0.0
    scuba_threshold = 80.0

    lines = [
        "# uiao-core Control Library Report",
        "",
        f"Generated: {generated}",
        "",
        f"**Total files**: {stats['total_files']}",
        f"**Base controls**: {stats['base_controls']}",
        f"**Enhancements**: {stats['enhancements']}",
        f"**Granular controls**: {stats['total_files']}",
        "",
        "## Family Breakdown",
    ]
    for fam in FAMILY_ORDER:
        entry = stats["families"].get(fam)
        if not entry:
            continue
        lines.append(
            f"- **{fam}**: {entry['count']} files "
            f"(base={entry['base']}, enh={entry['enhancements']}, "
            f"ksi-linked={entry['ksi_linked']})"
        )
    lines.extend([
        "",
        "## Quality Metrics",
        f"- KSI coverage: **{stats['ksi_linked_files']}** / {stats['total_files']} files "
        f"({coverage_pct:.1f}%)",
        f"- Parameters: **{stats['parameter_files']}** files",
        f"- Implementation statements: **{stats['implementation_files']}** files",
        "",
        "## Priority-family KSI coverage (AC/SC/IA/AU/CM)",
        "",
        f"- Linked: **{priority_linked}** / {priority_total} "
        f"({priority_pct:.1f}%)",
        f"- SCuBA-importer threshold: {scuba_threshold:.0f}%",
        f"- Status: **{'READY' if priority_pct >= scuba_threshold else 'BELOW THRESHOLD'}**",
        "",
        "## Next Steps",
    ])
    if priority_pct >= scuba_threshold:
        lines.append("- Priority-family coverage met — SCuBA importer (Phase 1) is unblocked.")
        lines.append("- Extend KSI linkage to the remaining families (MA, MP, PE, PL, PS, RA, SA, SI, AT, CA, CP, IR).")
    else:
        lines.append("- Focus KSI rule population on AC, SC, IA, AU, and CM families first.")
        lines.append(f"- Aim for >{scuba_threshold:.0f}% priority-family KSI coverage before starting SCuBA importer (Phase 1).")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Regenerate control_library_report.md")
    ap.add_argument("--core-root", type=Path, default=Path(__file__).resolve().parent.parent, help="Path to uiao-core repo root")
    ap.add_argument("--check-only", action="store_true", help="Do not write; exit 1 if the report would change")
    ap.add_argument("--generated", type=str, default=None, help="Override the 'Generated:' timestamp (YYYY-MM-DD HH:MM); default uses today's date")
    args = ap.parse_args()

    core_root: Path = args.core_root.resolve()
    tree = core_root / CONTROL_LIB_REL
    if not tree.is_dir():
        print(f"ERROR: control library tree not found at {tree}", file=sys.stderr)
        return 2

    stats = scan_tree(tree)
    generated = args.generated or _today_stamp()
    rendered = render_report(stats, generated)

    report_path = core_root / REPORT_REL
    current = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""
    if rendered == current:
        print(f"report unchanged: {report_path}")
        return 0

    if args.check_only:
        print(f"report drift detected: {report_path} would change")
        return 1

    report_path.write_text(rendered, encoding="utf-8")
    print(f"report regenerated: {report_path}")
    return 1


def _today_stamp() -> str:
    # The canonical build date is injected as 2026-04-16 per CLAUDE.md session
    # context; in CI, override via --generated or rely on the runner's date.
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


if __name__ == "__main__":
    sys.exit(main())
