#!/usr/bin/env python3
"""
link_ksi_to_controls.py — Populate KSI cross-references in the control library.

Reads the master crosswalk at `rules/ksi/uiao-control-to-ksi-mapping.yaml`
and injects (or refreshes) a `ksi:` block into each matching control file
under `data/control-library/<family>/`. The block is the minimal pointer
needed for downstream tooling (SCuBA importer, dashboard, OSCAL generator)
to resolve the KSI rule that owns a given control:

    ksi:
      ksi_id: KSI-AC-02
      ksi_title: Account Management
      category: iam
      family: AC
      severity: critical
      rule_path: rules/ksi/iam/ksi-ac-02.yaml

The tool is:

  - **Idempotent.** Running it twice on a clean tree produces no changes.
  - **Non-destructive.** Never deletes existing keys. If a `ksi:` block is
    already present, only the individual sub-fields that drifted from the
    crosswalk are updated; user-added keys under `ksi:` are preserved.
  - **Scoped.** Defaults to the FedRAMP Moderate priority families
    (AC, SC, IA, AU, CM). Pass `--family` to override.

Exit codes:
  0  success; no changes written (tree already in sync)
  1  success; one or more files updated (CI should open a PR)
  2  error (crosswalk unreadable, schema mismatch, or family path missing)

USAGE:
    python3 tools/link_ksi_to_controls.py --check-only
    python3 tools/link_ksi_to_controls.py --write
    python3 tools/link_ksi_to_controls.py --write --family ac --family sc --json
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install -r tools/requirements.txt", file=sys.stderr)
    sys.exit(2)


DEFAULT_FAMILIES = ("ac", "sc", "ia", "au", "cm")
CROSSWALK_REL = Path("rules/ksi/uiao-control-to-ksi-mapping.yaml")
CONTROL_LIB_REL = Path("data/control-library")

# Ordered keys we want in the injected ksi: block
KSI_FIELDS = ("ksi_id", "ksi_title", "category", "family", "severity", "rule_path")


@dataclass
class FileAction:
    kind: str  # "linked" | "refreshed" | "unchanged" | "no-mapping" | "malformed"
    path: str
    control_id: str
    detail: str = ""


@dataclass
class Report:
    core_root: str
    families: list[str]
    write: bool
    crosswalk_path: str
    mappings_loaded: int = 0
    files_scanned: int = 0
    actions: list[FileAction] = field(default_factory=list)

    @property
    def files_changed(self) -> int:
        return sum(1 for a in self.actions if a.kind in ("linked", "refreshed"))

    @property
    def exit_code(self) -> int:
        if any(a.kind == "malformed" for a in self.actions):
            return 2
        if self.files_changed > 0:
            return 1 if self.write else 1  # drift detected; either fixed or about to be
        return 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "core_root": self.core_root,
            "families": self.families,
            "write": self.write,
            "crosswalk_path": self.crosswalk_path,
            "mappings_loaded": self.mappings_loaded,
            "files_scanned": self.files_scanned,
            "files_changed": self.files_changed,
            "actions": [dataclasses.asdict(a) for a in self.actions],
            "exit_code": self.exit_code,
        }


def load_crosswalk(path: Path) -> dict[str, dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    mapping = data.get("control_to_ksi") or {}
    if not isinstance(mapping, dict):
        raise ValueError(f"{path}: 'control_to_ksi' block is not a mapping")
    return mapping


def split_leading_comments(text: str) -> tuple[str, str]:
    """Return (comment_header, yaml_body). Preserves the `# ...` prelude some
    control files use to document provenance."""
    lines = text.splitlines(keepends=True)
    header: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped == "" or stripped.isspace():
            header.append(line)
            continue
        break
    return "".join(header), "".join(lines[len(header):])


def infer_family_from_control_id(control_id: str) -> str:
    m = re.match(r"^([A-Z]{2})-", control_id)
    return m.group(1) if m else "??"


def build_ksi_block(mapping_entry: dict[str, Any], control_id: str) -> dict[str, Any]:
    family = mapping_entry.get("family") or infer_family_from_control_id(control_id)
    block = {
        "ksi_id": mapping_entry.get("ksi_id"),
        "ksi_title": mapping_entry.get("ksi_title"),
        "category": mapping_entry.get("category"),
        "family": family,
        "severity": mapping_entry.get("severity"),
        "rule_path": mapping_entry.get("file"),
    }
    return {k: v for k, v in block.items() if v is not None}


def merge_ksi_block(existing: Any, desired: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Return (merged_block, drifted). User-added fields under `ksi:` are
    preserved, canonical fields are overwritten from the crosswalk."""
    if not isinstance(existing, dict):
        return desired, True
    merged = dict(existing)
    drifted = False
    for k, v in desired.items():
        if merged.get(k) != v:
            merged[k] = v
            drifted = True
    # Re-order: canonical keys first (in KSI_FIELDS order), extras appended
    ordered: dict[str, Any] = {}
    for k in KSI_FIELDS:
        if k in merged:
            ordered[k] = merged[k]
    for k, v in merged.items():
        if k not in ordered:
            ordered[k] = v
    return ordered, drifted


