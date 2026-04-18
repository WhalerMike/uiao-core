# Rule: Quarto + MkDocs Coexistence

**Always-on.**

This repo builds with **both** Quarto and MkDocs. Changes must not break either.

- Quarto config: `_quarto.yml`. Sources: `docs/**/*.qmd`.
- MkDocs config: `mkdocs.yml`. Sources: `docs/**/*.md`.
- Shared assets: `docs/images/`, `docs/stylesheets/`, `docs/javascripts/`.

When adding a new doc:

- If it renders math, diagrams-as-code, or citations → Quarto (qmd).
- If it is plain reference content → MkDocs (md).
- Index pages: one of each (`index.qmd` and `index.md`) if both systems need to land on the page.

When updating navigation, update the relevant config **and** verify the other side still builds. The `build-docs` CI runs both.
