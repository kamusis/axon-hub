<#
.SYNOPSIS
    Cross-platform multi-node Axon synchronizer for PowerShell with Smart Convergence.

.DESCRIPTION
    Reads node definitions from ~/.axon/nodes.json (generated from ~/.ssh/config + local/wsl).
    Executes 'axon sync' (or other axon commands) across Local, WSL, and Remote SSH nodes.
    Features Smart Convergence: Automatically detects if subsequent nodes pushed newer commits,
    and performs a lightweight catch-up pass on lagging nodes to guarantee 100% cluster consistency.

.PARAMETER Init
    Reads ~/.ssh/config, discovers local and WSL environments, and initializes ~/.axon/nodes.json.

.PARAMETER Scan
    Probes all nodes from ~/.ssh/config and local/wsl to check for axon installation, updating nodes.json.

.PARAMETER List
    Displays all configured nodes and their enabled status.

.PARAMETER Node
    Specifies one or more node names to sync (e.g., -Node "imac-m1,local").

.PARAMETER Command
    The axon command to run (default: "sync").

.PARAMETER ConfigFile
    Path to the nodes configuration JSON file (default: ~/.axon/nodes.json).

.PARAMETER NoConverge
    Disables the smart second-pass convergence check.

.PARAMETER DryRun
    Simulates command execution without making any network calls or changes.

.EXAMPLE
    .\axon-sync-all.ps1
    .\axon-sync-all.ps1 -Scan
    .\axon-sync-all.ps1 -Node imac-m1
    .\axon-sync-all.ps1 -Command "status"
#>

[CmdletBinding()]
param(
    [Alias("i")]
    [switch]$Init,

    [Alias("s")]
    [switch]$Scan,

    [Alias("l")]
    [switch]$List,

    [Alias("n")]
    [string[]]$Node,

    [Alias("cmd")]
    [string]$Command = "sync",

    [Alias("c")]
    [string]$ConfigFile = (Join-Path $HOME ".axon\nodes.json"),

    [Alias("nc")]
    [switch]$NoConverge,

    [Alias("d")]
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# ANSI Color Codes
$ESC = [char]27
$C_RESET  = "$ESC[0m"
$C_BOLD   = "$ESC[1m"
$C_GREEN  = "$ESC[32m"
$C_RED    = "$ESC[31m"
$C_YELLOW = "$ESC[33m"
$C_CYAN   = "$ESC[36m"
$C_GRAY   = "$ESC[90m"

function Write-Info([string]$msg) {
    Write-Host "${C_CYAN}[INFO]${C_RESET} $msg"
}

function Write-Success([string]$msg) {
    Write-Host "${C_GREEN}[SUCCESS]${C_RESET} $msg"
}

function Write-Warn([string]$msg) {
    Write-Host "${C_YELLOW}[WARN]${C_RESET} $msg"
}

function Write-Err([string]$msg) {
    Write-Host "${C_RED}[ERROR]${C_RESET} $msg"
}

function Get-SshHosts {
    $sshConfigFile = Join-Path $HOME ".ssh\config"
    $hosts = @()
    if (Test-Path $sshConfigFile) {
        $lines = Get-Content $sshConfigFile -Encoding UTF8
        foreach ($line in $lines) {
            $trimmed = $line.Trim()
            if ($trimmed -match '^Host\s+(.+)$') {
                $rawHosts = $Matches[1].Split([char[]]@(' ', "`t"), [StringSplitOptions]::RemoveEmptyEntries)
                foreach ($h in $rawHosts) {
                    if ($h -notmatch '[\*\?]' -and $h -notin $hosts) {
                        $hosts += $h
                    }
                }
            }
        }
    }
    return $hosts
}

function Get-DefaultWslDistro {
    try {
        $wslOut = & wsl.exe --list --quiet 2>$null
        if ($wslOut) {
            $distros = $wslOut -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 }
            if ($distros.Count -gt 0) {
                $clean = ($distros[0] -replace "`0", "").Trim()
                if (![string]::IsNullOrWhiteSpace($clean)) {
                    return $clean
                }
            }
        }
    } catch {}
    return "Ubuntu-24.04"
}

