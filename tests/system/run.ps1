param(
    [int]$DatabasePort = 55433,
    [int]$BackendPort = 8100,
    [int]$FrontendPort = 3200
)

$ErrorActionPreference = "Stop"
$SystemDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent (Split-Path -Parent $SystemDir)
$ContainerName = "silentshield-system-test-db-$PID"
$ContainerStarted = $false
$BackendProcess = $null
$FrontendProcess = $null

function Resolve-TestPython {
    $candidates = @(
        $env:SYSTEM_TEST_PYTHON,
        (Join-Path $RepoRoot "backend/.venv/Scripts/python.exe"),
        (Join-Path $RepoRoot "backend/.venv312/Scripts/python.exe")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    foreach ($candidate in $candidates) {
        $previousPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = "Continue"
            & $candidate -c "import fastapi, psycopg, uvicorn" *> $null
            $candidateExitCode = $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $previousPreference
        }
        if ($candidateExitCode -eq 0) { return (Resolve-Path -LiteralPath $candidate).Path }
    }
    throw "Không tìm thấy Python environment hợp lệ. Hãy cài backend[dev] theo backend/tests/README.md."
}

$Python = Resolve-TestPython
$DatabaseUrl = "postgresql+psycopg://silentshield:silentshield@127.0.0.1:$DatabasePort/silentshield"

function Wait-HttpEndpoint {
    param([string]$Url, [string]$Name)
    for ($attempt = 1; $attempt -le 60; $attempt++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return }
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    throw "$Name không sẵn sàng tại $Url sau 60 giây."
}

try {
    docker run --rm -d --name $ContainerName `
        -e POSTGRES_USER=silentshield `
        -e POSTGRES_PASSWORD=silentshield `
        -e POSTGRES_DB=silentshield `
        -p "${DatabasePort}:5432" postgres:16 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Không thể khởi động PostgreSQL test tại cổng $DatabasePort." }
    $ContainerStarted = $true

    $ready = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        docker exec $ContainerName pg_isready -U silentshield -d silentshield *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw "PostgreSQL test không sẵn sàng sau 30 giây." }

    $env:DATABASE_URL = $DatabaseUrl
    $env:TEST_DATABASE_URL = $DatabaseUrl
    $env:SYSTEM_TEST_PYTHON = $Python
    $env:SYSTEM_TEST_BACKEND_PORT = [string]$BackendPort
    $env:SYSTEM_TEST_FRONTEND_PORT = [string]$FrontendPort
    $env:SYSTEM_TEST_EXTERNAL_SERVERS = "1"

    Push-Location (Join-Path $RepoRoot "backend")
    try {
        & $Python -m app.dwh.cli import-semester
        if ($LASTEXITCODE -ne 0) { throw "Import semester fixture thất bại." }
        & $Python -m app.dwh.cli import-attendance
        if ($LASTEXITCODE -ne 0) { throw "Import attendance fixture thất bại." }
    } finally {
        Pop-Location
    }

    $env:CORS_ORIGINS = "http://127.0.0.1:$FrontendPort"
    $BackendProcess = Start-Process -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--app-dir", (Join-Path $RepoRoot "backend"), "--host", "127.0.0.1", "--port", [string]$BackendPort) `
        -PassThru -WindowStyle Hidden

    $env:NEXT_PUBLIC_API_BASE = "http://127.0.0.1:$BackendPort"
    $env:NEXT_PUBLIC_ADVISOR_LOCAL_DEMO = "0"
    $NextCli = Join-Path $RepoRoot "frontend/node_modules/next/dist/bin/next"
    $Node = (Get-Command node -ErrorAction Stop).Source
    $FrontendProcess = Start-Process -FilePath $Node `
        -ArgumentList @($NextCli, "dev", (Join-Path $RepoRoot "frontend"), "--hostname", "127.0.0.1", "--port", [string]$FrontendPort) `
        -PassThru -WindowStyle Hidden

    Wait-HttpEndpoint -Url "http://127.0.0.1:$BackendPort/health" -Name "Backend"
    Wait-HttpEndpoint -Url "http://127.0.0.1:$FrontendPort/login" -Name "Frontend"

    Push-Location $SystemDir
    try {
        npm test
        if ($LASTEXITCODE -ne 0) { throw "System test thất bại." }
    } finally {
        Pop-Location
    }
} finally {
    foreach ($process in @($FrontendProcess, $BackendProcess)) {
        if ($null -ne $process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            $null = $process.WaitForExit(5000)
        }
    }
    if ($ContainerStarted) {
        docker rm -f $ContainerName | Out-Null
    }
}
