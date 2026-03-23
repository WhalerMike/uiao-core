"""OSCAL POA&M (Plan of Action & Milestones) generator.

Migrated from scripts/generate_poam.py into the uiao_core package.
Auto-detects gaps from unified_compliance_matrix and fedramp-20x
mandatory requirements, then exports OSCAL 1.0 POA&M JSON.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from uiao_core.utils.context import get_settings, load_context


# ---------------------------------------------------------------------------
# Gap detection
# ---------------------------------------------------------------------------
def detect_gaps(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Auto-detect gaps from canon data."""
    gaps: list[dict[str, Any]] = []

    matrix = context.get("unified_compliance_matrix", [])
    if not isinstance(matrix, list):
        matrix = []

    fedramp = context.get("fedramp_20x_config", {})
    if not isinstance(fedramp, dict):
        fedramp = {}
    core_mappings = fedramp.get("core_mappings", [])
    if not isinstance(core_mappings, list):
        core_mappings = []

    # Detect incomplete maturity levels
    for entry in matrix:
        if not isinstance(entry, dict):
            continue
        maturity = entry.get("cisa_maturity", "")
        if maturity in ("Initial", "Developing", ""):
            gaps.append({
                "title": f"Low maturity: {entry.get('category', 'Unknown')}",
                "description": (
                    f"CISA maturity is '{maturity}' for category "
                    f"'{entry.get('category', 'N/A')}'. "
                    f"Controls: {entry.get('nist_controls', [])}"
                ),
                "risk_level": "moderate" if maturity == "Developing" else "high",
                "related_controls": entry.get("nist_controls", []),
            })

    # Detect missing KSI evidence
    for m in core_mappings:
        if not isinstance(m, dict):
            continue
        evidence = m.get("evidence_source", "")
        if not evidence or str(evidence).strip() == "":
            gaps.append({
                "title": f"Missing evidence: {m.get('concept', 'Unknown')}",
                "description": (
                    f"No evidence source defined for KSI concept "
                    f"'{m.get('concept', 'N/A')}' "
                    f"(control: {m.get('nist_rev5_control', 'N/A')})"
                ),
                "risk_level": "moderate",
                "related_controls": [m.get("nist_rev5_control", "")],
            })

    # Detect inventory gaps from core-stack.yml
    core_stack = context.get("core_stack", [])
    if not isinstance(core_stack, list):
        core_stack = []
    inventory_items = context.get("inventory_items", [])
    if not isinstance(inventory_items, list):
        inventory_items = []
    # Collect the set of pillars covered by inventory items
    covered_pillars: set[str] = set()
    for inv in inventory_items:
        if not isinstance(inv, dict):
            continue
        for comp_ref in inv.get("implemented_components", []):
            if isinstance(comp_ref, str) and comp_ref.startswith("component-"):
                covered_pillars.add(comp_ref[len("component-"):])
    # Flag any core-stack component whose pillar has no inventory coverage
    for stack_item in core_stack:
        if not isinstance(stack_item, dict):
            continue
        item_id = stack_item.get("id", "unknown")
        item_pillar = str(stack_item.get("pillar", "")).lower()
        if item_pillar and item_pillar not in covered_pillars:
            gaps.append({
                "title": f"No inventory coverage: {stack_item.get('name', item_id)}",
                "description": (
                    f"Core stack component '{stack_item.get('name', item_id)}' "
                    f"(id: {item_id}, pillar: {item_pillar}) has no corresponding "
                    f"inventory item in inventory-items.yml."
                ),
                "risk_level": "moderate",
                "related_controls": [],
                "source": "core-stack-inventory-check",
            })

    return gaps


# ---------------------------------------------------------------------------
# POA&M builder
# ---------------------------------------------------------------------------
def build_poam(
    context: dict[str, Any],
    manual_findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build OSCAL POA&M from detected gaps and optional manual findings."""
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    gaps = detect_gaps(context)
    if manual_findings:
        gaps.extend(manual_findings)

    poam_items: list[dict[str, Any]] = []
    for i, gap in enumerate(gaps, start=1):
        related = gap.get("related_controls", [])
        poam_items.append({
            "uuid": str(uuid.uuid4()),
            "title": gap.get("title", f"Finding {i}"),
            "description": gap.get("description", "No description"),
            "props": [
                {"name": "risk-level", "value": gap.get("risk_level", "moderate")},
                {"name": "finding-id", "value": f"POAM-{i:04d}"},
            ],
            "related-observations": [
                {"description": f"Related NIST controls: {', '.join(related)}"}
            ] if related else [],
        })

    poam: dict[str, Any] = {
        "uuid": str(uuid.uuid4()),
        "metadata": {
            "title": "UIAO Plan of Action & Milestones",
            "version": "1.0",
            "oscal-version": "1.0.4",
            "last-modified": now_iso,
            "published": now_iso,
        },
        "poam-items": poam_items,
    }
    return poam


def build_poam_export(
    canon_path: str | Path | None = None,
    data_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    manual_findings: list[dict[str, Any]] | None = None,
) -> Path:
    """Build and export POA&M JSON. Returns path to generated file.

    Manual findings from ``data/poam-findings.yml`` are loaded automatically
    and merged with any *manual_findings* passed by the caller.
    """
    settings = get_settings()
    if output_dir is None:
        output_dir = settings.project_root / "exports" / "oscal"
    output_dir = Path(output_dir)

    context = load_context(canon_path, data_dir)

    # Merge YAML-defined manual findings from poam-findings.yml
    yaml_findings: list[dict[str, Any]] = []
    raw_findings = context.get("poam_findings", [])
    if isinstance(raw_findings, list):
        for f in raw_findings:
            if isinstance(f, dict):
                yaml_findings.append({
                    "title": f.get("title", ""),
                    "description": f.get("description", ""),
                    "risk_level": f.get("severity", "moderate"),
                    "related_controls": f.get("control-ids", []),
                    "source": f.get("source", "poam-findings.yml"),
                })
    all_manual: list[dict[str, Any]] = yaml_findings + (manual_findings or [])

    poam = build_poam(context, all_manual if all_manual else None)

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "uiao-poam.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"plan-of-action-and-milestones": poam}, f, indent=2)
    return json_path
