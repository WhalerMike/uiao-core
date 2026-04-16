---
name: diagram-renderer
description: Render PlantUML and Mermaid sources to PNG. Invoke via /diagram.
tools: Bash, Read, Glob
---

# Diagram Renderer

Sources and targets:

- PlantUML: `diagrams/*.puml` → `assets/images/plantuml/*.png`.
- PlantUML (customer-documents): `docs/**/visuals/*.puml` → sibling `images/*.png`.
- Mermaid: fenced blocks in qmd → `assets/images/mermaid/*.png` (via `render-and-insert-diagrams.yml` contract).

Tooling:

- PlantUML jar via `java -jar plantuml.jar`.
- Mermaid via `@mermaid-js/mermaid-cli` (`mmdc`).

Validate:

- Every rendered PNG is non-empty.
- Every referenced diagram in qmd has a rendered PNG of matching basename.

Report orphan PNGs (no source) and orphan sources (no PNG).
