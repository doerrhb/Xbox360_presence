[CmdletBinding()]
param(
    [string]$InnoCompiler
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExePath = Join-Path $Root "dist\Xbox360Presence.exe"
$InstallerScript = Join-Path $Root "installer\Xbox360Presence.iss"

if (-not (Test-Path $ExePath)) {
    & (Join-Path $Root "build_exe.ps1")
}

if (-not $InnoCompiler) {
    $Command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($Command) {
        $InnoCompiler = $Command.Source
    } else {
        $PossiblePaths = @(
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
        )
        foreach ($Path in $PossiblePaths) {
            if (Test-Path $Path) {
                $InnoCompiler = $Path
                break
            }
        }
    }
}

if (-not $InnoCompiler) {
    throw "Inno Setup 6 was not found. Install it, or pass -InnoCompiler C:\Path\To\ISCC.exe."
}

& $InnoCompiler $InstallerScript
Write-Host "Built $Root\dist\installer\Xbox360PresenceSetup.exe"
