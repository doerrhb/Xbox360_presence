[CmdletBinding()]
param(
    [string]$Python
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not $Python) {
    $Command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($Command) {
        $Python = $Command.Source
    } else {
        $FallbackPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"
        if (Test-Path $FallbackPython) {
            $Python = $FallbackPython
        }
    }
}

if (-not $Python) {
    throw "Python was not found. Install Python 3, or pass -Python C:\Path\To\python.exe."
}

Push-Location $Root
try {
    & $Python -m pip install -r requirements.txt

    $AddDefaultConfig = "config_default.ini;."
    $AddTitleIds = "xbox360titleids.json;."
    $AddAvatar = "avatar.ico;."

    & $Python -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --windowed `
        --name Xbox360Presence `
        --icon avatar.ico `
        --add-data $AddDefaultConfig `
        --add-data $AddTitleIds `
        --add-data $AddAvatar `
        --hidden-import pystray._win32 `
        xbox360_presence_tray.py

    Write-Host "Built $Root\dist\Xbox360Presence.exe"
}
finally {
    Pop-Location
}
