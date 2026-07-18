param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,
    [Parameter(Mandatory = $true)]
    [string]$ApiBaseUrl,
    [Parameter(Mandatory = $true)]
    [string]$RepositoryUrl,
    [switch]$AllowUnavailableAi
)

$ErrorActionPreference = "Stop"
$ReleaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SystemDir = Split-Path -Parent $ReleaseDir

foreach ($entry in @{
    RELEASE_BASE_URL = $BaseUrl
    RELEASE_API_BASE_URL = $ApiBaseUrl
    RELEASE_REPOSITORY_URL = $RepositoryUrl
}.GetEnumerator()) {
    if ([string]::IsNullOrWhiteSpace($entry.Value)) {
        throw "$($entry.Key) không được để trống."
    }
    [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value.Trim(), "Process")
}
$env:RELEASE_REQUIRE_LIVE_AI_OK = if ($AllowUnavailableAi) { "0" } else { "1" }

Push-Location $SystemDir
try {
    npm run test:release
    if ($LASTEXITCODE -ne 0) { throw "Release smoke test thất bại." }
} finally {
    Pop-Location
}
