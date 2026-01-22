$ErrorActionPreference = "Stop"

$taskName = "stockmanager-daily-price"

schtasks /Delete /F /TN $taskName | Out-Null
Write-Host "삭제 완료: $taskName"
