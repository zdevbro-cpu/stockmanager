$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot

Write-Host "Stopping API/Web processes..."
$targets = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -in @("python.exe", "node.exe") -and $_.CommandLine -match "uvicorn|vite|npm"
}
foreach ($proc in $targets) {
    try {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction Stop
        Write-Host "Stopped PID $($proc.ProcessId): $($proc.CommandLine)"
    } catch {
        Write-Host "Failed to stop PID $($proc.ProcessId): $($_.Exception.Message)"
    }
}

Write-Host "Done."
