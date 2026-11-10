$ErrorActionPreference = "Stop"
$projectRoot = Split-Path $PSScriptRoot -Parent
$logDirectory = Join-Path $env:TEMP (
    "VirtualECULab-" + [guid]::NewGuid().ToString("N")
)

New-Item -ItemType Directory -Path $logDirectory | Out-Null

function Test-Ready {
    param([string]$Url)

    try {
        $response = Invoke-WebRequest `
            -Uri $Url `
            -UseBasicParsing `
            -TimeoutSec 2

        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

$servers = @(
    @{
        Name = "Backend"
        Url = "http://127.0.0.1:8000/health"
        Port = 8000
        Directory = $projectRoot
        Executable = Join-Path $projectRoot ".venv\Scripts\python.exe"
        Arguments = @(
            "-m", "uvicorn", "backend.main:app",
            "--host", "127.0.0.1", "--port", "8000", "--reload"
        )
    },
    @{
        Name = "Frontend"
        Url = "http://localhost:5173/"
        Port = 5173
        Directory = Join-Path $projectRoot "frontend"
        Executable = $env:ComSpec
        Arguments = @(
            "/d", "/c",
            "npm.cmd run dev -- --host localhost --port 5173 --strictPort"
        )
    }
)

foreach ($server in $servers) {
    if (Test-Ready $server.Url) {
        Write-Host "[PASS] $($server.Name) already ready: $($server.Url)" `
            -ForegroundColor Green
        continue
    }

    $listener = Get-NetTCPConnection `
        -LocalPort $server.Port `
        -State Listen `
        -ErrorAction SilentlyContinue

    if ($listener) {
        throw "$($server.Name): port $($server.Port) is occupied, but its URL is unhealthy. No process was stopped."
    }

    $server.OutputLog = Join-Path $logDirectory "$($server.Name).out.log"
    $server.ErrorLog = Join-Path $logDirectory "$($server.Name).err.log"

    Write-Host "[START] $($server.Name)..." -ForegroundColor Cyan

    Start-Process `
        -FilePath $server.Executable `
        -ArgumentList $server.Arguments `
        -WorkingDirectory $server.Directory `
        -WindowStyle Hidden `
        -RedirectStandardOutput $server.OutputLog `
        -RedirectStandardError $server.ErrorLog | Out-Null
}

$deadline = (Get-Date).AddSeconds(60)

do {
    $pending = @(
        $servers | Where-Object { -not (Test-Ready $_.Url) }
    )

    if ($pending.Count -eq 0) {
        break
    }

    Start-Sleep -Milliseconds 500
} while ((Get-Date) -lt $deadline)

foreach ($server in $servers) {
    if (Test-Ready $server.Url) {
        Write-Host "[PASS] $($server.Name) ready: $($server.Url)" `
            -ForegroundColor Green
    }
    else {
        Write-Host "[FAIL] $($server.Name) did not become ready." `
            -ForegroundColor Red

        if ($server.ErrorLog) {
            Write-Host "Error log: $($server.ErrorLog)"
        }

        if ($server.OutputLog) {
            Write-Host "Output log: $($server.OutputLog)"
        }
    }
}

Write-Host ""
Write-Host "Server readiness check finished. This does not run tests."
Write-Host "Servers remain running after you close this window."
Write-Host "Startup logs: $logDirectory"