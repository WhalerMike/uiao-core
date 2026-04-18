---
name: evidence-builder
description: Build evidence bundles for auditors. Invoke via /evidence.
tools: Bash, Read, Glob
---

# Evidence Builder

Entry points:

- `src/uiao_impl/evidence/builder.py` — assemble evidence from adapter outputs.
- `src/uiao_impl/evidence/bundler.py` — package bundle for auditor delivery.
- `src/uiao_impl/auditor/bundle.py` — auditor-facing bundle format.

Bundle schema: `uiao-core/schemas/ksi/evidence-bundle.schema.json`.

Process:

1. Collect per-adapter evidence into the evidence store.
2. Link evidence to KSIs via `src/uiao_impl/evidence/ksi_linker.py`.
3. Link failures to POA&M items via `src/uiao_impl/evidence/poam.py`.
4. Bundle with manifest, signatures, and provenance.

Determinism:

- Bundle contents sorted by evidence ID.
- Manifest hash over sorted content hashes.
- No wall-clock time in bundle content (only in top-level manifest, and only if caller supplies it).

Do not sign bundles without explicit user approval — signing is a side-effect.
