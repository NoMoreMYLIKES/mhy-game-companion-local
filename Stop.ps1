#Requires -Version 7.0
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)

$root = $PSScriptRoot
$pidFile = Join-Path $root 'data\server.pid'

if (Test-Path -LiteralPath $pidFile) {
    try {
        $meta = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
        $targetPid = [int]$meta.pid
        if ($targetPid -gt 0) {
            $proc = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "Stopping the Game Companion Local backend (PID: $targetPid)..." -ForegroundColor Cyan
                Stop-Process -Id $targetPid -Force
                Start-Sleep -Milliseconds 500
            }
        }
    } catch {
        Write-Warning "Failed to read the PID file: $($_.Exception.Message)"
    } finally {
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
    }
}

# Fallback: stop whatever still listens on port 18800
try {
    $connections = Get-NetTCPConnection -LocalPort 18800 -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        if ($conn.OwningProcess -gt 0) {
            Write-Host "Freeing the port (PID: $($conn.OwningProcess))..." -ForegroundColor Cyan
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
} catch {}

Write-Host 'Game Companion Local stopped.' -ForegroundColor Green
