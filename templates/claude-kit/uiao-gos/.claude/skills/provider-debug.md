---
name: provider-debug
description: Diagnose a failing provider adapter.
---

# Provider Debug

When a provider adapter fails in the pipeline:

1. **Isolate.** Run the adapter alone: `python -m core.providers.<vendor>.<vendor>_adapter` (each adapter exposes a `__main__` for this).
2. **Inspect credentials.** Check `.env` against the adapter's `README.md`. Missing scopes are the #1 cause.
3. **Replay.** Use a fixture from `tests/fixtures/` (or create one from a scrubbed live response) and run the adapter in replay mode.
4. **Determinism check.** Run `collect()` twice with the same input; diff the output. Non-zero diff is a determinism bug, not a transient failure.
5. **Evidence validation.** Run the output through `jsonschema` against `uiao-core/schemas/ksi/evidence-bundle.schema.json`.

Never add retries as a workaround for a determinism bug. Retries are appropriate only for transient network/auth errors, with exponential backoff capped at 3 attempts.
