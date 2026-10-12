#Requires -Version 7.0
[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$NonElevated
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)

$root = $PSScriptRoot
$pwsh = 'C:\Program Files\PowerShell\7\pwsh.exe'
$port = 18800

# ------------------------------------------------------------- 1. Elevate to administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin -and -not $NonElevated) {
    Write-Host 'Restarting as administrator (automation needs admin rights to control the game window)...' -ForegroundColor Cyan
    Start-Process -FilePath $pwsh -ArgumentList @('-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $root 'Start.ps1')) -Verb RunAs
    exit 0
}

# ------------------------------------------------------------- 2. Already running?
try {
    $res = Invoke-RestMethod -Uri "http://127.0.0.1:$port/api/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
    if ($res -and $res.ok) {
        Write-Host "Game Companion Local is already running (port $port)" -ForegroundColor Green
        if (-not $NoBrowser) {
            Start-Process "http://127.0.0.1:$port/"
        }
        exit 0
    }
} catch {}

# ------------------------------------------------------------- 3. Find Python and create the virtual environment
$venvPython = Join-Path $root '.venv\Scripts\python.exe'
$venvPythonw = Join-Path $root '.venv\Scripts\pythonw.exe'

if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host 'No virtual environment yet; creating .venv...' -ForegroundColor Cyan
    $basePython = $null
    $candidates = @(
        'C:\Python314\python.exe',
        'C:\Program Files\Python314\python.exe',
        (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue)
    )
    foreach ($cand in $candidates) {
        if ($cand -and (Test-Path -LiteralPath $cand)) {
            $basePython = $cand
            break
        }
    }
    if (-not $basePython) {
        Write-Error 'No Python interpreter found. Please install Python 3.10+ first.'
        exit 1
    }

    & $basePython -m venv (Join-Path $root '.venv')
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Error 'Failed to create the virtual environment.'
        exit 1
    }

    Write-Host 'Installing dependencies (requirements.txt)...' -ForegroundColor Cyan
    & $venvPython -m pip install --upgrade pip -q
    & $venvPython -m pip install -r (Join-Path $root 'requirements.txt') -q
}

# ------------------------------------------------------------- 4. Start the backend silently
Write-Host 'Starting the Game Companion Local backend...' -ForegroundColor Cyan
$launcher = if (Test-Path -LiteralPath $venvPythonw) { $venvPythonw } else { $venvPython }

$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $launcher
$startInfo.Arguments = '-m server'
$startInfo.WorkingDirectory = $root
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.CreateNoWindow = $true
$startInfo.UseShellExecute = $false

$proc = [System.Diagnostics.Process]::Start($startInfo)
if (-not $proc) {
    Write-Error 'Failed to start the backend process.'
    exit 1
}

# ------------------------------------------------------------- 5. Wait for the health check, then open the browser
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 300
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:$port/api/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($res -and $res.ok) {
            $ready = $true
            break
        }
    } catch {}
}

if ($ready) {
    Write-Host "Game Companion Local is ready: http://127.0.0.1:$port/" -ForegroundColor Green
    if (-not $NoBrowser) {
        Start-Process "http://127.0.0.1:$port/"
    }
} else {
    Write-Warning 'The backend did not start in time; check data/logs/app.log.'
}
