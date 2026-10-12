@echo off
set "PWSH=C:\Program Files\PowerShell\7\pwsh.exe"
if not exist "%PWSH%" (
    echo [ERROR] PowerShell 7 not found: %PWSH%
    pause
    exit /b 1
)
"%PWSH%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start.ps1" %*
