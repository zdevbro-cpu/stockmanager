$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $root "scripts\\backfill_yesterday_and_retention.py"
$apiVenvPython = Join-Path $root "apps\\api\\.venv\\Scripts\\python.exe"
$pythonExe = if (Test-Path $apiVenvPython) { $apiVenvPython } else { "python" }

$logDir = Join-Path $root "artifacts"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}
$logPath = Join-Path $logDir "daily_price_task.log"

Push-Location $root
try {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logPath -Value "=== daily price start $stamp ==="
    & $pythonExe $scriptPath 2>&1 | Tee-Object -FilePath $logPath -Append
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logPath -Value "=== daily price end $stamp ==="
} finally {
    Pop-Location
}
