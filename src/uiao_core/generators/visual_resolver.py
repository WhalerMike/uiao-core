"""Visual manifest resolver — wire ``canon/visual_manifest_v1.0.yaml``
into the document generation pipeline.

For each entry in the manifest this module:
  * **Mermaid.js** – renders the ``.mermaid`` source file in ``visuals/``
    to PNG via :func:`~uiao_core.generators.mermaid.render_mermaid_file`.
  * **AI-Generated PNG** – returns the PNG from ``visuals/`` or
    ``assets/images/gemini/`` if it already exists; otherwise calls the
    Gemini generator using the manifest ``description`` as the prompt.

The public :func:`resolve_visuals` function returns a mapping of
``doc_location`` → ``[resolved image Path, ...]`` that DOCX and PPTX
generators can use to embed the right images in the right places.
"""

from __future__ import annotations

import logging
from pathlib import Path

from uiao_core.models.visual_manifest import VisualManifest, load_visual_manifest
from uiao_core.utils.context import get_settings

logger = logging.getLogger(__name__)

_DEFAULT_VISUALS_DIR = Path("visuals")
_DEFAULT_MERMAID_OUTPUT_DIR = Path("assets/images/mermaid")
_DEFAULT_GEMINI_OUTPUT_DIR = Path("assets/images/gemini")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _resolve_mermaid_entry(
    filename: str,
    visuals_dir: Path,
    mermaid_output_dir: Path,
    force: bool,
) -> Path | None:
    """Render a Mermaid source file to PNG and return the PNG path."""
    stem = Path(filename).stem
    mmd_path = visuals_dir / filename
    if not mmd_path.exists():
        logger.warning(
            "Mermaid source file not found, skipping: %s", mmd_path
        )
        return None

    try:
        from uiao_core.generators.mermaid import render_mermaid_file

        return render_mermaid_file(mmd_path, mermaid_output_dir, force=force)
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to render Mermaid file %s: %s", filename, exc)
        return None


def _resolve_ai_png_entry(
    filename: str,
    description: str,
    visuals_dir: Path,
    gemini_output_dir: Path,
    force: bool,
) -> Path | None:
    """Return an existing AI-generated PNG or generate it via Gemini."""
    # 1. Check visuals/ directory first (pre-committed PNGs)
    local_path = visuals_dir / filename
    if local_path.exists() and not force:
        logger.info("Using existing PNG from visuals/: %s", local_path)
        return local_path

    # 2. Check assets/images/gemini/
    gemini_path = gemini_output_dir / filename
    if gemini_path.exists() and not force:
        logger.info("Using cached Gemini PNG: %s", gemini_path)
        return gemini_path

    # 3. Try to generate via Gemini API
    try:
        from uiao_core.generators.gemini_visuals import generate_gemini_image

        name = Path(filename).stem
        result = generate_gemini_image(
            name,
            prompt=description,
            output_dir=gemini_output_dir,
            force=force,
        )
        if result:
            return result
    except Exception as exc:  # pragma: no cover
        logger.warning("Gemini generation failed for %s: %s", filename, exc)

    logger.warning("Could not resolve AI-generated image: %s", filename)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_visuals(
    manifest_path: Path | None = None,
    visuals_dir: Path | None = None,
    mermaid_output_dir: Path | None = None,
    gemini_output_dir: Path | None = None,
    force: bool = False,
) -> dict[str, list[Path]]:
    """Resolve all images in the visual manifest to filesystem paths.

    Args:
        manifest_path: Path to ``visual_manifest_v1.0.yaml``. Defaults to
            ``canon/visual_manifest_v1.0.yaml``.
        visuals_dir: Directory containing Mermaid source files and
            pre-committed PNGs. Defaults to ``visuals/``.
        mermaid_output_dir: Output directory for Mermaid-rendered PNGs.
            Defaults to ``assets/images/mermaid/``.
        gemini_output_dir: Output/cache directory for Gemini-generated PNGs.
            Defaults to ``assets/images/gemini/``.
        force: When ``True``, skip caches and regenerate all images.

    Returns:
        Mapping of ``doc_location`` → list of resolved :class:`~pathlib.Path`
        objects. An entry is omitted from the list if its image could not be
        resolved (with a warning logged).
    """
    settings = get_settings()

    if visuals_dir is None:
        visuals_dir = settings.root_dir / _DEFAULT_VISUALS_DIR
    if mermaid_output_dir is None:
        mermaid_output_dir = settings.root_dir / _DEFAULT_MERMAID_OUTPUT_DIR
    if gemini_output_dir is None:
        gemini_output_dir = settings.root_dir / _DEFAULT_GEMINI_OUTPUT_DIR

    visuals_dir = Path(visuals_dir)
    mermaid_output_dir = Path(mermaid_output_dir)
    gemini_output_dir = Path(gemini_output_dir)

    mermaid_output_dir.mkdir(parents=True, exist_ok=True)
    gemini_output_dir.mkdir(parents=True, exist_ok=True)

    manifest: VisualManifest = load_visual_manifest(manifest_path)

    resolved: dict[str, list[Path]] = {}
    stats = {"total": 0, "resolved": 0, "missing": 0}

    for entry in manifest.images:
        stats["total"] += 1
        image_path: Path | None = None

        if entry.type == "Mermaid.js":
            image_path = _resolve_mermaid_entry(
                entry.filename, visuals_dir, mermaid_output_dir, force
            )
        elif entry.type == "AI-Generated PNG":
            image_path = _resolve_ai_png_entry(
                entry.filename, entry.description,
                visuals_dir, gemini_output_dir, force,
            )

        if image_path is not None:
            resolved.setdefault(entry.doc_location, []).append(image_path)
            stats["resolved"] += 1
        else:
            stats["missing"] += 1

    logger.info(
        "Visual manifest resolved %d/%d image(s) (%d missing).",
        stats["resolved"], stats["total"], stats["missing"],
    )
    return resolved


def get_images_for_location(
    resolved: dict[str, list[Path]],
    location_fragment: str,
) -> list[Path]:
    """Return all resolved image paths whose doc_location contains *location_fragment*.

    Performs a case-insensitive substring match, so
    ``get_images_for_location(resolved, "Executive Summary")`` will match
    ``"Pitch Deck Slide 1 / Executive Summary"``.

    Args:
        resolved: Output of :func:`resolve_visuals`.
        location_fragment: Substring to search for in doc_location keys.

    Returns:
        Combined list of image paths from all matching locations.
    """
    fragment_lower = location_fragment.lower()
    images: list[Path] = []
    for loc, paths in resolved.items():
        if fragment_lower in loc.lower():
            images.extend(paths)
    return images
