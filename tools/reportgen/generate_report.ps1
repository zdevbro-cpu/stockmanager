# tools/reportgen/generate_report.ps1

param(
  [string]$Template = "docs/templates/project-report-template.TEMPLATE.docx",
  [string]$Out = "out/project-report.docx",
  [string]$Data = "docs/report-data.json",
  [string]$ProjectId = "DEMO-PROJECT",
  [string]$AsOf = "2026-01-01",
  [switch]$InitJson
)

$ErrorActionPreference = "Stop"

if (!(Test-Path ".\.venv\Scripts\Activate.ps1")) {
  python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
pip install -q docxtpl python-docx

Write-Host "1) Scan template tokens"
python tools/reportgen/generate_report.py --template $Template --scan-only

if ($InitJson) {
  Write-Host "2) Generate JSON skeleton from template tokens"
  $skeletonPath = "docs/report-data.skeleton.json"
  python tools/reportgen/generate_report.py --template $Template --init-json | Set-Content -Path $skeletonPath -Encoding UTF8
  Write-Host "   Saved: $skeletonPath"
}

Write-Host "3) File mode example"
python tools/reportgen/generate_report.py --template $Template --data $Data --out $Out

Write-Host "4) System mode example (stub)"
python tools/reportgen/generate_report.py --template $Template --source system --project_id $ProjectId --asof $AsOf --out $Out
