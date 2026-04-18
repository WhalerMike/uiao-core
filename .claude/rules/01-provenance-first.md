# Rule: Provenance First

**Always-on.**

Every artifact in `canon/`, `rules/`, `schemas/`, `data/`, `ksi/`, and `compliance/` must trace to a canonical source. No orphan artifacts.

When creating or updating an artifact:

1. Record its source in frontmatter (`source:`, `derived_from:`, or `crosswalk:` keys as appropriate).
2. Reference the governing ADR if the change is architectural.
3. Link to the originating KSI or control ID if the change is compliance-bearing.

When the artifact has no upstream source, mark it `NEW (Proposed)` and require ADR coverage before merging.

Workflows that move artifacts between repos (canon sync, dashboard export, appendix sync) must preserve provenance metadata end-to-end. Stripping provenance is a drift violation.
