---
description: Run metadata validation suite
argument-hint: "[--fix]"
---

Invoke the `governance-agent` to run the full metadata validation pipeline over canon, rules, schemas, and data.

If `$ARGUMENTS` contains `--fix`, the agent may propose auto-remediation patches but must not apply them without explicit approval.

Expected CI gates this mirrors:

- `.github/workflows/metadata-validator.yml`
- `.github/workflows/canon-validation.yml`
- `.github/workflows/validate-workflow-serialization.yml`
