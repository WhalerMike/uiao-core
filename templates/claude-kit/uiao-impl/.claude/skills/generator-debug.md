---
name: generator-debug
description: Diagnose a failing OSCAL/SSP/POA&M/SAR generator.
---

# Generator Debug

When a generator produces invalid output or non-deterministic bytes:

1. **Reproduce.** Run the generator in isolation with a fixed input fixture.
2. **Diff bytes.** Run twice; diff the output. Any delta is a determinism bug — search the generator code for `datetime.now`, `uuid.uuid4`, unsorted dict/set serialization, `os.urandom`.
3. **Validate.** Run through `scripts/validate_oscal.py` / `scripts/validate_schemas.py`. Report the first failing JSONPath and the expected schema constraint.
4. **Check canon refs.** Every control ID referenced must exist in `uiao-core/data/control-library/<family>/<ID>.yml`. Missing refs point to either a stale canon sync or a genuine canon gap.
5. **Narrative.** For SSP narrative issues, trace through `src/uiao_impl/generators/narrative_loader.py` and `src/uiao_impl/ssp/narrative.py`.

Never paper over a validation failure by relaxing the schema in `uiao-core`. The schema is canon; the generator must conform.
