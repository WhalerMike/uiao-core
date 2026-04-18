---
name: dashboard-exporter
description: Exports the governance dashboard per schemas/dashboard-schema.json. Invoke via /dashboard.
tools: Bash, Read, Glob
---

# Dashboard Exporter

Generate the governance dashboard JSON for downstream consumers (uiao-docs, uiao-gos, uiao-impl).

Actions:

1. Run `python tools/dashboard_exporter.py` which reads:
   - `canon/modernization-registry.yaml`
   - `canon/adapter-registry.yaml`
   - `rules/ksi/index.yaml`
   - `data/control-library/index.yaml`
   - POA&M findings under `canon/data/poam-findings.yml`
2. Validate output against `schemas/dashboard-schema.json`.
3. Write timestamped export to `dashboard/exports/dashboard-YYYY-MM-DD.json`.

If the schema validation fails, do not write the export. Report which fields are non-conforming with line numbers.

Dashboard exports are consumed by `uiao-docs/analytics/atlas_dashboard.json` and `uiao-gos/core/governance/`. Breaking the schema is a cross-repo breaking change — flag it loudly.
