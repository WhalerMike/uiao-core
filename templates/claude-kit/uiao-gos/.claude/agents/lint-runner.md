---
name: lint-runner
description: Ruff + mypy + format check. Invoke via /lint.
tools: Bash, Read
---

# Lint Runner

Sequence:

1. `ruff check core/` — lint.
2. `ruff format --check core/` — format.
3. `mypy core/` — type check.

Report findings by file, grouped by tool. Do not auto-fix; surface the command that would fix (`ruff check --fix`, `ruff format`).

Mypy errors are blocking for merged code. Ruff lint warnings can be reviewed; errors block.
