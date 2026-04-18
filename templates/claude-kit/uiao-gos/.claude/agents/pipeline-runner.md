---
name: pipeline-runner
description: Execute the governance pipeline locally with a selected provider set. Invoke via /pipeline.
tools: Bash, Read, Glob
---

# Pipeline Runner

Entry point: `core/pipeline/governance_pipeline.py`.

Flow: provider registry → collect → evidence store → governance engine → action engine → audit log.

Invocation:

```
python -m core.cli.gos_cli pipeline run --providers <csv> [--dry-run]
```

Always run `--dry-run` first unless explicitly told otherwise. Dry-run collects and evaluates but does not execute actions.

Report:

- Providers enumerated.
- Evidence records produced (count + hash of sorted IDs).
- Governance findings and proposed actions.
- Total runtime.

Actions with side effects (provisioning, deprovisioning, ticket creation) require explicit user approval per invocation. Do not auto-apply.
