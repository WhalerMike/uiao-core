# Rule: Canon Consumer

**Always-on.**

This repository consumes canon from `uiao-core`. It does not own canon.

When tempted to edit:

- `canon/**` — **stop.** Open a PR in `uiao-core`. The change flows back via `canon-sync-receive.yml`.
- Any schema, KSI rule, control library entry, or adapter registry entry — same as above.
- Frontmatter canonical IDs — stop. Verify the ID exists in `uiao-core` first.

When editing is legitimate here:

- Narrative prose (qmd/md bodies).
- Diagram sources (`visuals/`, `diagrams/`, `docs/**/*.puml`).
- Generation inputs (`generation-inputs/*.yaml`).
- Quarto/MkDocs config.
- Presentation-only frontmatter (titles, subtitles, author, layout).

If unsure which side of the line you're on, ask.
