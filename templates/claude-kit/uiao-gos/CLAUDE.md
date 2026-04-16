# CLAUDE.md — UIAO-GOS Repository

> Governance Operating System — runtime Python package. Canon-consumer.

## Repository Identity

- **Name:** uiao-gos
- **Purpose:** Python runtime implementing the UIAO governance model — provider adapters, adapter registry, governance pipeline, evidence store, drift engine, action engine, virtual OU tree.
- **Role:** Consumer of `uiao-core` canon. Executable at runtime; ships as a Python package.
- **Language:** Python 3.11+ (see `pyproject.toml`).

## Package Layout

```
core/
├── adapters/ipam/            # IPAM adapters (infoblox, bluecat, generic)
├── cli/gos_cli.py            # Command-line entry point
├── drift/                    # Drift engine
├── evidence/                 # Evidence model + store
├── governance/               # Governance engine, action engine, registries, audit log
├── orgpath/                  # Org-path model
├── pipeline/                 # Governance pipeline orchestration
├── providers/                # Provider adapters (aws, azure, entra, github, m365, servicenow)
├── virtual_ou/               # Virtual OU tree
└── version.py
```

## Relationship to uiao-core

- **Consumes:** Adapter registry schema, KSI rules, control library, evidence bundle schema.
- **Never edits:** Canon artifacts. All schema and registry changes belong upstream.
- **Contract:** Runtime enforcement conforms to the rules expressed in `uiao-core/rules/ksi/` and `uiao-core/canon/adapter-registry.yaml`.

## Operating Principles

1. **Deterministic execution** — no wall-clock timestamps in hashed output; no `set()` iteration order in serialized evidence.
2. **Adapter contract** — every provider adapter implements `BaseAdapter` from `core/providers/base_adapter.py`. No exceptions.
3. **Evidence provenance** — every evidence record carries its source adapter, timestamp (UTC), and a content hash.
4. **Fail loud** — a provider raising an unexpected exception halts the pipeline with the traceback. Do not swallow.

## Commit Convention

```
[UIAO-GOS] <verb>: <module> — <description>
```

Verbs: `ADD`, `UPDATE`, `FIX`, `REFACTOR`, `TEST`, `DEPRECATE`.

## CI Gates

- `ci.yml` — lint (ruff), type-check (mypy), test (pytest).
- `release.yml` — tagged releases build and publish artifacts.

## Agent Activation

| Command | Agent | Purpose |
|---|---|---|
| `/test` | `test-runner` | Run pytest with coverage |
| `/adapter` | `adapter-author` | Scaffold a new provider adapter |
| `/pipeline` | `pipeline-runner` | Execute governance pipeline locally |
| `/evidence` | `evidence-inspector` | Query local evidence store |
| `/lint` | `lint-runner` | Ruff + mypy + format check |
