---
description: Full canon integrity check
argument-hint: "[--blocking-only]"
---

Invoke the `canon-steward` agent to run the eight-stage integrity check (structure, schemas, canon, metadata, drift, crosswalks, appendix, dashboard).

With `--blocking-only` in `$ARGUMENTS`, suppresses non-blocking findings in the report.

This is the pre-PR gate. Run it before opening any PR that touches `canon/`, `rules/`, `schemas/`, or `data/`.
