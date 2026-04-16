# CLAUDE.md — UIAO-Impl Repository

> Implementation layer — adapters, orchestrator, OSCAL/SSP/POA&M generators, evidence builders, KSI evaluator. Canon-consumer.

## Repository Identity

- **Name:** uiao-impl
- **Purpose:** Reference implementation of the UIAO model — collect evidence from vendor systems, evaluate KSIs, generate OSCAL artifacts, produce SSP narratives, manage POA&Ms, drive continuous monitoring.
- **Role:** Consumer of `uiao-core` canon. Complements `uiao-gos` (which is the embeddable runtime); this repo is the batch/assessment toolkit.
- **Language:** Python 3.11+ (see `pyproject.toml`). Source at `src/uiao_impl/`.

## Package Layout

```
src/uiao_impl/
├── abstractions/          # Provider abstractions
├── adapters/              # Vendor adapters (entra, m365, intune, terraform, scuba, etc.)
├── auditor/               # Evidence bundling for auditors
├── cli/                   # Typer CLI (app.py + per-domain subcommands)
├── collectors/            # Collectors (entra, infoblox, sdwan, servicenow)
├── coverage/              # Control coverage calc
├── dashboard/             # Dashboard exports
├── diff/                  # Canon diff engine
├── evidence/              # Evidence builder, bundler, POA&M linker
├── freshness/             # Evidence freshness engine + scheduler
├── generators/            # OSCAL, SSP, POA&M, briefing, diagrams, PPTX, docx, SAR, SBOM
├── governance/            # Actions, drift, ownership, report, SLA
├── ir/                    # Intermediate representation (models, adapters, mapping)
├── ksi/                   # KSI evaluator
├── models/                # Pydantic models (canon, evidence, poam)
├── monitoring/            # Event processor, Sentinel hook, ongoing authorization
├── onboarding/            # Wizard + validator
├── oscal/                 # OSCAL generator
├── scuba/                 # SCuBA transform
├── ssp/                   # SSP lineage + narrative
├── utils/                 # Context helpers
└── validators/            # IR + KSI validators
adapters/                  # Legacy adapter implementations (base_adapter.py + vendor dirs)
orchestrator/              # Compliance Orchestrator
scripts/                   # Standalone automation (50+ scripts)
tests/                     # Pytest suite (60+ test modules)
```

## Relationship to uiao-core

- **Consumes:** Control library, KSI rules, schemas, adapter registry, overlays, canon documents.
- **Emits:** OSCAL SSP/SAR/POA&M, evidence bundles, dashboard exports, KSI evaluations.
- **Contract:** Every emitted artifact validates against the corresponding `uiao-core/schemas/` schema.

## Operating Principles

1. **Canon is read-only.** If you need a new KSI, control, or schema, raise the PR in `uiao-core`.
2. **Test coverage ≥ 80%** for `src/uiao_impl/` (see `.coveragerc`). Below that is blocking for merge.
3. **Pydantic models** for all canon-adjacent data. No dict-typed payloads in generators.
4. **Deterministic generators.** OSCAL, SSP, POA&M output must be byte-stable given the same inputs.
5. **Conformance tests** for every adapter live in `tests/test_<adapter>_adapter*.py`.

## Commit Convention

```
[UIAO-IMPL] <verb>: <module> — <description>
```

Verbs: `ADD`, `UPDATE`, `FIX`, `REFACTOR`, `TEST`, `DEPRECATE`.

## CI Gates

- `ci.yml` — lint + type-check + pytest.
- `acceptance-tests.yml` — end-to-end acceptance.
- `adapter-conformance.yml` — adapter contract conformance.
- `link-check.yml` — doc link integrity.

## Agent Activation

| Command | Agent | Purpose |
|---|---|---|
| `/test` | `test-author` (existing) + `test-runner` | Author and run tests |
| `/adapter` | `adapter-author` | Scaffold a new vendor adapter |
| `/oscal` | `oscal-generator` | Produce OSCAL SSP/SAR/POA&M |
| `/ksi` | `ksi-evaluator` | Run KSI evaluation |
| `/evidence` | `evidence-builder` | Build evidence bundles |
| `/orchestrate` | `orchestrator-runner` | Run the compliance orchestrator |