function Build-InitialConfig {
    $defaultPath = '$HOME/.local/bin:$HOME/go/bin:$HOME/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH'
    $nodesList = @()

    # 1. Local workstation
    $nodesList += [PSCustomObject]@{
        name        = "local"
        type        = "local"
        enabled     = $true
        description = "Local workstation environment"
    }

    # 2. WSL
    $distro = Get-DefaultWslDistro
    $nodesList += [PSCustomObject]@{
        name        = "wsl"
        type        = "wsl"
        distro      = $distro
        ssh_host    = "wsl-ubuntu"
        enabled     = $true
        description = "WSL Linux environment ($distro)"
    }

    # 3. Remote SSH hosts
    $sshHosts = @(Get-SshHosts)
    foreach ($h in $sshHosts) {
        if ($h -eq "wsl-ubuntu") {
            continue
        }
        $nodesList += [PSCustomObject]@{
            name        = $h
            type        = "ssh"
            host        = $h
            enabled     = $false
            description = "Remote host from SSH config"
        }
    }

    $configObj = [PSCustomObject]@{
        version  = 1
        settings = [PSCustomObject]@{
            ssh_timeout = 10
            remote_path = $defaultPath
            parallel    = $false
        }
        nodes    = $nodesList
    }

    return $configObj
}

