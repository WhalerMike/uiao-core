---
description: Export governance dashboard
argument-hint: "[--dry-run]"
---

Invoke the `dashboard-exporter` agent to generate a timestamped governance dashboard JSON under `dashboard/exports/`.

With `--dry-run` in `$ARGUMENTS`, validates but does not write the export file.

Schema: `schemas/dashboard-schema.json`.
Consumers: `uiao-docs/analytics/atlas_dashboard.json`, `uiao-gos/core/governance/`.

Mirrors `.github/workflows/dashboard-export.yml`.
