---
name: canon-writer
description: Authoring skill for new canonical artifacts (ADRs, KSIs, control entries, adapter registrations).
---

# Canon Writer

When authoring a new canonical artifact, follow this skill:

## ADR

- Path: `canon/adr/adr-<nnn>-<slug>.md`
- Number: next unused integer in `canon/adr/index.md`.
- Required frontmatter: `id`, `title`, `status` (proposed|accepted|deprecated|superseded), `date`, `deciders`, `context`.
- Supersession: set `supersedes:` and `superseded_by:` keys; update both ADRs.

## KSI Rule

- Path: `rules/ksi/<category>/ksi-<family>-<nn>.yaml` where category ∈ {iam, boundary-protection, configuration-management, incident-response, monitoring-logging, planning-personnel, other}.
- Schema: `rules/ksi/ksi_schema.yaml`.
- Must appear in `rules/ksi/index.yaml` and in the control mapping at `rules/ksi/uiao-control-to-ksi-mapping.yaml`.
- Top-level KSI-NNN bundles live in `ksi/rules/KSI-<nnn>.yaml` — link to the per-control files.

## Control Library Entry

- Path: `data/control-library/<family>/<ID>.yml`.
- Family lowercase (ac, at, au, ca, cm, cp, ia, ir, ma, mp, pe, pl, ps, ra, sa, sc, si).
- Enhancements use parentheses in the filename: `AC-2(3).yml`.
- Must be listed in `data/control-library/index.yaml` and `data/control-library/uiao-control-matrix.yaml`.

## Adapter Registration

- Registry: `canon/adapter-registry.yaml`.
- Schema: `schemas/adapter-registry/adapter-registry.schema.json`.
- Vendor overlay: `data/overlays/<vendor>/<product>.yml` or `data/vendor-overlays/<vendor>.yaml`.
- Evidence bundle schema: `schemas/ksi/evidence-bundle.schema.json`.

After authoring, run `/canon` before committing.
