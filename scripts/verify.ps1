# Unified verify for Silent Shield (backend + frontend)
# Usage:
#   .\scripts\verify.ps1           # full verify
#   .\scripts\verify.ps1 -Quick    # lint only
#   .\scripts\verify.ps1 -System   # full verify + Playwright system test
#   .\scripts\verify.ps1 -Release  # full verify + system test + online release gate

param(
    [switch]$Quick,
    [switch]$System,
    [switch]$Release
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if ($Quick -and ($System -or $Release)) {
    throw "-Quick không thể dùng cùng -System hoặc -Release"
}

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
    Write-Host "`n==> Agent rules wiring" -ForegroundColor Cyan
    if (-not (Test-Path -LiteralPath "RULES.md")) {
        throw "RULES.md is missing"
    }
    if (-not (Test-Path -LiteralPath "AGENTS.md")) {
        throw "AGENTS.md is missing"
    }
    if ((Get-Content -Raw -Encoding UTF8 -LiteralPath "RULES.md") -notmatch "AGENTS\.md") {
        throw "RULES.md does not reference AGENTS.md"
    }
    if ((Get-Content -Raw -Encoding UTF8 -LiteralPath "AGENTS.md") -notmatch "RULES\.md") {
        throw "AGENTS.md does not reference RULES.md"
    }
    $AgentEntrypoints = @(
        "CLAUDE.md",
        ".cursor/rules/project.mdc",
        ".github/copilot-instructions.md"
    )
    foreach ($EntryPoint in $AgentEntrypoints) {
        if (-not (Test-Path -LiteralPath $EntryPoint)) {
            throw "Agent entrypoint missing: $EntryPoint"
        }
        if ((Get-Content -Raw -Encoding UTF8 -LiteralPath $EntryPoint) -notmatch "AGENTS\.md") {
            throw "Agent entrypoint does not reference AGENTS.md: $EntryPoint"
        }
    }

    if (-not (Get-Command ruff -ErrorAction SilentlyContinue)) {
        throw "ruff not found; install backend dev dependencies before verify"
    }
    Invoke-Step "Backend lint (ruff)" {
        Push-Location backend
        try { ruff check app tests } finally { Pop-Location }
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
            if ((Get-Content -Raw -Encoding UTF8 "frontend/package.json") -match "No frontend tests yet") {
                Write-Warning "Frontend tests are a placeholder; this is not behavioral test evidence"
            }
            Invoke-Step "Frontend production build" {
                npm run build --prefix frontend
            }
            if ($System -or $Release) {
                Invoke-Step "Cross-system Playwright tests" {
                    & .\tests\system\run.ps1
                }
            }
            if ($Release) {
                Invoke-Step "Online release gate" {
                    & .\tests\system\release\run.ps1 `
                        -BaseUrl $env:RELEASE_BASE_URL `
                        -ApiBaseUrl $env:RELEASE_API_BASE_URL `
                        -RepositoryUrl $env:RELEASE_REPOSITORY_URL
                }
            }
        }
    } else {
        Write-Warning "frontend/package.json missing; skip frontend verify (scaffold Next.js in G01)"
    }

    Write-Host "`nAll verify steps passed." -ForegroundColor Green
} finally {
    Pop-Location
}
