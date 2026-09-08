#Requires -Version 5.1
<#
.SYNOPSIS
    Syncs latest Mopheus code to WSL Ubuntu-24.04 preview-test harness and starts preview services.
.PARAMETER SourcePath
    Source code directory on Windows host (default: main repo or current worktree).
#>
param(
    [string]$SourcePath = "C:\Users\kamus\CascadeProjects\mopheus"
)

$ErrorActionPreference = "Stop"

$wslDistro = "Ubuntu-24.04"
$wslHarnessUnc = "\\wsl.localhost\$wslDistro\home\kamus\CascadeProjects\mopheus\.worktrees\preview-test"
$wslHarnessScript = "/home/kamus/CascadeProjects/mopheus/.worktrees/preview-test/scripts/start_preview.sh"
$localScript = Join-Path $PSScriptRoot "start_preview_wsl.sh"

Write-Host "==> [1/3] Verifying source directory: $SourcePath" -ForegroundColor Cyan
if (-not (Test-Path $SourcePath)) {
    Write-Error "Source path does not exist: $SourcePath"
}

$xdWorktrees = if ($SourcePath -like "*\.worktrees\*") { "$SourcePath\.worktrees" } else { ".worktrees" }
robocopy $SourcePath $wslHarnessUnc /MIR /NFL /NDL /NJH /NJS /nc /ns /np /XD .git node_modules .next .turbo $xdWorktrees uploads dist bin __pycache__ /XF .env.worktree .env.local *.log *.pid *.tmp
if ($LASTEXITCODE -ge 8) {
    Write-Error "Robocopy failed with exit code $LASTEXITCODE"
}

# Ensure startup script is in place inside the harness
$harnessScriptUnc = Join-Path $wslHarnessUnc "scripts\start_preview.sh"
if (Test-Path $localScript) {
    Copy-Item -Path $localScript -Destination $harnessScriptUnc -Force
}

Write-Host "==> [3/3] Executing native startup in WSL ($wslDistro)..." -ForegroundColor Cyan
wsl -d $wslDistro -- bash $wslHarnessScript
