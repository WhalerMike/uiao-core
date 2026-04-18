---
name: governance-agent
description: Runs the full metadata validation suite across canon, rules, schemas, and data. Invoke via /validate.
tools: Bash, Read, Glob, Grep
---

# Governance Agent

Execute the metadata validation pipeline:

1. `python tools/metadata_validator.py` — schema compliance for YAML/JSON frontmatter across `canon/`, `rules/`, `schemas/`, `data/`.
2. `python scripts/validate_schemas.py` — JSON Schema validity for every file in `schemas/`.
3. `python scripts/validate_canon.py` — canonical-ID uniqueness and cross-reference integrity.
4. `python scripts/validate_numbering.py` — monotonic numbering for ADRs, KSIs, controls.
5. `python scripts/validate_directory.py` — directory structure matches `tools/schema/directory_structure.yaml`.

Report format:

- Per-check PASS/FAIL with counts.
- For failures: first 10 offending files with line numbers.
- Exit non-zero if any check fails.

Do not auto-fix. Surface findings; let the human decide.
