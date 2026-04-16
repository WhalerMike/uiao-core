# Rule: Commit Convention

**Always-on for commits touching governance artifacts.**

Format:

```
[UIAO-CORE] <VERB>: <artifact-id> — <short description>
```

Verbs (uppercase):

- `CREATE` — new artifact
- `UPDATE` — enhance existing artifact
- `FIX` — correct a defect
- `ENFORCE` — add or tighten a CI gate
- `MIGRATE` — move an artifact or change its schema
- `DEPRECATE` — mark an artifact for retirement

Examples:

- `[UIAO-CORE] CREATE: KSI-011 — evidence retention KSI`
- `[UIAO-CORE] UPDATE: adapter-registry.yaml — add Infoblox DDI overlay`
- `[UIAO-CORE] ENFORCE: metadata-validator — require provenance on canon/*`

Non-canon commits (CI config, tooling, docs) may use conventional prefixes (`chore:`, `ci:`, `docs:`) but the UIAO-CORE format is preferred.
