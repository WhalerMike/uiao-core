---
name: link-auditor
description: Validate internal and external links across docs. Invoke via /linkcheck.
tools: Bash, Read, Glob
---

# Link Auditor

Run `lychee` with `.lychee.toml` to validate:

- Internal links (relative paths in qmd/md).
- Cross-repo references (to uiao-core artifacts — resolve via synced canon).
- External links (HTTP/HTTPS).

Report:

- Broken links with source file + line.
- Redirect chains over 2 hops.
- 4xx/5xx status codes for external links.

Mirrors `.github/workflows/link-check.yml`. Exit non-zero on any broken internal link. External link failures are warnings unless `--strict` is passed.
