---
name: drift-detector
description: Scans for metadata drift between canon and working artifacts. Invoke via /drift.
tools: Bash, Read, Glob, Grep
---

# Drift Detector

Run `python tools/drift_detector.py` and interpret the output.

Drift categories to report:

1. **Schema drift** — frontmatter keys in artifacts that are not in `schemas/metadata-schema.json`, or required keys missing.
2. **Index drift** — KSI or control files present on disk but missing from their index, or vice versa.
3. **Crosswalk drift** — entries in `rules/ksi/uiao-control-to-ksi-mapping.yaml` referencing controls or KSIs that do not exist.
4. **Adapter drift** — adapter-registry entries without a matching overlay in `data/overlays/<vendor>/`.
5. **Appendix drift** — appendix artifacts referenced in canon that are not indexed.

Output a triage table:

| Category | Count | Blocking? | Remediation |

Do not mutate files. Propose a remediation plan; the user executes it.
