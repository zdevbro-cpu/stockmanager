$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$taskName = "stockmanager-daily-price"
$runner = Join-Path $root "scripts\\run_daily_price.ps1"
$startTime = "18:10"

$action = "powershell -NoProfile -ExecutionPolicy Bypass -File `"$runner`""

schtasks /Create /F /SC DAILY /ST $startTime /TN $taskName /TR $action | Out-Null
Write-Host "등록 완료: $taskName (매일 $startTime)"
