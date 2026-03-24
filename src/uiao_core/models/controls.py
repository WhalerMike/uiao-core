"""Pydantic v2 models for FedRAMP Moderate Rev 5 control catalog.

Supports loading, validating, and rendering NIST SP 800-53 Rev 5 controls
with Jinja2 narrative stub templates and OSCAL parameter assignments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class ControlParameter(BaseModel):
    """An OSCAL set-parameter assignment for a control."""

    param_id: str = Field(..., alias="param_id")
    label: str = ""
    value: str = ""
    remarks: str = ""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ControlEntry(BaseModel):
    """A single FedRAMP control with narrative template and parameters.

    ``narrative_template`` is a Jinja2 template string whose ``{{ var }}``
    placeholders are resolved at render time from context data
    (program.yml, parameters.yml, inventory, etc.).
    """

    id: str
    family: str
    family_name: str = ""
    title: str
    description: str = ""
    narrative_template: str = ""
    parameters: list[ControlParameter] = []
    baseline_impact: str = "MODERATE"
    fedramp_applicable: bool = True
    related_controls: list[str] = []
    implementation_status: str = "implemented"

    model_config = ConfigDict(extra="allow")


class ControlFamily(BaseModel):
    """A family of related controls (e.g., AC, AU, CM)."""

    id: str
    name: str
    controls: list[ControlEntry] = []

    model_config = ConfigDict(extra="allow")


class ControlCatalog(BaseModel):
    """Full FedRAMP Moderate Rev 5 control catalog."""

    title: str = "FedRAMP Moderate Rev 5 Control Catalog"
    version: str = "Rev 5"
    baseline: str = "Moderate"
    oscal_version: str = "1.1.0"
    controls: list[ControlEntry] = []

    model_config = ConfigDict(extra="allow")

    def families(self) -> dict[str, list[ControlEntry]]:
        """Return controls grouped by family ID."""
        result: dict[str, list[ControlEntry]] = {}
        for ctrl in self.controls:
            result.setdefault(ctrl.family, []).append(ctrl)
        return result

    def get_control(self, control_id: str) -> ControlEntry | None:
        """Look up a control by its ID (case-insensitive)."""
        cid = control_id.upper()
        for ctrl in self.controls:
            if ctrl.id.upper() == cid:
                return ctrl
        return None


def load_controls(catalog_path: Path | None = None) -> ControlCatalog:
    """Load and validate the FedRAMP control catalog from YAML.

    Args:
        catalog_path: Path to the controls YAML file.
            Defaults to ``data/fedramp_moderate_rev5_controls.yaml``
            relative to the project root.

    Returns:
        Validated :class:`ControlCatalog` instance.
    """
    if catalog_path is None:
        catalog_path = (
            Path(__file__).resolve().parent.parent.parent.parent.parent
            / "data"
            / "fedramp_moderate_rev5_controls.yaml"
        )
    with catalog_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    # Flatten per-family controls into a single controls list if needed
    if "families" in raw and "controls" not in raw:
        controls: list[dict[str, Any]] = []
        for family_block in raw["families"]:
            for ctrl in family_block.get("controls", []):
                ctrl.setdefault("family", family_block["id"])
                ctrl.setdefault("family_name", family_block.get("name", ""))
                controls.append(ctrl)
        raw["controls"] = controls

    return ControlCatalog.model_validate(raw)
