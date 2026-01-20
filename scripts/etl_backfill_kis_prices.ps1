param(
    [int]$Days = 252,
    [string]$Tickers = "",
    [switch]$Watchlist,
    [int]$Limit = 0,
    [int]$Offset = 0
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    $argsList = @("scripts/backfill_kis_prices.py", "--days", $Days)
    if ($Tickers) {
        $argsList += @("--tickers", $Tickers)
    }
    if ($Watchlist) {
        $argsList += "--watchlist"
    }
    if ($Limit -gt 0) {
        $argsList += @("--limit", $Limit)
    }
    if ($Offset -gt 0) {
        $argsList += @("--offset", $Offset)
    }
    python @argsList
} finally {
    Pop-Location
}
