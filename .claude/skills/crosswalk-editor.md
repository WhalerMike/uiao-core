---
name: crosswalk-editor
description: Edit control↔KSI, control↔adapter, and NIST↔FedRAMP crosswalks safely.
---

# Crosswalk Editor

Crosswalks live in:

- `rules/ksi/uiao-control-to-ksi-mapping.yaml` — NIST control → KSI rule(s).
- `canon/data/crosswalk-index.yml` — master crosswalk.
- `compliance/reference/fedramp-rev5/ato-overlay-pack.yaml` — FedRAMP Rev5 overlays.
- `canon/data/fedramp-20x.yml` — FedRAMP 20x mappings.

## Editing Rules

1. **Both sides must exist.** Never add a crosswalk row where either the control ID or the KSI ID is unregistered.
2. **Bidirectional.** If control X maps to KSI Y, the inverse must be derivable from the same file — do not split forward/reverse mappings across files.
3. **One authoritative file per mapping type.** Don't duplicate mappings across files. If a mapping appears in two places, one is the source and the other is a generated projection — mark the projection with `generated: true`.
4. **Versioned.** Every crosswalk file has a `version:` key. Increment on any change.

After editing, run `python tools/validators/crosswalk_validator.py` and `/drift crosswalk`.
