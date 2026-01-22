$ErrorActionPreference = "Stop"

Write-Host "run_local.ps1 start"

$root = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $root "apps\\api"
$webDir = Join-Path $root "apps\\web"
$apiVenvPython = Join-Path $apiDir ".venv\\Scripts\\python.exe"
$pythonExe = if (Test-Path $apiVenvPython) { $apiVenvPython } else { "python" }

function Require-Command {
    param([string]$Name)
    if (Test-Path $Name) {
        return
    }
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        throw "Missing command: $Name"
    }
}

function Invoke-Checked {
    param(
        [string]$Command,
        [string]$WorkDir
    )
    Push-Location $WorkDir
    try {
        & cmd /c $Command
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed ($LASTEXITCODE): $Command"
        }
    } finally {
        Pop-Location
    }
}

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

try {
    Write-Host "Environment check..."
    Require-Command "docker"
    Require-Command "npm"
    Require-Command $pythonExe

    Write-Host "Docker status..."
    Invoke-Checked -Command "docker info >nul 2>nul" -WorkDir $root

    Write-Host "Starting docker compose..."
    Invoke-Checked -Command "docker compose up -d" -WorkDir $root

    Write-Host "Starting API server..."
    Start-ConsoleProcess -Command "$pythonExe -m uvicorn app.main:app --reload --port 8010" -WorkDir $apiDir -Title "stockmanager-api"

    Write-Host "Starting web dev server..."
    Start-ConsoleProcess -Command "npm run dev -- --host" -WorkDir $webDir -Title "stockmanager-web"

    Write-Host "Done. Close the opened windows to stop API/Web."
} catch {
    Write-Host "Failed: $($_.Exception.Message)"
    exit 1
}
