---
name: oscal-generator
description: Produce OSCAL SSP/SAR/POA&M artifacts. Invoke via /oscal.
tools: Bash, Read, Glob
---

# OSCAL Generator

Entry point: `python -m uiao_impl.cli.app oscal generate`.

Sub-artifacts:

- **SSP** — System Security Plan. Source: `src/uiao_impl/generators/ssp.py`, `src/uiao_impl/ssp/narrative.py`.
- **SAR** — Security Assessment Report. Source: `src/uiao_impl/generators/sar.py`.
- **POA&M** — Plan of Actions and Milestones. Source: `src/uiao_impl/generators/poam.py` + `poam_rules.py`.

Validation pipeline:

1. Generate OSCAL JSON.
2. Validate against the OSCAL schema (we use `trestle` via `scripts/validate_with_trestle.py`).
3. Validate against the UIAO canon mapping — every control referenced must exist in `uiao-core/data/control-library/`.

Emit byte-stable output. Re-running with the same inputs must produce identical bytes.

Report:

- Controls covered vs. controls referenced.
- Validation errors by severity.
- Output path.
