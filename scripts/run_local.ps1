$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $root "apps\\api"
$webDir = Join-Path $root "apps\\web"

function Start-ConsoleProcess {
    param(
        [string]$Command,
        [string]$WorkDir,
        [string]$Title
    )
    $escaped = $Command.Replace('"', '""')
    $args = @(
        "-NoExit",
        "-Command",
        "Set-Location -LiteralPath `"$WorkDir`"; `$Host.UI.RawUI.WindowTitle = `"$Title`"; $escaped"
    )
    Start-Process -FilePath "powershell" -ArgumentList $args -WorkingDirectory $WorkDir | Out-Null
}

Write-Host "Starting docker compose..."
Push-Location $root
docker compose up -d
Pop-Location

Write-Host "Starting API server..."
Start-ConsoleProcess -Command "uvicorn app.main:app --reload --port 8010" -WorkDir $apiDir -Title "stockmanager-api"

Write-Host "Starting web dev server..."
Start-ConsoleProcess -Command "npm run dev -- --host" -WorkDir $webDir -Title "stockmanager-web"

Write-Host "Done. Close the opened windows to stop API/Web."
