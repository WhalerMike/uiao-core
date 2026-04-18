# Rule: Deterministic Workflows

**Always-on.**

State machines are acyclic and deterministic. No ambiguous transitions.

- Every state has a single predecessor set and a single successor set.
- Every transition has a named trigger and a recorded owner.
- Every terminal state is explicit; no implicit "end".

Code that implements a workflow (in `tools/`, `scripts/`, or `.github/workflows/`) must:

1. Produce identical output for identical input — no timestamps, random IDs, or `set()` ordering in serialized output.
2. Exit non-zero on any undefined transition.
3. Log state transitions with `from`, `to`, `trigger`, and `actor`.

Workflow serialization is validated by `tests/test_workflow_serialization.py` and enforced by `.github/workflows/validate-workflow-serialization.yml`. Do not break determinism to make a test pass — fix the root cause.
