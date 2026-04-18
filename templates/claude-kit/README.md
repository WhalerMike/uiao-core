# UIAO Claude Kit

Per-repo `CLAUDE.md` + `.claude/` trees for the three canon-consumer repos.

## What this is

This directory holds templates for the three sibling repos in the UIAO workspace. `uiao-core`'s own Claude config lives at `uiao-core/.claude/` and is not part of this kit.

```
templates/claude-kit/
├── install.ps1             # Windows installer (pwsh)
├── install.sh              # Linux/macOS installer
├── README.md               # This file
├── uiao-docs/
│   ├── CLAUDE.md
│   └── .claude/            # rules, agents, skills, commands
├── uiao-gos/
│   ├── CLAUDE.md
│   └── .claude/
└── uiao-impl/
    ├── CLAUDE.md
    └── .claude/
```

## Install

From the workspace root (parent of `uiao-core`):

**Windows (PowerShell):**

```powershell
pwsh ./uiao-core/templates/claude-kit/install.ps1
```

**Linux/macOS:**

```bash
./uiao-core/templates/claude-kit/install.sh
```

Or, from inside `uiao-core`:

```bash
./templates/claude-kit/install.sh ..
```

### Flags

| Flag | Effect |
|---|---|
| *(none)* | Copies files; skips anything that already exists. Safe default. |
| `-Force` / `--force` | Overwrites existing `CLAUDE.md` and files under `.claude/`. |
| `-Clean` / `--clean` | Removes the target repo's existing `.claude/` and `CLAUDE.md` before copying. **Destructive.** PowerShell prompts for confirmation unless `-Confirm:$false`. |
| `-WhatIf` (PowerShell) / `--dry-run` (bash) | Logs what would happen without touching the filesystem. |

## Per-repo scope

Each repo's kit is tailored to its role:

- **uiao-docs** — Quarto/MkDocs, publications, diagrams, canon-sync. Rules emphasize "canon consumer, never edit canon." Agents: docs-builder, publication-packager, diagram-renderer, canon-syncer, link-auditor.
- **uiao-gos** — Python governance OS. Rules emphasize adapter contract and determinism. Agents: test-runner, adapter-author, pipeline-runner, evidence-inspector, lint-runner.
- **uiao-impl** — Implementation toolkit (adapters, OSCAL/SSP/POA&M, orchestrator). Rules complement the existing `canon-consumer.md` and `test-coverage.md` — they do not replace them. Agents: oscal-generator, ksi-evaluator, evidence-builder, orchestrator-runner.

## Updating a kit

Edit the templates in this directory, commit to `uiao-core`, then re-run the installer with `--force` in each workspace.

The kit is versioned with `uiao-core` — there is no separate release cycle.

## Installing to a fresh repo

If you clone a new workspace, run the installer immediately after cloning:

```bash
git clone <url> uiao-docs
./uiao-core/templates/claude-kit/install.sh
```

No files pre-exist, so no flags needed.

## Migrating old workspace paths

If the sibling repos contain references to an older workspace layout
(e.g. `C:\Users\whale\uiao-*` before the move into `C:\Users\whale\src\`),
run the migration helper from `C:\Users\whale\src`:

```powershell
# Preview first
pwsh .\uiao-core\templates\claude-kit\migrate-old-paths.ps1 -WhatIf

# Apply
pwsh .\uiao-core\templates\claude-kit\migrate-old-paths.ps1
```

The script rewrites three variants in common text files across `uiao-docs`,
`uiao-gos`, and `uiao-impl`:

| Old | New |
|---|---|
| `C:\Users\whale\uiao-*` | `C:\Users\whale\src\uiao-*` |
| `c:\Users\whale\uiao-*` | `c:\Users\whale\src\uiao-*` |
| `C:/Users/whale/uiao-*` | `C:/Users/whale/src/uiao-*` |

Extensions scanned: `.md`, `.yml`, `.yaml`, `.py`, `.ps1`, `.sh`, `.qmd`,
`.json`, `.txt`. `.git/` is skipped. Idempotent — safe to re-run.

After running, commit the changes in each affected repo on its own branch.