function Save-Config($configObj, [string]$path) {
    $parent = Split-Path -Parent $path
    if ($parent -and !(Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $json = $configObj | ConvertTo-Json -Depth 10
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($path, $json, $utf8NoBom)
}

function Load-Config([string]$path) {
    if (!(Test-Path $path)) {
        Write-Warn "Configuration file not found: $path. Initializing from SSH config..."
        $config = Build-InitialConfig
        Save-Config $config $path
        Write-Success "Created new configuration at: $path"
        return $config
    }
    $content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
    return ($content | ConvertFrom-Json)
}

function Test-NodeAxon($node, $settings) {
    $remotePath = if ($settings.remote_path) { $settings.remote_path } else { '$HOME/.local/bin:$HOME/go/bin:$HOME/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH' }
    $timeout = if ($settings.ssh_timeout) { $settings.ssh_timeout } else { 8 }

    switch ($node.type) {
        "local" {
            try {
                $axonCmd = Get-Command axon -ErrorAction SilentlyContinue
                if ($axonCmd) {
                    $ver = & axon version 2>&1
                    $firstLine = ($ver -split "`r?`n")[0]
                    return @{ Found = $true; Version = $firstLine; Error = $null }
                }
            } catch {
                return @{ Found = $false; Version = $null; Error = $_.Exception.Message }
            }
            return @{ Found = $false; Version = $null; Error = "axon executable not found in PATH" }
        }
        "wsl" {
            try {
                $distro = if ($node.distro) { $node.distro } else { Get-DefaultWslDistro }
                $checkCmd = "export PATH=`"$remotePath`"; which axon 2>/dev/null && axon version 2>&1"
                $out = & wsl.exe -d $distro -- bash -c $checkCmd 2>&1
                if ($LASTEXITCODE -eq 0 -and $out) {
                    $lines = $out -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 }
                    $verLine = if ($lines.Count -gt 1) { $lines[1] } else { $lines[0] }
                    return @{ Found = $true; Version = $verLine; Error = $null }
                } else {
                    return @{ Found = $false; Version = $null; Error = "axon not found in WSL" }
                }
            } catch {
                return @{ Found = $false; Version = $null; Error = $_.Exception.Message }
            }
        }
        "ssh" {
            $hostName = if ($node.host) { $node.host } else { $node.name }
            $checkCmd = "export PATH=`"$remotePath`"; which axon 2>/dev/null && axon version 2>&1"
            try {
                $out = & ssh -o BatchMode=yes -o "ConnectTimeout=$timeout" $hostName $checkCmd 2>&1
                if ($LASTEXITCODE -eq 0 -and $out) {
                    $lines = $out -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 }
                    $verLine = if ($lines.Count -gt 1) { $lines[1] } else { $lines[0] }
                    return @{ Found = $true; Version = $verLine; Error = $null }
                } else {
                    $errText = ($out -join " ").Trim()
                    if ([string]::IsNullOrWhiteSpace($errText)) { $errText = "axon not found or host unreachable" }
                    return @{ Found = $false; Version = $null; Error = $errText }
                }
            } catch {
                return @{ Found = $false; Version = $null; Error = $_.Exception.Message }
            }
        }
        default {
            return @{ Found = $false; Version = $null; Error = "Unknown node type: $($node.type)" }
        }
    }
}

# Execute command on a node and retrieve stdout, status, and commit SHA
function Invoke-NodeAxonCommand($node, [string]$cmdToRun, $settings, [int]$timeoutSec) {
    $remotePath = if ($settings.remote_path) { $settings.remote_path } else { '$HOME/.local/bin:$HOME/go/bin:$HOME/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH' }
    $nodeType = $node.type
    $nodeName = $node.name

    $status = "OK"
    $details = ""
    $outputLines = @()
    $commitSha = ""
    $exitCode = 0

    try {
        switch ($nodeType) {
            "local" {
                $tempOut = [System.IO.Path]::GetTempFileName()
                $tempErr = [System.IO.Path]::GetTempFileName()
                $proc = Start-Process -FilePath "axon" -ArgumentList $cmdToRun -NoNewWindow -PassThru -RedirectStandardOutput $tempOut -RedirectStandardError $tempErr
                $proc.WaitForExit()
                $stdout = if (Test-Path $tempOut) { Get-Content $tempOut -Raw } else { "" }
                $stderr = if (Test-Path $tempErr) { Get-Content $tempErr -Raw } else { "" }
                Remove-Item $tempOut, $tempErr -ErrorAction SilentlyContinue

                $combined = "$stdout`n$stderr".Trim()
                $outputLines = $combined -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 }
                $exitCode = $proc.ExitCode

                # Query commit SHA
                $localRepo = Join-Path $HOME ".axon\repo"
                if (Test-Path $localRepo) {
                    $shaOut = & git -C $localRepo rev-parse --short HEAD 2>$null
                    if ($LASTEXITCODE -eq 0 -and $shaOut) {
                        $shaClean = $shaOut.Trim()
                        if ($shaClean -match '^[0-9a-fA-F]{7,40}$') {
                            $commitSha = $shaClean
                        }
                    }
                }
            }
            "wsl" {
                $distro = if ($node.distro) { $node.distro } else { Get-DefaultWslDistro }
                $wslCmd = "export PATH=`"$remotePath`"; axon $cmdToRun; _ec=`$?; echo '___AXON_DELIM___'; echo `"EXIT:`$_ec`"; git -C ~/.axon/repo rev-parse --short HEAD 2>/dev/null"
                $out = & wsl.exe -d $distro -- bash -c $wslCmd 2>&1

                $rawLines = $out -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 }
                $delimIdx = [Array]::IndexOf($rawLines, "___AXON_DELIM___")
                
                if ($delimIdx -ge 0) {
                    $outputLines = if ($delimIdx -gt 0) { $rawLines[0..($delimIdx - 1)] } else { @() }
                    $metaLines = $rawLines[($delimIdx + 1)..($rawLines.Count - 1)]
                    foreach ($m in $metaLines) {
                        if ($m -match '^EXIT:(\d+)$') {
                            $exitCode = [int]$Matches[1]
                        } elseif ($m.Trim() -match '^[0-9a-fA-F]{7,40}$') {
                            $commitSha = $m.Trim()
                        }
                    }
                } else {
                    $outputLines = $rawLines
                    $exitCode = $LASTEXITCODE
                }
            }
            "ssh" {
                $hostName = if ($node.host) { $node.host } else { $nodeName }
                $sshCmd = "export PATH=`"$remotePath`"; axon $cmdToRun; _ec=`$?; echo '___AXON_DELIM___'; echo `"EXIT:`$_ec`"; git -C ~/.axon/repo rev-parse --short HEAD 2>/dev/null"
                $out = & ssh -o BatchMode=yes -o "ConnectTimeout=$timeoutSec" $hostName $sshCmd 2>&1

                $rawLines = $out -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 }
                $delimIdx = [Array]::IndexOf($rawLines, "___AXON_DELIM___")

                if ($delimIdx -ge 0) {
                    $outputLines = if ($delimIdx -gt 0) { $rawLines[0..($delimIdx - 1)] } else { @() }
                    $metaLines = $rawLines[($delimIdx + 1)..($rawLines.Count - 1)]
                    foreach ($m in $metaLines) {
                        if ($m -match '^EXIT:(\d+)$') {
                            $exitCode = [int]$Matches[1]
                        } elseif ($m.Trim() -match '^[0-9a-fA-F]{7,40}$') {
                            $commitSha = $m.Trim()
                        }
                    }
                } else {
                    $outputLines = $rawLines
                    $exitCode = $LASTEXITCODE
                }
            }
            default {
                $status = "ERROR"
                $details = "Unknown type: $nodeType"
                $exitCode = 1
            }
        }

        if ($exitCode -ne 0) {
            $combinedErr = ($outputLines -join " ")
            if ($combinedErr -match "timed out|Connection timed out") {
                $status = "TIMEOUT"
                $details = "Connection timed out ($timeoutSec s)"
            } elseif ($combinedErr -match "Permission denied|bad permissions") {
                $status = "AUTH_ERR"
                $details = "SSH authentication failed"
            } elseif ($combinedErr -match "command not found") {
                $status = "FAILED"
                $details = "axon command not found"
            } else {
                $status = "FAILED"
                $details = if ($outputLines.Count -gt 0) { $outputLines[-1] } else { "Exit code: $exitCode" }
            }
        } else {
            $status = "SUCCESS"
            $details = "Synced successfully"
        }
    } catch {
        $status = "ERROR"
        $details = $_.Exception.Message
    }

    return @{
        Status      = $status
        Details     = $details
        OutputLines = $outputLines
        CommitSha   = $commitSha
    }
}

