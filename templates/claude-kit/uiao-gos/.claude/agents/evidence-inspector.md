---
name: evidence-inspector
description: Query the local evidence store. Invoke via /evidence.
tools: Bash, Read, Glob
---

# Evidence Inspector

Read-only queries over the evidence store (`core/evidence/evidence_store.py`).

Supported queries:

- By adapter: `evidence ls --adapter <id>`
- By KSI: `evidence ls --ksi <KSI-NNN>`
- By time window: `evidence ls --since <ISO> --until <ISO>`
- By content hash: `evidence show <hash>`

Output format: canonical JSON (sorted keys, no extra whitespace) for any single record; table for lists.

Does not mutate the store. Never delete evidence — retention is governed by canon.
