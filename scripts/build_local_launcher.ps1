$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $root "tools\\local_launcher.py"

if (-not (Test-Path $launcher)) {
    Write-Error "Launcher not found: $launcher"
    exit 1
}

Write-Host "Building local launcher executable..."
python -m pip install --upgrade pyinstaller
python -m pyinstaller --onefile --name stockmanager-local $launcher
Write-Host "Done. Executable is in dist\\stockmanager-local.exe"