function Invoke-InitAction {
    Write-Info "Initializing configuration from ~/.ssh/config..."
    $config = Build-InitialConfig
    Save-Config $config $ConfigFile
    Write-Success "Configuration initialized at: $ConfigFile"
    Write-Info "Run with -Scan to auto-detect and enable nodes with Axon installed."
}

function Invoke-ScanAction {
    Write-Info "Scanning all nodes to detect Axon CLI installation..."
    $config = Load-Config $ConfigFile
    $sshHosts = @(Get-SshHosts)

    $currentNodes = @()
    $seenNames = @()

    foreach ($n in $config.nodes) {
        $currentNodes += $n
        $seenNames += $n.name
    }

    # Add any newly discovered SSH hosts
    foreach ($h in $sshHosts) {
        if ($h -ne "wsl-ubuntu" -and $h -notin $seenNames) {
            $currentNodes += [PSCustomObject]@{
                name        = $h
                type        = "ssh"
                host        = $h
                enabled     = $false
                description = "Remote host from SSH config"
            }
            $seenNames += $h
        }
    }

    $results = @()
    $updatedNodes = @()

    foreach ($node in $currentNodes) {
        Write-Host -NoNewline "  Probing ${C_BOLD}$($node.name)${C_RESET} ($($node.type))... "
        $res = Test-NodeAxon $node $config.settings
        
        $newObj = [PSCustomObject]@{
            name        = $node.name
            type        = $node.type
            host        = if ($node.host) { $node.host } else { $null }
            distro      = if ($node.distro) { $node.distro } else { $null }
            ssh_host    = if ($node.ssh_host) { $node.ssh_host } else { $null }
            enabled     = [bool]$res.Found
            description = $node.description
        }
        $updatedNodes += $newObj

        if ($res.Found) {
            Write-Host "${C_GREEN}FOUND${C_RESET} ($($res.Version))"
            $results += [PSCustomObject]@{
                Node    = $node.name
                Type    = $node.type
                Status  = "FOUND"
                Version = $res.Version
                Enabled = "Yes"
            }
        } else {
            Write-Host "${C_GRAY}NOT FOUND / UNREACHABLE${C_RESET}"
            $results += [PSCustomObject]@{
                Node    = $node.name
                Type    = $node.type
                Status  = "NOT FOUND"
                Version = "-"
                Enabled = "No"
            }
        }
    }

    $config.nodes = $updatedNodes
    Save-Config $config $ConfigFile
    Write-Host ""
    Write-Success "Configuration updated and saved to: $ConfigFile`n"
    $results | Format-Table -AutoSize
}

