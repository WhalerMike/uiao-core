<#
.SYNOPSIS
  Migrate stale workspace paths across sibling repos.

.DESCRIPTION
  Replaces references to the old workspace layout (C:\Users\whale\uiao-*)
  with the new layout (C:\Users\whale\src\uiao-*) across specified repos.

  Handles three variants:
    C:\Users\whale\uiao-*   -> C:\Users\whale\src\uiao-*
    c:\Users\whale\uiao-*   -> c:\Users\whale\src\uiao-*   (lowercase drive)
    C:/Users/whale/uiao-*   -> C:/Users/whale/src/uiao-*   (forward slash)

  Safe to re-run: the new-form paths contain "whale\src\uiao-" which does
  not match the old pattern, so replacement is idempotent.

.PARAMETER WorkspaceRoot
  Parent directory containing the sibling repos. Defaults to the parent of
  the directory this script lives in (i.e. when run from uiao-core clone,
  defaults to C:\Users\whale\src).

.PARAMETER Repos
  Repos to scan. Default: uiao-docs, uiao-gos, uiao-impl.

.PARAMETER Extensions
  File extensions to scan. Default covers common text formats.

.PARAMETER WhatIf
  Preview only; do not modify files.

.EXAMPLE
  pwsh .\uiao-core\templates\claude-kit\migrate-old-paths.ps1 -WhatIf

.EXAMPLE
  pwsh .\uiao-core\templates\claude-kit\migrate-old-paths.ps1
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Medium')]
param(
    [string]$WorkspaceRoot,
    [string[]]$Repos = @('uiao-docs', 'uiao-gos', 'uiao-impl'),
    [string[]]$Extensions = @('.md', '.yml', '.yaml', '.py', '.ps1', '.sh', '.qmd', '.json', '.txt')
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$CoreRoot  = Split-Path -Parent (Split-Path -Parent $ScriptDir)

if (-not $WorkspaceRoot) {
    $WorkspaceRoot = Split-Path -Parent $CoreRoot
}
if (-not (Test-Path $WorkspaceRoot)) {
    throw "Workspace root not found: $WorkspaceRoot"
}

# Replacement pairs — order matters (longest first would matter if patterns
# overlapped, but these don't).
$Replacements = @(
    @{ Old = 'C:\Users\whale\uiao-'; New = 'C:\Users\whale\src\uiao-' },
    @{ Old = 'c:\Users\whale\uiao-'; New = 'c:\Users\whale\src\uiao-' },
    @{ Old = 'C:/Users/whale/uiao-'; New = 'C:/Users/whale/src/uiao-' }
)

$TotalFiles   = 0
$ChangedFiles = 0
$TotalHits    = 0

Write-Host "Workspace root: $WorkspaceRoot" -ForegroundColor Cyan
Write-Host "Repos:          $($Repos -join ', ')" -ForegroundColor Cyan
Write-Host ""

foreach ($repo in $Repos) {
    $repoPath = Join-Path $WorkspaceRoot $repo
    if (-not (Test-Path $repoPath)) {
        Write-Warning "Repo missing: $repoPath (skipping)"
        continue
    }

    Write-Host "==> $repo" -ForegroundColor Green

    $files = Get-ChildItem -Path $repoPath -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            $Extensions -contains $_.Extension -and
            $_.FullName -notmatch '[\\/]\.git[\\/]'
        }

    $repoChanged = 0
    $repoHits    = 0

    foreach ($file in $files) {
        $TotalFiles++
        try {
            $content = [System.IO.File]::ReadAllText($file.FullName)
        } catch {
            Write-Warning "  read failed: $($file.FullName) — $_"
            continue
        }

        $originalContent = $content
        $fileHits = 0
        foreach ($pair in $Replacements) {
            # Case-sensitive literal replacement via .NET (-creplace is regex).
            $before = $content
            $content = $content.Replace($pair.Old, $pair.New)
            if ($content -ne $before) {
                # Count occurrences replaced.
                $fileHits += ($before.Length - $content.Length) / ($pair.Old.Length - $pair.New.Length) * -1
            }
        }

        if ($content -ne $originalContent) {
            $repoChanged++
            $repoHits += $fileHits
            $relative = $file.FullName.Substring($repoPath.Length + 1)
            if ($PSCmdlet.ShouldProcess($file.FullName, "rewrite ($fileHits replacements)")) {
                [System.IO.File]::WriteAllText($file.FullName, $content)
                Write-Host "    $relative — $fileHits replacements"
            } else {
                Write-Host "    [preview] $relative — $fileHits replacements"
            }
        }
    }

    if ($repoChanged -eq 0) {
        Write-Host "    no changes" -ForegroundColor DarkGray
    } else {
        Write-Host "    $repoChanged files, $repoHits replacements" -ForegroundColor Yellow
    }
    Write-Host ""

    $ChangedFiles += $repoChanged
    $TotalHits    += $repoHits
}

Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  scanned: $TotalFiles files"
Write-Host "  changed: $ChangedFiles files"
Write-Host "  total replacements: $TotalHits"

if ($WhatIfPreference) {
    Write-Host ""
    Write-Host "Dry run — no files modified. Remove -WhatIf to apply." -ForegroundColor Yellow
}
