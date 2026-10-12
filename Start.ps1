#Requires -Version 7.0
<#
.SYNOPSIS
    Starts Game Companion Local in the background and opens the dashboard.

.DESCRIPTION
    Sets up .venv on first use, asks for administrator rights (automation needs them to
    control the game window), then starts the backend with server.launcher, which waits
    until the backend answers and explains any failure. Address and runtime folder are the
    ones the backend uses: GCL_HOME (default: data next to this script) and the port in its
    settings.json.

.PARAMETER NoBrowser
    Do not open the dashboard.

.PARAMETER NonElevated
    Start without administrator rights. The dashboard works; game automation may not.

.PARAMETER Port
    Save this port for this installation, then start.

.PARAMETER Timeout
    Seconds to wait for the backend to become ready (default 60).

.NOTES
    Exit codes:
     0  ready, or already running
     3  settings.json cannot be used
     4  the address is used by another program or installation
     5  the backend exited while starting
     6  the backend was not ready in time (it was stopped)
    10  Python 3.10 or newer was not found
    11  .venv cannot be created or does not run
    12  the Python packages cannot be installed
    13  administrator rights were not granted
    14  the administrator window ended without a result
#>
[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [switch]$NonElevated,
    [int]$Port,
    [ValidateRange(5, 600)][int]$Timeout = 60,
    # Internal: used when this script restarts itself as administrator.
    [Parameter(DontShow)][switch]$Elevated,
    [Parameter(DontShow)][string]$ResultFile,
    [Parameter(DontShow)][string]$DataDir
)
$ErrorActionPreference = 'Continue'  # native exit codes are checked one by one below
$PSNativeCommandUseErrorActionPreference = $false
try { [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false) } catch {}
$env:PYTHONIOENCODING = 'utf-8'

$root = $PSScriptRoot
$venv = Join-Path $root '.venv'
$python = if ($IsWindows) { Join-Path $venv 'Scripts\python.exe' } else { Join-Path $venv 'bin/python' }
$script:readyUrl = $null