def render_ksi_block(block: dict[str, Any]) -> str:
    """Render the injected `ksi:` mapping as a textual YAML block with
    2-space indent. Used so the rest of the file is preserved verbatim —
    no reserialization of unrelated keys, no stylistic diff noise."""
    lines = ["ksi:"]
    for k in KSI_FIELDS:
        if k in block:
            lines.append(f"  {k}: {_scalar(block[k])}")
    # Preserve any non-canonical sub-keys the author added
    for k, v in block.items():
        if k in KSI_FIELDS:
            continue
        lines.append(f"  {k}: {_scalar(v)}")
    return "\n".join(lines) + "\n"


def _scalar(value: Any) -> str:
    """Emit a YAML-safe scalar for single-line values. Strings that need
    quoting get double-quoted; everything else is dumped raw via PyYAML."""
    if isinstance(value, str) and _needs_quote(value):
        return yaml.safe_dump(value, default_style='"').strip().rstrip("\n").rstrip("...").strip()
    dumped = yaml.safe_dump(value, default_flow_style=True).strip()
    # safe_dump appends trailing newlines and "..." for plain scalars; trim.
    return dumped.rstrip("\n").rstrip("...").strip()


_QUOTE_CHARS = set(":#&*!|>'\"%@`,[]{}")


def _needs_quote(s: str) -> bool:
    if not s:
        return True
    if s[0] in "-?:" or s[0].isspace() or s[-1].isspace():
        return True
    return any(ch in _QUOTE_CHARS for ch in s)


def process_file(path: Path, crosswalk: dict[str, dict[str, Any]], write: bool, report: Report) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        report.actions.append(FileAction("malformed", str(path), path.stem, f"read error: {e}"))
        return

    header, body = split_leading_comments(text)
    try:
        doc = yaml.safe_load(body) if body.strip() else {}
    except yaml.YAMLError as e:
        report.actions.append(FileAction("malformed", str(path), path.stem, f"YAML parse error: {e}"))
        return

    if not isinstance(doc, dict):
        report.actions.append(FileAction("malformed", str(path), path.stem, "top-level is not a mapping"))
        return

    control_id = doc.get("control_id") or doc.get("control-id") or path.stem
    entry = crosswalk.get(control_id)
    if entry is None:
        report.actions.append(FileAction("no-mapping", str(path), control_id, f"no crosswalk entry for {control_id}"))
        return

    desired = build_ksi_block(entry, control_id)
    merged, drifted = merge_ksi_block(doc.get("ksi"), desired)

    had_block = "ksi" in doc
    if not drifted and had_block:
        report.actions.append(FileAction("unchanged", str(path), control_id))
        return

    new_block_text = render_ksi_block(merged)
    if write:
        new_text = _splice_ksi_block(text, new_block_text, had_block)
        path.write_text(new_text, encoding="utf-8")

    kind = "refreshed" if had_block else "linked"
    detail = f"ksi_id={merged['ksi_id']}" + (" (drift)" if had_block else "")
    report.actions.append(FileAction(kind, str(path), control_id, detail))


