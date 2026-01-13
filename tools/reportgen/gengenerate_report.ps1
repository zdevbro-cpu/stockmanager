# tools/reportgen/generate_report.ps1

param(
  [string]$Template = "docs/templates/project-report-template.docx",
  [string]$Data = "docs/report-data.json",
  [string]$Out = "out/project-report.docx"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path ".\.venv\Scripts\Activate.ps1")) {
  python -m venv .venv
}

.\.venv\Scripts\Activate.ps1
pip install -q docxtpl python-docx

python tools/reportgen/generate_report.py $Template $Data $Out
