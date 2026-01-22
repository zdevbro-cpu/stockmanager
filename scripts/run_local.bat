@echo off
setlocal
echo run_local.bat 실행
powershell -ExecutionPolicy Bypass -File "%~dp0run_local.ps1"
if errorlevel 1 (
  echo 실행 실패. 위 메시지를 확인하세요.
  pause
)
