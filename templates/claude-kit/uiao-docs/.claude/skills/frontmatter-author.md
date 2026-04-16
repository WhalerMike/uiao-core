---
name: frontmatter-author
description: Produce UIAO-compliant frontmatter for qmd/md documents.
---

# Frontmatter Author

UIAO documents carry a shared frontmatter schema. Required keys:

- `title` — human-readable title.
- `id` — canonical ID if the document is registered in `canon/document-registry.yaml`; otherwise omit.
- `version` — semver; increment on every content change.
- `status` — `draft` | `review` | `published` | `archived`.
- `owner` — single owner email or team handle.
- `source` — provenance: canon artifact path or external source URL.
- `last_reviewed` — ISO date (YYYY-MM-DD).

Optional:

- `tags` — array of strings; use controlled vocabulary from `data/style-guide.yml`.
- `supersedes` / `superseded_by` — for document lifecycle.

Validate with `.github/workflows/validate-uiao-frontmatter.yml`. The schema is in `uiao-core/schemas/metadata-schema.json`.
