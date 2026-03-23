"""Pydantic v2 models for the UIAO visual manifest canon YAML.

Validates entries in ``canon/visual_manifest_v1.0.yaml`` and provides a
typed loader used by ``visual_resolver``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict


class VisualEntry(BaseModel):
    """A single image/diagram entry in the visual manifest."""

    filename: str
    description: str
    doc_location: str
    type: Literal["AI-Generated PNG", "Mermaid.js"]
    model_config = ConfigDict(extra="allow")


class VisualManifest(BaseModel):
    """Top-level visual manifest document."""

    project: str = ""
    last_updated: str = ""
    images: list[VisualEntry] = []
    model_config = ConfigDict(extra="allow")


class VisualManifestDoc(BaseModel):
    """Wrapper matching the YAML root key ``visual_manifest``."""

    visual_manifest: VisualManifest = VisualManifest()
    model_config = ConfigDict(extra="allow")


def load_visual_manifest(manifest_path: Path | None = None) -> VisualManifest:
    """Load and validate the visual manifest YAML file.

    Args:
        manifest_path: Explicit path to the manifest YAML. Defaults to
            ``canon/visual_manifest_v1.0.yaml`` relative to CWD.

    Returns:
        Validated :class:`VisualManifest` instance.
    """
    if manifest_path is None:
        manifest_path = Path("canon") / "visual_manifest_v1.0.yaml"
    with manifest_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    doc = VisualManifestDoc.model_validate(data)
    return doc.visual_manifest
