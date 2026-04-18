#!/usr/bin/env bash
# Install the UIAO Claude kit into sibling repos (uiao-docs, uiao-gos, uiao-impl).
#
# Usage:
#   install.sh [WORKSPACE_ROOT] [--force] [--clean] [--dry-run]
#
# By default refuses to overwrite existing files. --force overwrites. --clean
# removes existing .claude/ + CLAUDE.md before installing. --dry-run logs only.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_ROOT="$SCRIPT_DIR"
CORE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

WORKSPACE_ROOT=""
FORCE=0
CLEAN=0
DRY_RUN=0

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=1 ;;
        --clean) CLEAN=1 ;;
        --dry-run) DRY_RUN=1 ;;
        -*) echo "Unknown flag: $arg" >&2; exit 2 ;;
        *) WORKSPACE_ROOT="$arg" ;;
    esac
done

if [[ -z "$WORKSPACE_ROOT" ]]; then
    WORKSPACE_ROOT="$(cd "$CORE_ROOT/.." && pwd)"
fi

if [[ ! -d "$WORKSPACE_ROOT" ]]; then
    echo "Workspace root not found: $WORKSPACE_ROOT" >&2
    exit 1
fi

log() { printf '%s\n' "$*"; }
run() {
    if [[ $DRY_RUN -eq 1 ]]; then
        log "  [dry-run] $*"
    else
        "$@"
    fi
}

log "Workspace root: $WORKSPACE_ROOT"
log "Kit source:     $KIT_ROOT"
log ""

for repo in uiao-docs uiao-gos uiao-impl; do
    src="$KIT_ROOT/$repo"
    dst="$WORKSPACE_ROOT/$repo"

    if [[ ! -d "$src" ]]; then
        log "WARN: kit source missing for $repo; skipping."
        continue
    fi
    if [[ ! -d "$dst" ]]; then
        log "WARN: target repo not present: $dst (skipping)"
        continue
    fi

    log "==> $repo"

    if [[ $CLEAN -eq 1 ]]; then
        [[ -d "$dst/.claude" ]] && run rm -rf "$dst/.claude" && log "    removed $dst/.claude"
        [[ -f "$dst/CLAUDE.md" ]] && run rm -f "$dst/CLAUDE.md" && log "    removed $dst/CLAUDE.md"
    fi

    # CLAUDE.md
    if [[ -f "$src/CLAUDE.md" ]]; then
        if [[ -f "$dst/CLAUDE.md" && $FORCE -eq 0 && $CLEAN -eq 0 ]]; then
            log "    CLAUDE.md exists; skip (use --force or --clean)"
        else
            run cp "$src/CLAUDE.md" "$dst/CLAUDE.md"
            log "    wrote CLAUDE.md"
        fi
    fi

    # .claude/ tree
    if [[ -d "$src/.claude" ]]; then
        while IFS= read -r -d '' file; do
            rel="${file#$src/.claude/}"
            target="$dst/.claude/$rel"
            parent="$(dirname "$target")"
            [[ -d "$parent" ]] || run mkdir -p "$parent"
            if [[ -f "$target" && $FORCE -eq 0 && $CLEAN -eq 0 ]]; then
                log "    .claude/$rel exists; skip"
            else
                run cp "$file" "$target"
                log "    wrote .claude/$rel"
            fi
        done < <(find "$src/.claude" -type f -print0)
    fi

    log ""
done

log "Done."
