---
name: ksi-evaluator
description: Run KSI evaluation against collected evidence. Invoke via /ksi.
tools: Bash, Read, Glob
---

# KSI Evaluator

Entry point: `src/uiao_impl/ksi/evaluate.py`.

Inputs:

- KSI rules from `uiao-core/rules/ksi/` (synced).
- Evidence bundles from `src/uiao_impl/evidence/`.
- IR mapping from `src/uiao_impl/ir/mapping/ksi_to_ir.py`.

Output: KSI evaluation report per `uiao-core/schemas/ksi/ksi.schema.json`.

Process:

1. Load KSI rule set (filtered by `--category` or `--ksi-id` if given).
2. For each KSI, resolve the IR query.
3. Apply the rule to the evidence model.
4. Classify: PASS / FAIL / INCONCLUSIVE / N/A.
5. For FAIL, emit a POA&M candidate (dry-run by default).

Validation: output must satisfy `uiao-core/schemas/ksi/ksi.schema.json`. Blocking on schema failure.

Report metrics:

- Count by status.
- Top failing KSIs by control family.
- Orphan evidence (no rule matched).
