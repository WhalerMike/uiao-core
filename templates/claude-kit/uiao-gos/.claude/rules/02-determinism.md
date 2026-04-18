# Rule: Deterministic Output

**Always-on for code that produces evidence, audit logs, or hashed artifacts.**

- No `datetime.now()` in hash inputs. If a timestamp is semantically required, take it as a parameter.
- No unsorted `set` or `dict` iteration in serialized output. Use `sorted()` or `json.dumps(..., sort_keys=True)`.
- No random IDs in content-addressed artifacts. If uniqueness is needed, derive from content hash.
- No locale-dependent string formatting.

Evidence store writes go through `core/evidence/evidence_store.py` which enforces canonical JSON (sorted keys, no whitespace variation).

If a test produces flaky output, the fix is to find the non-determinism, not to loosen the assertion.
