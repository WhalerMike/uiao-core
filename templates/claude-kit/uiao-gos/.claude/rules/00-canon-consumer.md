# Rule: Canon Consumer

**Always-on.**

Runtime code in this repo enforces rules defined in `uiao-core`. It does not author them.

Forbidden here:

- Hard-coding control IDs, KSI IDs, or vendor baselines that are not in `uiao-core/canon/` or `uiao-core/rules/ksi/`.
- Defining a new adapter contract. The contract lives in `uiao-core/canon/specs/adapter-contract.qmd`.
- Inventing evidence schemas. Evidence conforms to `uiao-core/schemas/ksi/evidence-bundle.schema.json`.

Permitted here:

- Implementing adapters that satisfy the upstream contract.
- Adding runtime features (caching, retries, parallelism) that don't mutate governance semantics.
- Extending the CLI and pipeline orchestration.

If you need a new rule or schema, propose it in `uiao-core` first.
