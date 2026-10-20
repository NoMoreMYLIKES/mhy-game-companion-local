#Requires -Version 7.0
[CmdletBinding()]
param([ValidateSet('Repros','Baseline','UI')][string]$Mode = 'Repros', [string]$Python)
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
if (-not $Python) { $Python = Join-Path $source '.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Supply -Python pointing to an environment with requirements.txt installed.' }
$run = Join-Path ([IO.Path]::GetTempPath()) ('gcl-logic-audit-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $run | Out-Null
$env:GCL_HOME = Join-Path $run 'runtime'
New-Item -ItemType Directory -Path $env:GCL_HOME | Out-Null
'synthetic' | Set-Content (Join-Path $env:GCL_HOME 'AUDIT_RUNTIME') -Encoding utf8
$env:PYTHONIOENCODING = 'utf-8'
$entry = switch ($Mode) { 'Baseline' {'run_baseline.py'} 'UI' {'serve_fixture.py'} default {'reproduce.py'} }
Write-Output "Isolated audit artifacts: $run"
if ($Mode -eq 'UI') {
    Write-Output 'Synthetic server only: http://127.0.0.1:18891/#/goals; Ctrl+C stops this fixture.'
    & $Python (Join-Path $PSScriptRoot $entry) $source
} else {
    & $Python (Join-Path $PSScriptRoot $entry) $source *> (Join-Path $run ($Mode + '.log'))
    $code = $LASTEXITCODE
    Get-Content (Join-Path $run ($Mode + '.log')) -Tail 8
    if ($Mode -eq 'Repros') {
        Write-Output 'Exit 1 means the audited defects are still reproduced. See repro-results.json and the log.'
    }
    exit $code
}
