$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
docker compose down
Pop-Location

Write-Host "Docker containers stopped. Close any API/Web windows manually."
