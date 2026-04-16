# Rule: No-Hallucination Protocol

**Always-on. Applies to every response.**

Use only provided text, files, and canon artifacts as source of truth. Do not invent identifiers, schemas, control IDs, KSI IDs, adapter names, or vendor baselines.

When information is incomplete:

- Mark missing content as `MISSING`
- Mark uncertain content as `UNSURE`
- Mark invented content as `NEW (Proposed)` — and flag it for human review

Never cite an artifact you have not read. Never reference a previous version of canon; this repo is single-version canon.

If asked to produce a canonical ID (control, KSI, adapter, ADR), verify it exists in the appropriate registry:

- Controls: `data/control-library/<family>/<ID>.yml`
- KSIs: `rules/ksi/<category>/ksi-<family>-<nn>.yaml` and `ksi/rules/KSI-<nnn>.yaml`
- Adapters: `canon/adapter-registry.yaml`
- ADRs: `canon/adr/adr-<nnn>-<slug>.md`
- Documents: `canon/document-registry.yaml`

If the ID does not exist, say so. Do not guess.
