---
name: orchestrator-runner
description: Run the Compliance Orchestrator end-to-end. Invoke via /orchestrate.
tools: Bash, Read, Glob
---

# Orchestrator Runner

Entry point: `orchestrator/orchestrator.py`.

Orchestration stages (roughly):

1. Collect evidence across enabled providers.
2. Transform to IR.
3. Evaluate KSIs.
4. Generate OSCAL (SSP/SAR/POA&M).
5. Link POA&Ms to monitoring sources.
6. Produce dashboard export.

Invocation:

```
python orchestrator/orchestrator.py --config orchestrator/config.yaml [--dry-run]
```

Always `--dry-run` first. Full runs take minutes-to-hours depending on provider set.

Report:

- Stage timings.
- Records/artifacts produced per stage.
- Blocking errors (schema, canon reference).
- Non-blocking warnings (freshness, coverage).

A stage failure aborts downstream stages unless `--continue-on-error`. Never auto-continue when an OSCAL stage fails — downstream artifacts would be partially invalid.
