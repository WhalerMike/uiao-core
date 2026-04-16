# Rule: Drift Prevention

**Always-on.**

Metadata drift between canon and working artifacts is detected, flagged, and remediated via CI. Do not bypass drift gates.

Drift sources to watch:

- Frontmatter schema changes in `schemas/metadata-schema.json` not propagated to artifacts.
- KSI rule changes in `rules/ksi/` not reflected in `rules/ksi/index.yaml` or `rules/ksi/uiao-control-to-ksi-mapping.yaml`.
- Control library updates in `data/control-library/` not mirrored in `data/control-library/index.yaml` or `data/control-library/uiao-control-matrix.yaml`.
- Adapter registry entries in `canon/adapter-registry.yaml` not matching `schemas/adapter-registry/adapter-registry.schema.json`.
- Appendix index in `appendices/` out of sync with artifacts.

When you touch any of these, re-run the relevant validator from `tools/` and commit both the source change and the regenerated index in the same PR.

The `/drift` slash command invokes the drift detector. Use it before opening a PR.
