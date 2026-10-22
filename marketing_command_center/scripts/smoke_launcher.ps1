param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 4192
)

$ErrorActionPreference = 'Stop'
$startedPid = $null
$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($listener) {
    throw "Test port $Port is already occupied."
}

try {
    $output = & (Join-Path $PSScriptRoot 'start.ps1') -Port $Port -NoBrowser | Out-String
    if ($output -notmatch 'READY .* pid=(\d+) existing=false') {
        throw 'Launcher did not report a cold-start READY signal.'
    }
    $startedPid = [int]$Matches[1]
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 5
    if ($health.status -ne 'ok' -or $health.service -ne 'marketing-command-center') {
        throw 'Launcher health response was invalid.'
    }
    Write-Output 'PASS launcher: cold start, health, background process'
}
finally {
    if ($startedPid) {
        Stop-Process -Id $startedPid -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $startedPid -Timeout 5 -ErrorAction SilentlyContinue
    }
    $started = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($started) {
        Stop-Process -Id $started.OwningProcess -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $started.OwningProcess -Timeout 5 -ErrorAction SilentlyContinue
    }
}
