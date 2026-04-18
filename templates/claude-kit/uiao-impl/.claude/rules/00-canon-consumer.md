# Rule: Canon Consumer

**Always-on.** Complements the existing `canon-consumer.md` rule — merge, do not replace.

`uiao-impl` consumes canon; it does not author it.

Never edit in this repo:

- Control library entries — those live in `uiao-core/data/control-library/<family>/`.
- KSI rules — those live in `uiao-core/rules/ksi/<category>/`.
- Schemas — `uiao-core/schemas/**`.
- Adapter registry — `uiao-core/canon/adapter-registry.yaml`.
- ADRs touching architecture — `uiao-core/canon/adr/`.

If the upstream canon is missing something your implementation needs, the correct fix is a PR in `uiao-core`. Open an issue there, not a workaround here.

When testing against canon artifacts, use `tests/canon_paths.py` to resolve paths — never hard-code relative paths into `uiao-core/`.
