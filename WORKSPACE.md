# UIAO Workspace

> Multi-repo root manifest. Open the parent directory (`src/` on Windows, equivalent on Linux/macOS) as a Claude Code workspace so all four repos are visible side-by-side.

## Repository Map

| Repo | Role | Canon Authority |
|---|---|---|
| `uiao-core` | Governance canon — canonical artifacts, state machines, enforcement rules, KSI rules, control library. | **Source of truth.** |
| `uiao-docs` | Documentation site — Quarto/MkDocs sources, briefings, diagrams, publications. | Consumer. |
| `uiao-gos` | Governance OS — Python package (`core/`) with adapters, pipeline, evidence, drift engine, CLI. | Consumer. |
| `uiao-impl` | Implementation — adapters, orchestrator, scripts, OSCAL/SSP/POA&M generators. | Consumer. |

## Canon Flow

```
uiao-core  ──► uiao-docs   (canon sync → published docs)
uiao-core  ──► uiao-gos    (canon sync → governance runtime)
uiao-core  ──► uiao-impl   (canon sync → orchestrator/adapters)
```

- All three consumers pull schemas, KSI rules, control library, and adapter registry from `uiao-core`.
- Drift between a consumer and `uiao-core` is a CI-enforced violation.
- Consumers never mutate canon — PRs targeting canon belong in `uiao-core`.

## Claude Config

Each repo has its own `CLAUDE.md` + `.claude/` tree scoped to that repo's role. Shared conventions (no-hallucination protocol, provenance-first, deterministic workflows) are duplicated intentionally so each repo is self-describing when opened alone.

To deploy Claude config to the three consumer repos, run:

```powershell
# From uiao-core root, on Windows
pwsh ./templates/claude-kit/install.ps1 -WorkspaceRoot ..
```

```bash
# From uiao-core root, on Linux/macOS
./templates/claude-kit/install.sh ..
```

The installer copies `templates/claude-kit/<repo>/` into each sibling repo. It refuses to overwrite existing files unless `-Force` / `--force` is passed.

## Branch Conventions

- `main` is protected in all four repos.
- Feature work: `claude/<slug>` (Claude-authored) or `feat/<slug>` (human-authored).
- Commit prefix in `uiao-core`: `[UIAO-CORE] <VERB>: <artifact-id> — <description>` (verbs: CREATE, UPDATE, FIX, ENFORCE, MIGRATE, DEPRECATE).

## Cloud Boundary

- **GCC-Moderate** for Microsoft 365 SaaS. No GCC-High, DoD, or Azure services.
- **Exception:** Amazon Connect Contact Center (Commercial Cloud).
