[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Default", "Natural", "0", "1")]
    [string]$Mode
)

function Test-Administrator {
    <#
    .SYNOPSIS
    Returns whether the current PowerShell process is running as Administrator.
    #>
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function ConvertTo-FlipFlopWheelValue {
    <#
    .SYNOPSIS
    Converts a user-facing scroll mode into the FlipFlopWheel registry value.
    #>
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("Default", "Natural", "0", "1")]
        [string]$ScrollMode
    )

    if ($ScrollMode -eq "Natural" -or $ScrollMode -eq "1") {
        return 1
    }

    return 0
}

function Get-ScrollModeName {
    <#
    .SYNOPSIS
    Returns the user-facing scroll mode name for a FlipFlopWheel value.
    #>
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet(0, 1)]
        [int]$Value
    )

    if ($Value -eq 1) {
        return "Natural"
    }

    return "Default"
}

if (-not (Test-Administrator)) {
    $scriptPath = (Resolve-Path -LiteralPath $PSCommandPath).Path
    $argumentList = @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "`"$scriptPath`"",
        "-Mode",
        $Mode
    )

    Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList $argumentList
    Write-Host "Started an elevated PowerShell process to update mouse wheel settings."
    exit 0
}

$value = ConvertTo-FlipFlopWheelValue -ScrollMode $Mode
$modeName = Get-ScrollModeName -Value $value
$devices = Get-PnpDevice -Class Mouse -PresentOnly -Status OK

if (-not $devices) {
    Write-Warning "No present mouse devices with status OK were found."
    exit 1
}

$results = foreach ($device in $devices) {
    $deviceId = $device.InstanceId
    if (-not $deviceId) {
        $deviceId = $device.DeviceID
    }

    $registryPath = "HKLM:\SYSTEM\CurrentControlSet\Enum\$deviceId\Device Parameters"

    if (-not (Test-Path -LiteralPath $registryPath)) {
        Write-Warning "Skipping device because its registry path was not found: $($device.FriendlyName)"
        continue
    }

    Set-ItemProperty -LiteralPath $registryPath -Name "FlipFlopWheel" -Value $value
    $currentValue = (Get-ItemProperty -LiteralPath $registryPath -Name "FlipFlopWheel").FlipFlopWheel

    [PSCustomObject]@{
        DeviceName = $device.FriendlyName
        InstanceId = $deviceId
        RegistryPath = $registryPath
        FlipFlopWheel = $currentValue
        Mode = $modeName
    }
}

$results | Format-Table -AutoSize
Write-Host "Mouse wheel mode set to $modeName. Restart Windows, sign out and sign in, or reconnect the mouse if the change is not immediate."
