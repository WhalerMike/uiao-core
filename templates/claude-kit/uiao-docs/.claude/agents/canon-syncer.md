---
name: canon-syncer
description: Pull latest canon from uiao-core into this repo. Invoke via /canon-sync.
tools: Bash, Read, Glob
---

# Canon Syncer

Consume the canon-sync dispatch from `uiao-core`.

Sources of truth (in `uiao-core`):

- `canon/`, `rules/`, `schemas/`, `data/`, `ksi/`, `compliance/`.

Targets in this repo:

- `canon/` (direct mirror).
- `docs/canon/` (indexed view for site nav).

Process:

1. Trigger or consume the `.github/workflows/canon-sync-receive.yml` workflow.
2. Verify file-level hashes match upstream manifest.
3. Regenerate `docs/canon/index.md` if artifact list changed.
4. Fail loudly on any hash mismatch — do not auto-resolve.

Never mutate synced files locally. If a sync produces unwanted content, fix the source in `uiao-core`.
