---
description: Scan for canon drift
argument-hint: "[category]"
---

Invoke the `drift-detector` agent to scan for metadata, index, crosswalk, adapter, and appendix drift.

If `$ARGUMENTS` specifies a category (`schema`, `index`, `crosswalk`, `adapter`, `appendix`), scope the scan to that category only. Otherwise run all five.

Mirrors `.github/workflows/drift-scan.yml` and `.github/workflows/drift-detection.yml`.
