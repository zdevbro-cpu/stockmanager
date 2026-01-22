@echo off
setlocal
echo run_local.bat start
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_local.ps1"
if errorlevel 1 (
  echo run_local.bat failed. See messages above.
  pause
)
