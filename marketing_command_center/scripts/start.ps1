param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 4175,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$url = "http://127.0.0.1:$Port/"
$healthUrl = "http://127.0.0.1:$Port/api/health"

function Test-MarketingServer {
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
        return $health.status -eq 'ok' -and $health.service -eq 'marketing-command-center'
    }
    catch {
        return $false
    }
}

function Open-MarketingBrowser {
    if (-not $NoBrowser) {
        Start-Process $url
    }
}

function Get-RunningCodeVersion {
    try { return [int64](Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2).code_version } catch { return $null }
}

# A server started before serve.py last changed runs old code; restart it instead of reusing it.
if (Test-MarketingServer) {
    $currentVersion = [int64][DateTimeOffset]::new((Get-Item (Join-Path $projectRoot 'serve.py')).LastWriteTimeUtc).ToUnixTimeSeconds()
    if ((Get-RunningCodeVersion) -ne $currentVersion) {
        $stale = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        Write-Host "Restarting server that runs outdated code (pid $($stale.OwningProcess))."
        Stop-Process -Id $stale.OwningProcess -Force -ErrorAction Stop
        Wait-Process -Id $stale.OwningProcess -Timeout 5 -ErrorAction SilentlyContinue
    }
}

if (Test-MarketingServer) {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    Write-Host "Hermes Marketing Studio is already running: $url"
    Write-Output "READY url=$url pid=$($listener.OwningProcess) existing=true"
    Open-MarketingBrowser
    return
}

$occupied = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($occupied) {
    throw "Port $Port is already used by another program."
}

$python = Get-Command python -ErrorAction Stop
$keyLoader = 'C:\Users\cs930\Desktop\ai_agent\keyinfo\load-keys.ps1'
if (Test-Path -LiteralPath $keyLoader) {
    . $keyLoader
}

$logDirectory = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$stdoutLog = Join-Path $logDirectory 'server.out.log'
$stderrLog = Join-Path $logDirectory 'server.err.log'
$process = Start-Process -FilePath $python.Source `
    -ArgumentList @('serve.py', '--host', '127.0.0.1', '--port', [string]$Port) `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru

$deadline = (Get-Date).AddSeconds(20)
do {
    Start-Sleep -Milliseconds 400
    if ($process.HasExited) {
        throw "Server exited during startup. Check logs\server.err.log."
    }
    if (Test-MarketingServer) {
        Write-Host "Hermes Marketing Studio started: $url"
        Write-Output "READY url=$url pid=$($process.Id) existing=false"
        Open-MarketingBrowser
        return
    }
} while ((Get-Date) -lt $deadline)

Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
throw "Server health check timed out. Check logs\server.err.log."
