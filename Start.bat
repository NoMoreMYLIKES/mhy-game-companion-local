@echo off
setlocal
rem Starts Game Companion Local with PowerShell 7; exit codes are those of Start.ps1.
rem After a failure the window waits for a key when it was opened by double-click.
rem Set GCL_NO_PAUSE=1 to never wait (for scripts and scheduled tasks).
set "GCL_PWSH="
for %%P in (pwsh.exe) do set "GCL_PWSH=%%~$PATH:P"
if not defined GCL_PWSH if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" set "GCL_PWSH=%ProgramFiles%\PowerShell\7\pwsh.exe"
if not defined GCL_PWSH (
    echo PowerShell 7 was not found. Install it from https://aka.ms/powershell, then run Start.bat again.
    set "GCL_CODE=10"
    goto done
)
"%GCL_PWSH%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start.ps1" %*
set "GCL_CODE=%ERRORLEVEL%"
:done
if "%GCL_CODE%"=="0" exit /b 0
if defined GCL_NO_PAUSE exit /b %GCL_CODE%
echo "%CMDCMDLINE%" | find /i "%~nx0" >nul && pause
exit /b %GCL_CODE%