def _splice_ksi_block(text: str, new_block_text: str, had_block: bool) -> str:
    """Return a new file body with the canonical `ksi:` block either appended
    (if not present) or replaced in place. Never touches unrelated bytes."""
    if not had_block:
        if text and not text.endswith("\n"):
            text += "\n"
        return text + new_block_text

    lines = text.splitlines(keepends=True)
    # Find the line that starts the existing `ksi:` top-level key.
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^ksi\s*:\s*(#.*)?$", line) or re.match(r"^ksi\s*:\s*\{", line):
            start = i
            break
    if start is None:
        # Fallback: append.
        if text and not text.endswith("\n"):
            text += "\n"
        return text + new_block_text

    # The block continues until the next top-level key (non-indented, non-blank,
    # non-comment) or EOF.
    end = len(lines)
    for j in range(start + 1, len(lines)):
        line = lines[j]
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[0] not in " \t":
            end = j
            break

    return "".join(lines[:start]) + new_block_text + "".join(lines[end:])


def scan_family(core_root: Path, family: str, crosswalk: dict[str, dict[str, Any]], write: bool, report: Report) -> None:
    fam_dir = core_root / CONTROL_LIB_REL / family.lower()
    if not fam_dir.is_dir():
        report.actions.append(FileAction("malformed", str(fam_dir), family.upper(), "family directory missing"))
        return
    for path in sorted(fam_dir.glob("*.yml")):
        report.files_scanned += 1
        process_file(path, crosswalk, write, report)


def render_human(report: Report) -> str:
    lines = [f"link_ksi_to_controls — write={report.write}"]
    lines.append(f"  core: {report.core_root}")
    lines.append(f"  crosswalk: {report.crosswalk_path} ({report.mappings_loaded} mappings)")
    lines.append(f"  families: {', '.join(report.families)}")
    lines.append(f"  files scanned: {report.files_scanned}")
    lines.append(f"  files changed: {report.files_changed}")
    counts: dict[str, int] = {}
    for a in report.actions:
        counts[a.kind] = counts.get(a.kind, 0) + 1
    for kind, n in sorted(counts.items()):
        lines.append(f"    [{kind:12s}] {n}")
    if any(a.kind == "malformed" for a in report.actions):
        lines.append("  MALFORMED files (blocking):")
        for a in report.actions:
            if a.kind == "malformed":
                lines.append(f"    - {a.path}: {a.detail}")
    lines.append(f"  exit-code: {report.exit_code}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Populate KSI cross-references in the control library")
    ap.add_argument("--core-root", type=Path, default=Path(__file__).resolve().parent.parent, help="Path to uiao-core repo root")
    ap.add_argument("--family", action="append", default=None, help="Control family to process (lowercase, e.g. ac). Repeat. Default: ac,sc,ia,au,cm")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Apply changes (default behaviour)")
    mode.add_argument("--check-only", action="store_true", help="Report drift without writing")
    ap.add_argument("--json", action="store_true", help="Emit machine-readable JSON report on stdout")
    args = ap.parse_args()

    core_root: Path = args.core_root.resolve()
    families = [f.lower() for f in (args.family or DEFAULT_FAMILIES)]
    write = not args.check_only

    crosswalk_path = core_root / CROSSWALK_REL
    if not crosswalk_path.is_file():
        print(f"ERROR: crosswalk not found at {crosswalk_path}", file=sys.stderr)
        return 2

    try:
        crosswalk = load_crosswalk(crosswalk_path)
    except (yaml.YAMLError, ValueError) as e:
        print(f"ERROR: failed to load crosswalk: {e}", file=sys.stderr)
        return 2

    report = Report(
        core_root=str(core_root),
        families=families,
        write=write,
        crosswalk_path=str(crosswalk_path),
        mappings_loaded=len(crosswalk),
    )

    for family in families:
        scan_family(core_root, family, crosswalk, write, report)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(render_human(report))

    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
