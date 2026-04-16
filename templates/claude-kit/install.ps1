<#
.SYNOPSIS
  Install the UIAO Claude kit into sibling repos (uiao-docs, uiao-gos, uiao-impl).

.DESCRIPTION
  Copies templates/claude-kit/<repo>/CLAUDE.md and .claude/ into each sibling repo
  under the workspace root. By default refuses to overwrite existing files.

.PARAMETER WorkspaceRoot
  Parent directory containing uiao-core, uiao-docs, uiao-gos, uiao-impl.
  Defaults to the parent of uiao-core.

.PARAMETER Force
  Overwrite existing CLAUDE.md and .claude/ files in the sibling repos.

.PARAMETER Clean
  Remove the sibling repo's existing .claude/ tree and CLAUDE.md before installing.
  DESTRUCTIVE. Prompts for confirmation unless -Confirm:$false.

.PARAMETER WhatIf
  Show what would be done without copying.

.EXAMPLE
  pwsh ./templates/claude-kit/install.ps1

.EXAMPLE
  pwsh ./templates/claude-kit/install.ps1 -WorkspaceRoot C:\Users\whale\src -Force

.EXAMPLE
  pwsh ./templates/claude-kit/install.ps1 -Clean -Confirm:$false
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [string]$WorkspaceRoot,
    [switch]$Force,
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$KitRoot    = $ScriptRoot
$CoreRoot   = Split-Path -Parent (Split-Path -Parent $ScriptRoot)

if (-not $WorkspaceRoot) {
    $WorkspaceRoot = Split-Path -Parent $CoreRoot
}

if (-not (Test-Path $WorkspaceRoot)) {
    throw "Workspace root not found: $WorkspaceRoot"
}

$Targets = @('uiao-docs', 'uiao-gos', 'uiao-impl')

Write-Host "Workspace root: $WorkspaceRoot" -ForegroundColor Cyan
Write-Host "Kit source:     $KitRoot"       -ForegroundColor Cyan
Write-Host ""

foreach ($repo in $Targets) {
    $src = Join-Path $KitRoot $repo
    $dst = Join-Path $WorkspaceRoot $repo

    if (-not (Test-Path $src)) {
        Write-Warning "Kit source missing for $repo; skipping."
        continue
    }

    if (-not (Test-Path $dst)) {
        Write-Warning "Target repo not present: $dst (skipping)"
        continue
    }

    Write-Host "==> $repo" -ForegroundColor Green

    if ($Clean) {
        $oldClaude = Join-Path $dst '.claude'
        $oldMd     = Join-Path $dst 'CLAUDE.md'
        if (Test-Path $oldClaude) {
            if ($PSCmdlet.ShouldProcess($oldClaude, 'Remove existing .claude/')) {
                Remove-Item $oldClaude -Recurse -Force
                Write-Host "    removed $oldClaude"
            }
        }
        if (Test-Path $oldMd) {
            if ($PSCmdlet.ShouldProcess($oldMd, 'Remove existing CLAUDE.md')) {
                Remove-Item $oldMd -Force
                Write-Host "    removed $oldMd"
            }
        }
    }

    # CLAUDE.md
    $srcMd = Join-Path $src 'CLAUDE.md'
    $dstMd = Join-Path $dst 'CLAUDE.md'
    if ((Test-Path $dstMd) -and -not $Force -and -not $Clean) {
        Write-Warning "    CLAUDE.md exists; skip (use -Force or -Clean to replace)"
    } elseif (Test-Path $srcMd) {
        if ($PSCmdlet.ShouldProcess($dstMd, 'Write CLAUDE.md')) {
            Copy-Item $srcMd $dstMd -Force
            Write-Host "    wrote CLAUDE.md"
        }
    }

    # .claude/ tree
    $srcClaude = Join-Path $src '.claude'
    $dstClaude = Join-Path $dst '.claude'
    if (Test-Path $srcClaude) {
        if (-not (Test-Path $dstClaude)) {
            New-Item -ItemType Directory -Path $dstClaude -Force | Out-Null
        }
        Get-ChildItem $srcClaude -Recurse -File | ForEach-Object {
            $rel    = $_.FullName.Substring($srcClaude.Length + 1)
            $target = Join-Path $dstClaude $rel
            $parent = Split-Path -Parent $target
            if (-not (Test-Path $parent)) {
                New-Item -ItemType Directory -Path $parent -Force | Out-Null
            }
            if ((Test-Path $target) -and -not $Force -and -not $Clean) {
                Write-Warning "    .claude/$rel exists; skip"
            } else {
                if ($PSCmdlet.ShouldProcess($target, 'Write .claude file')) {
                    Copy-Item $_.FullName $target -Force
                    Write-Host "    wrote .claude/$rel"
                }
            }
        }
    }

    Write-Host ""
}

Write-Host "Done." -ForegroundColor Cyan
