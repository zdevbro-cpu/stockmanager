param(
    [string]$TaskName = "StockManager_KIS_Prices_Hourly"
)

$ScriptPath = Join-Path $PSScriptRoot "etl_kis_prices_30min.ps1"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00am -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Hours 7)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Force
