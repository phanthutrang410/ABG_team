# Unified verify for Silent Shield (backend + frontend)
# Usage:
#   .\scripts\verify.ps1           # full verify
#   .\scripts\verify.ps1 -Quick    # lint only

param(
    [switch]$Quick
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Invoke-Step {
    param([string]$Name, [scriptblock]$Action)
    Write-Host "`n==> $Name" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0 -and $null -ne $LASTEXITCODE) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

Push-Location $Root
try {
    if (Get-Command ruff -ErrorAction SilentlyContinue) {
        Invoke-Step "Backend lint (ruff)" {
            Push-Location backend
            try { ruff check app tests } finally { Pop-Location }
        }
    } else {
        Write-Warning "ruff not found; skip backend lint"
    }

    if (-not $Quick) {
        Invoke-Step "Backend tests (pytest)" {
            Push-Location backend
            try {
                if (Get-Command pytest -ErrorAction SilentlyContinue) {
                    pytest -q -m "not slow and not eval"
                } else {
                    python -m pytest -q -m "not slow and not eval"
                }
            } finally { Pop-Location }
        }
    }

    if (Test-Path "frontend/package.json") {
        Invoke-Step "Frontend lint" {
            npm run lint --prefix frontend
        }
        if (-not $Quick) {
            Invoke-Step "Frontend tests" {
                npm test --prefix frontend
            }
        }
    } else {
        Write-Warning "frontend/package.json missing; skip frontend verify (scaffold Next.js in G01)"
    }

    Write-Host "`nAll verify steps passed." -ForegroundColor Green
} finally {
    Pop-Location
}
