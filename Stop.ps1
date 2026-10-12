#Requires -Version 7.0
<#
.SYNOPSIS
    Stops Game Companion Local.

.DESCRIPTION
    Stops this installation's backend: the one using the runtime folder in GCL_HOME (default:
    data next to this script), after checking that the process really is that backend.
    Programs that merely use the same port are never touched. A running batch is not
    interrupted unless -Force is given.

.PARAMETER Force
    Also stop a running batch: it is stopped first, its tool settings are restored, then the
    backend exits.

.NOTES
    Exit codes:
    0  stopped, or not running
    7  a batch is running (use -Force)
    8  the backend could not be stopped (for example: it runs as administrator and this
       PowerShell does not)
#>
[CmdletBinding()]
param([switch]$Force)
$ErrorActionPreference = 'Continue'
$PSNativeCommandUseErrorActionPreference = $false
try { [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false) } catch {}
$env:PYTHONIOENCODING = 'utf-8'

$root = $PSScriptRoot
$python = if ($IsWindows) { Join-Path $root '.venv\Scripts\python.exe' } else { Join-Path $root '.venv/bin/python' }
if (-not (Test-Path -LiteralPath $python)) {
    Write-Host 'Game Companion Local is not set up in this folder (.venv is missing), so it is not running.'
    exit 0
}

Push-Location -LiteralPath $root
try {
    $arguments = @('-m', 'server.launcher', 'stop')
    if ($Force) { $arguments += '--force' }
    & $python @arguments
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $code
