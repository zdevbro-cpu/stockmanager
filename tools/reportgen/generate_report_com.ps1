# tools/reportgen/generate_report_com.ps1
param(
  [string]$Template = (Resolve-Path "docs\templates\project-report-template.dotx"),
  [string]$Out = (Resolve-Path "out\project-report.docx")
)

$ErrorActionPreference = "Stop"

$word = New-Object -ComObject Word.Application
$word.Visible = $false

try {
  $doc = $word.Documents.Add($Template)

  # 예: 간단 텍스트 치환(토큰 방식)
  $find = $word.Selection.Find
  $find.ClearFormatting()
  $find.Replacement.ClearFormatting()

  $find.Text = "{{project_name}}"
  $find.Replacement.Text = "CrossManager PMS"
  $find.Execute([ref]$null,[ref]$null,[ref]$null,[ref]$null,[ref]$null,[ref]$null,[ref]$null,[ref]$null,[ref]$null,[ref]$null,2) | Out-Null
  # 2 = wdReplaceAll

  $outDir = Split-Path $Out
  if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }

  $doc.SaveAs([ref]$Out)
  $doc.Close()
}
finally {
  $word.Quit()
  [System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
}