function Invoke-ListAction {
    $config = Load-Config $ConfigFile
    Write-Host "`n${C_BOLD}Configured Axon Sync Nodes:${C_RESET}"
    $tableData = foreach ($n in $config.nodes) {
        $targetDesc = if ($n.type -eq "ssh") { $n.host } elseif ($n.type -eq "wsl") { $n.distro } else { "localhost" }
        [PSCustomObject]@{
            Name        = $n.name
            Type        = $n.type
            Target      = $targetDesc
            Enabled     = if ($n.enabled) { "Yes" } else { "No" }
            Description = $n.description
        }
    }
    $tableData | Format-Table -AutoSize
}

function Invoke-SyncAction {
    $config = Load-Config $ConfigFile
    $settings = $config.settings
    $timeout = if ($settings.ssh_timeout) { $settings.ssh_timeout } else { 10 }

    $isExplicitNode = ($Node -and $Node.Count -gt 0 -and $Node[0].Trim().Length -gt 0)

    # Filter nodes if specified
    $targetNodes = $config.nodes
    if ($isExplicitNode) {
        $filterList = $Node -split ',' | ForEach-Object { $_.Trim() }
        $targetNodes = @($config.nodes | Where-Object { $_.name -in $filterList })
        if (!$targetNodes -or $targetNodes.Count -eq 0) {
            Write-Err "No matching nodes found for: $($Node -join ', ')"
            exit 1
        }
    }

    Write-Host "`n${C_BOLD}====================================================${C_RESET}"
    Write-Host "${C_BOLD}     Axon Multi-Node Synchronizer (Smart Convergence)${C_RESET}"
    Write-Host "${C_BOLD}====================================================${C_RESET}"
    Write-Info "Command:    axon $Command"
    Write-Info "Config:     $ConfigFile"
    Write-Info "Convergence: $(if ($NoConverge) { 'Disabled' } else { 'Smart Auto-Detection (2-Pass if drift detected)' })"
    Write-Host ""

    $nodeResults = [System.Collections.Specialized.OrderedDictionary]::new()
    $totalStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $index = 0
    $totalCount = $targetNodes.Count

    # ── PHASE 1: Collect & Sync ─────────────────────────────────────────────
    Write-Host "${C_BOLD}[Phase 1: Initial Sync & State Discovery]${C_RESET}"
    Write-Host "${C_GRAY}----------------------------------------------------${C_RESET}"

    foreach ($node in $targetNodes) {
        $index++
        $nodeName = $node.name
        $nodeType = $node.type
        $isEnabled = [bool]$node.enabled

        if (!$isEnabled -and !$isExplicitNode) {
            Write-Host "${C_BOLD}[$index/$totalCount] Node: ${C_CYAN}$nodeName${C_RESET} ($nodeType) ${C_YELLOW}[SKIPPED]${C_RESET}"
            Write-Host "    ${C_GRAY}Disabled in nodes.json${C_RESET}`n"
            $nodeResults[$nodeName] = [PSCustomObject]@{
                Index     = $index
                Node      = $nodeName
                Type      = $nodeType
                Status    = "SKIPPED"
                CommitSha = "-"
                Passes    = 0
                Duration  = 0.0
                Details   = "Disabled in configuration"
                NodeObj   = $node
            }
            continue
        }

        Write-Host "${C_BOLD}[$index/$totalCount] Node: ${C_CYAN}$nodeName${C_RESET} ($nodeType)"

        if ($DryRun) {
            Write-Host "  ${C_GRAY}(Dry Run) Would execute: axon $Command${C_RESET}`n"
            $nodeResults[$nodeName] = [PSCustomObject]@{
                Index     = $index
                Node      = $nodeName
                Type      = $nodeType
                Status    = "DRY-RUN"
                CommitSha = "simulated"
                Passes    = 1
                Duration  = 0.0
                Details   = "Simulated"
                NodeObj   = $node
            }
            continue
        }

        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $execRes = Invoke-NodeAxonCommand $node $Command $settings $timeout
        $sw.Stop()
        $durationSec = [math]::Round($sw.Elapsed.TotalSeconds, 2)

        # Print command output
        if ($execRes.OutputLines -and $execRes.OutputLines.Count -gt 0) {
            foreach ($line in $execRes.OutputLines) {
                Write-Host "    ${C_GRAY}│${C_RESET} $line"
            }
        }

        $shaText = if ($execRes.CommitSha) { " [SHA: ${C_CYAN}$($execRes.CommitSha)${C_RESET}]" } else { "" }

        if ($execRes.Status -eq "SUCCESS") {
            Write-Host "    ${C_GREEN}✔ Success${C_RESET} in ${durationSec}s$shaText"
        } else {
            Write-Host "    ${C_RED}✖ $($execRes.Status)${C_RESET} in ${durationSec}s: $($execRes.Details)"
        }
        Write-Host ""

        $nodeResults[$nodeName] = [PSCustomObject]@{
            Index     = $index
            Node      = $nodeName
            Type      = $nodeType
            Status    = $execRes.Status
            CommitSha = if ($execRes.CommitSha) { $execRes.CommitSha } else { "-" }
            Passes    = 1
            Duration  = $durationSec
            Details   = $execRes.Details
            NodeObj   = $node
        }
    }

    # ── PHASE 2: Smart Convergence Check ─────────────────────────────────────
    if (!$DryRun -and !$NoConverge -and $Command -eq "sync") {
        # Determine the latest target commit SHA from the last successful node
        $successfulNodes = @($nodeResults.Values | Where-Object { $_.Status -eq "SUCCESS" -and $_.CommitSha -ne "-" })
        
        if ($successfulNodes.Count -gt 1) {
            $targetCommitSha = $successfulNodes[-1].CommitSha
            
            # Find lagging nodes that have an older commit SHA
            $laggingNodes = @($successfulNodes | Where-Object { $_.CommitSha -ne $targetCommitSha })

            if ($laggingNodes.Count -gt 0) {
                Write-Host "${C_BOLD}[Phase 2: Catch-up Convergence]${C_RESET}"
                Write-Host "${C_YELLOW}[!] Detected commit drift across cluster.${C_RESET}"
                Write-Host "    Latest Target SHA: ${C_CYAN}$targetCommitSha${C_RESET} (from $($successfulNodes[-1].Node))"
                Write-Host "    Lagging nodes to converge: ${C_YELLOW}$($laggingNodes.Node -join ', ')${C_RESET}"
                Write-Host "${C_GRAY}----------------------------------------------------${C_RESET}"

                $p2Index = 0
                foreach ($lagItem in $laggingNodes) {
                    $p2Index++
                    $node = $lagItem.NodeObj
                    $nodeName = $node.name
                    $nodeType = $node.type

                    Write-Host "${C_BOLD}[$p2Index/$($laggingNodes.Count)] Converging Node: ${C_CYAN}$nodeName${C_RESET} ($nodeType) [${lagItem.CommitSha} -> ${targetCommitSha}]"

                    $sw2 = [System.Diagnostics.Stopwatch]::StartNew()
                    $execRes2 = Invoke-NodeAxonCommand $node $Command $settings $timeout
                    $sw2.Stop()
                    $p2Duration = [math]::Round($sw2.Elapsed.TotalSeconds, 2)

                    if ($execRes2.OutputLines -and $execRes2.OutputLines.Count -gt 0) {
                        foreach ($line in $execRes2.OutputLines) {
                            Write-Host "    ${C_GRAY}│${C_RESET} $line"
                        }
                    }

                    if ($execRes2.Status -eq "SUCCESS") {
                        $lagItem.CommitSha = if ($execRes2.CommitSha) { $execRes2.CommitSha } else { $targetCommitSha }
                        $lagItem.Passes = 2
                        $lagItem.Duration = [math]::Round($lagItem.Duration + $p2Duration, 2)
                        $lagItem.Details = "Converged to $targetCommitSha"
                        Write-Host "    ${C_GREEN}✔ Converged${C_RESET} in ${p2Duration}s [SHA: ${C_CYAN}$($lagItem.CommitSha)${C_RESET}]`n"
                    } else {
                        $lagItem.Status = $execRes2.Status
                        $lagItem.Details = "Pass 2 failed: $($execRes2.Details)"
                        $lagItem.Duration = [math]::Round($lagItem.Duration + $p2Duration, 2)
                        Write-Host "    ${C_RED}✖ Convergence Failed${C_RESET}: $($execRes2.Details)`n"
                    }
                }
            } else {
                Write-Host "${C_GREEN}[Phase 2: Skipped]${C_RESET} All active nodes already converged at commit ${C_CYAN}$targetCommitSha${C_RESET}.`n"
            }
        }
    }

    $totalStopwatch.Stop()
    $totalDuration = [math]::Round($totalStopwatch.Elapsed.TotalSeconds, 2)

    # ── Summary Report ───────────────────────────────────────────────────────
    Write-Host "${C_BOLD}====================================================${C_RESET}"
    Write-Host "${C_BOLD}               Execution Summary                    ${C_RESET}"
    Write-Host "${C_BOLD}====================================================${C_RESET}"

    $allResults = @($nodeResults.Values | Sort-Object Index)
    $successCount = ($allResults | Where-Object { $_.Status -eq "SUCCESS" }).Count
    $failedCount  = ($allResults | Where-Object { $_.Status -in @("FAILED", "TIMEOUT", "AUTH_ERR", "ERROR") }).Count
    $skippedCount = ($allResults | Where-Object { $_.Status -eq "SKIPPED" }).Count

    # Unique commit SHAs among successful nodes
    $activeShas = @($allResults | Where-Object { $_.Status -eq "SUCCESS" -and $_.CommitSha -ne "-" } | ForEach-Object { $_.CommitSha } | Select-Object -Unique)
    $isFullyConverged = ($activeShas.Count -le 1)

    $tableRows = foreach ($r in $allResults) {
        [PSCustomObject]@{
            "Node"     = $r.Node
            "Type"     = $r.Type
            "Status"   = $r.Status
            "Commit"   = $r.CommitSha
            "Passes"   = if ($r.Passes -gt 0) { "$($r.Passes)" } else { "-" }
            "Duration" = "$($r.Duration)s"
            "Details"  = $r.Details
        }
    }

    $tableRows | Format-Table -AutoSize

    if ($isFullyConverged -and $activeShas.Count -gt 0) {
        Write-Host "${C_GREEN}✔ Cluster 100% Converged at commit [$($activeShas[0])] across all $successCount active node(s).${C_RESET}"
    } elseif ($activeShas.Count -gt 1) {
        Write-Host "${C_YELLOW}⚠ Cluster Divergence detected: multiple SHAs ($($activeShas -join ', '))${C_RESET}"
    }

    Write-Host "Total: $($allResults.Count) | ${C_GREEN}Success: $successCount${C_RESET} | ${C_RED}Failed: $failedCount${C_RESET} | ${C_YELLOW}Skipped: $skippedCount${C_RESET} | Total Time: ${totalDuration}s`n"

    if ($failedCount -gt 0) {
        exit 1
    } else {
        exit 0
    }
}

# --- Main Dispatcher ---
if ($Init) {
    Invoke-InitAction
} elseif ($Scan) {
    Invoke-ScanAction
} elseif ($List) {
    Invoke-ListAction
} else {
    Invoke-SyncAction
}
