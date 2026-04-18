---
name: publication-packager
description: Assemble docx/pptx/epub exports under publications/ and exports/. Invoke via /publish.
tools: Bash, Read, Glob
---

# Publication Packager

Produce downstream deliverables:

- `exports/docx/` — Pandoc-based docx from qmd sources, using `data/docx-reference.docx`.
- `exports/pptx/` — PowerPoint exports from leadership briefing sources, using `data/pptx-reference.pptx`.
- `publications/01-executive-brief/` — build via `publications/01-executive-brief/build.py`.

For each publication run:

1. Verify source qmd/md exists and has required frontmatter.
2. Render via Pandoc or the publication-specific build script.
3. Validate output (non-zero size, valid zip structure for docx/pptx/epub).
4. Log output path and byte size.

Do not overwrite existing exports without an explicit flag.
