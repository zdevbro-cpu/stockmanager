param(
    [int]$Limit = 0,
    [int]$Offset = 0
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    $limitValue = if ($Limit -gt 0) { $Limit } else { "None" }
    $cmd = "import sys; sys.path.append('services/ingest'); from ingest.kis_loader import update_kis_prices_task; update_kis_prices_task(limit=$limitValue, offset=$Offset)"
    python -c $cmd
} finally {
    Pop-Location
}