function Test-Admin {
    if (-not $IsWindows) { return $false }
    $principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-Python {
    # The first Python 3.10+ among: the py launcher, PATH, the usual install folders (newest first).
    $candidates = [Collections.Generic.List[object]]::new()
    if ($IsWindows) {
        foreach ($cmd in @(Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue)) {
            $candidates.Add(@($cmd.Source, '-3'))
        }
        foreach ($cmd in @(Get-Command python.exe, python3.exe -CommandType Application -All -ErrorAction SilentlyContinue)) {
            $candidates.Add(@($cmd.Source))
        }
        $patterns = "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe", "$env:ProgramFiles\Python3*\python.exe", "$env:SystemDrive\Python3*\python.exe"
        $installed = @(Get-ChildItem -Path $patterns -ErrorAction SilentlyContinue |
            Sort-Object { if ($_.Directory.Name -match '^Python3(\d+)') { [int]$Matches[1] } else { 0 } } -Descending)
        foreach ($file in $installed) { $candidates.Add(@($file.FullName)) }
    } else {
        foreach ($cmd in @(Get-Command python3, python -CommandType Application -All -ErrorAction SilentlyContinue)) {
            $candidates.Add(@($cmd.Source))
        }
    }
    foreach ($candidate in $candidates) {
        $exe = $candidate[0]
        $extra = @($candidate | Select-Object -Skip 1)
        $out = @(& $exe @extra -c 'import sys; print(sys.version_info >= (3, 10)); print(sys.executable)' 2>$null)
        if ($LASTEXITCODE -eq 0 -and $out.Count -ge 2 -and $out[0] -eq 'True') { return $out[1] }
    }
    return $null
}

function ConvertTo-Argument([string]$Value) {
    # One argument quoted for a Windows command line (CommandLineToArgvW rules).
    if ($Value -and $Value -notmatch '[\s"]') { return $Value }
    $escaped = ($Value -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1'
    return '"' + $escaped + '"'
}

function Read-AppendedText([string]$Path, [ref]$Offset) {
    # Complete lines appended to $Path since the last call; a line still being written waits for the next call.
    $stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete)
    try {
        $length = [int]($stream.Length - $Offset.Value)
        if ($length -le 0) { return }
        $buffer = [byte[]]::new($length)
        $null = $stream.Seek($Offset.Value, [IO.SeekOrigin]::Begin)
        $read = 0
        while ($read -lt $length) {
            $n = $stream.Read($buffer, $read, $length - $read)
            if ($n -le 0) { break }
            $read += $n
        }
    } finally {
        $stream.Dispose()
    }
    if ($read -le 0) { return }
    $end = [Array]::LastIndexOf($buffer, [byte]10, $read - 1)
    if ($end -lt 0) { return }
    $Offset.Value += $end + 1
    $lines = [Text.Encoding]::UTF8.GetString($buffer, 0, $end + 1) -split "`r?`n"
    $lines[0..($lines.Count - 2)]
}

function Invoke-Launcher {
    # Runs server.launcher, shows its output as it comes, and remembers the dashboard address.
    & $python -m server.launcher @args | ForEach-Object {
        if ($_ -match '^Ready: (\S+)') { $script:readyUrl = $Matches[1] } else { Write-Host $_ }
    }
    return $LASTEXITCODE
}

function Open-Dashboard([string]$Url) {
    if ($NoBrowser -or -not $Url) { return }
    if (-not $IsWindows) { return }
    if (Test-Admin) {
        Start-Process explorer.exe $Url  # opens the browser as the signed-in user, not as administrator
    } else {
        Start-Process $Url
    }
}

function Start-Elevated([string]$RuntimeFolder) {
    # Restarts this script as administrator in a hidden window and relays its output and exit code.
    $resultFile = Join-Path ([IO.Path]::GetTempPath()) "gcl-start-$([guid]::NewGuid().ToString('N')).log"
    $null = New-Item -ItemType File -Path $resultFile -Force
    $arguments = '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $root 'Start.ps1'),
        '-Elevated', '-ResultFile', $resultFile, '-DataDir', $RuntimeFolder, '-Timeout', "$Timeout"
    $commandLine = ($arguments | ForEach-Object { ConvertTo-Argument $_ }) -join ' '
    # pwsh.exe on PATH first: for a Microsoft Store install that is the alias that can be started
    $pwsh = @(Get-Command pwsh.exe -CommandType Application -ErrorAction SilentlyContinue)[0].Source
    if (-not $pwsh) { $pwsh = Join-Path $PSHOME 'pwsh.exe' }
    Write-Host 'Asking for administrator rights (automation needs them to control the game window)...'
    try {
        $process = Start-Process -FilePath $pwsh -ArgumentList $commandLine -Verb RunAs -WindowStyle Hidden -PassThru -ErrorAction Stop
    } catch {
        $declined = $false
        for ($e = $_.Exception; $e; $e = $e.InnerException) {
            if ($e -is [ComponentModel.Win32Exception] -and $e.NativeErrorCode -eq 1223) { $declined = $true }
        }
        if ($declined) {
            Write-Host 'Administrator rights were declined, so the backend was not started.'
        } else {
            Write-Host "Could not get administrator rights: $($_.Exception.Message)"
        }
        Write-Host 'Run Start.bat again and allow it, or start without them (game automation may not work): Start.bat -NonElevated'
        Remove-Item -LiteralPath $resultFile -ErrorAction SilentlyContinue
        return 13
    }
    $null = $process.Handle  # keeps the exit code readable after the process ends
    $offset = 0L
    $code = $null
    $deadline = [DateTime]::UtcNow.AddSeconds($Timeout + 120)
    while ($true) {
        $exited = $process.HasExited
        foreach ($line in @(Read-AppendedText $resultFile ([ref]$offset))) {
            if ($line -match '^@@EXIT (-?\d+)$') { $code = [int]$Matches[1]; continue }
            if ($line -match '^Ready: (\S+)') { $script:readyUrl = $Matches[1]; continue }
            Write-Host $line
        }
        if ($exited -or $null -ne $code) { break }
        if ([DateTime]::UtcNow -gt $deadline) { break }
        Start-Sleep -Milliseconds 200
    }
    if ($null -eq $code) {
        $exitCode = if ($process.HasExited) { $process.ExitCode } else { 'none, still running' }
        Write-Host "The administrator window ended without reporting a result (its exit code: $exitCode)."
        Write-Host "Its output is kept in: $resultFile"
        return 14
    }
    Remove-Item -LiteralPath $resultFile -ErrorAction SilentlyContinue
    return $code
}

# ------------------------------------------------------------- Elevated copy: start and report
if ($Elevated) {
    # One writer for the whole run, shared for reading: the waiting parent reads the file while it grows.
    $file = [IO.File]::Open($ResultFile, [IO.FileMode]::Append, [IO.FileAccess]::Write, [IO.FileShare]::ReadWrite)
    $writer = [IO.StreamWriter]::new($file, [Text.UTF8Encoding]::new($false))
    $writer.AutoFlush = $true
    $code = 14
    try {
        if ($DataDir) { $env:GCL_HOME = $DataDir }
        Set-Location -LiteralPath $root
        & $python -m server.launcher start --no-browser --timeout $Timeout 2>&1 | ForEach-Object { $writer.WriteLine("$_") }
        $code = $LASTEXITCODE
    } catch {
        $writer.WriteLine("Error in the administrator window: $($_.Exception.Message)")
    } finally {
        $writer.WriteLine("@@EXIT $code")
        $writer.Dispose()
    }
    exit $code
}

Push-Location -LiteralPath $root
try {
    # --------------------------------------------------------- 1. Python environment
    if (-not (Test-Path -LiteralPath $python)) {
        $base = Find-Python
        if (-not $base) {
            Write-Host 'Python 3.10 or newer was not found. Install it from https://www.python.org/downloads/'
            Write-Host '(select "Add python.exe to PATH"), then run Start.bat again.'
            exit 10
        }
        Write-Host "Creating the virtual environment in $venv with $base..."
        & $base -m venv $venv
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $python)) {
            Write-Host "Could not create $venv (exit code $LASTEXITCODE)."
            exit 11
        }
    }
    & $python -c 'import sys' 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "The Python in $venv does not run; the Python it was made from may have been removed or upgraded."
        Write-Host 'Delete the .venv folder and run Start.bat again.'
        exit 11
    }

    # --------------------------------------------------------- 2. Packages: install when requirements.txt changed or one is missing
    $requirements = Join-Path $root 'requirements.txt'
    $stampFile = Join-Path $venv 'gcl-requirements.sha256'
    $wanted = (Get-FileHash -LiteralPath $requirements -Algorithm SHA256).Hash
    $installed = if (Test-Path -LiteralPath $stampFile) { (Get-Content -LiteralPath $stampFile -Raw).Trim() } else { '' }
    $null = & $python -m server.launcher check-deps
    if ($LASTEXITCODE -ne 0 -or $wanted -ne $installed) {
        Write-Host 'Installing the Python packages from requirements.txt...'
        & $python -m pip install --disable-pip-version-check -r $requirements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Installing the packages failed (pip exit code $LASTEXITCODE). Check the network connection, then run Start.bat again."
            exit 12
        }
        & $python -m server.launcher check-deps
        if ($LASTEXITCODE -ne 0) { exit 12 }
        Set-Content -LiteralPath $stampFile -Value $wanted -Encoding ascii -NoNewline
    }

    # --------------------------------------------------------- 3. Port, when given
    if ($PSBoundParameters.ContainsKey('Port')) {
        $code = Invoke-Launcher set-port $Port
        if ($code -ne 0) { exit $code }
    }

    # --------------------------------------------------------- 4. Already running? Then no administrator prompt is needed.
    $statusLines = @(& $python -m server.launcher status --json)
    $code = $LASTEXITCODE
    $status = $null
    if ($code -in 0, 1 -and $statusLines.Count) {
        try { $status = $statusLines[-1] | ConvertFrom-Json -ErrorAction Stop } catch { $status = $null }
    }
    if (-not $status) {
        $statusLines | ForEach-Object { Write-Host $_ }
        exit $(if ($code -in 0, 1) { 1 } else { $code })
    }
    if ($status.running) {
        Write-Host "Game Companion Local is already running at $($status.url)"
        Open-Dashboard $status.url
        exit 0
    }

    # --------------------------------------------------------- 5. Start the backend, as administrator unless told otherwise
    if ($status.starting -or $NonElevated -or -not $IsWindows -or (Test-Admin)) {
        $code = Invoke-Launcher start --no-browser --timeout $Timeout
    } else {
        $code = Start-Elevated $status.data
    }
    if ($code -eq 0) { Open-Dashboard $script:readyUrl }
    exit $code
} finally {
    Pop-Location
}
