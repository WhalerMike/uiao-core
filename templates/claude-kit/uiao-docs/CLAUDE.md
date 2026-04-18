# CLAUDE.md — UIAO-Docs Repository

> Documentation site and publications. Canon-consumer.

## Repository Identity

- **Name:** uiao-docs
- **Purpose:** Human-facing documentation — Quarto/MkDocs sources, briefings, diagrams, appendices, customer-documents, publications.
- **Role:** Consumer of `uiao-core` canon. Never mutates canon.
- **Build:** Quarto (`_quarto.yml`) + MkDocs (`mkdocs.yml`). Site output under `site/`.

## Relationship to uiao-core

- Schemas, KSI rules, control library, and dashboard JSON flow **from** `uiao-core` **into** this repo via `canon-sync-receive.yml`.
- This repo owns presentation (qmd files, narrative, diagrams, exports to docx/pptx/epub).
- A change that requires updating canon belongs in `uiao-core`, not here. Raise a PR there and wait for the sync.

## Operating Principles

1. **No-Hallucination Protocol** — cite canonical sources only. Never invent control IDs, KSI IDs, or adapter names.
2. **Provenance First** — every qmd with canonical content carries frontmatter pointing back to its canon source.
3. **Version Isolation** — one version of canon at a time. No back-references to prior versions.

## Directory Convention

```
uiao-docs/
├── CLAUDE.md
├── .claude/
├── _quarto.yml
├── mkdocs.yml
├── docs/                      # Primary content (qmd + md)
├── canon/                     # Mirror of uiao-core/canon (synced)
├── appendices/                # Appendix A–E
├── narrative/                 # Long-form narrative
├── publications/              # Executive briefs, mission statements
├── exports/                   # Generated docx/pptx/epub
├── visuals/                   # PlantUML + PNG
├── diagrams/                  # PlantUML sources
├── generation-inputs/         # YAML inputs for generators
└── tools/                     # Documentation generators
```

## Commit Convention

```
[UIAO-DOCS] <verb>: <artifact> — <description>
```

Verbs: `ADD`, `UPDATE`, `FIX`, `PUBLISH`, `ARCHIVE`.

## CI Gates

- `build-docs` — Quarto/MkDocs build succeeds.
- `canon-validation` — synced canon files match upstream hashes.
- `metadata-validator` — frontmatter conforms.
- `link-check` — no broken internal links.
- `validate-uiao-frontmatter` — UIAO-specific frontmatter schema.
- `appendix-sync` — appendix index in sync with uiao-core.

## Agent Activation

| Command | Agent | Purpose |
|---|---|---|
| `/build` | `docs-builder` | Local Quarto+MkDocs build |
| `/publish` | `publication-packager` | Assemble docx/pptx/epub exports |
| `/diagram` | `diagram-renderer` | Render PlantUML/Mermaid to PNG |
| `/canon-sync` | `canon-syncer` | Pull latest canon from uiao-core |
| `/linkcheck` | `link-auditor` | Validate internal and external links |
