# Inject OPENAI_* from local .env into Live API via SSM Parameter Store + EC2 recreate.
# Does not print secret values. Requires AWS CLI + SSM access to i-0b0576945d080cb3f.
# Usage (repo root):  .\scripts\inject-live-openai.ps1

$ErrorActionPreference = "Stop"
$Region = "ap-southeast-1"
$InstanceId = "i-0b0576945d080cb3f"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$EnvFile = Join-Path $Root ".env"
$SsmDoc = Join-Path $Root "deploy\aws\ssm-inject-openai.json"

if (-not (Test-Path $EnvFile)) { throw ".env not found at $EnvFile" }
if (-not (Test-Path $SsmDoc)) { throw "SSM script missing: $SsmDoc" }

function Get-DotEnvValue([string]$name) {
  $line = Get-Content $EnvFile | Where-Object { $_ -match ("^\s*" + [regex]::Escape($name) + "\s*=") } | Select-Object -First 1
  if (-not $line) { return "" }
  return (($line -split "=", 2)[1].Trim().Trim('"').Trim("'"))
}

$key = Get-DotEnvValue "OPENAI_API_KEY"
$model = Get-DotEnvValue "OPENAI_MODEL"
$base = Get-DotEnvValue "OPENAI_BASE_URL"
if ([string]::IsNullOrWhiteSpace($base)) { $base = "https://api.openai.com" }
if ([string]::IsNullOrWhiteSpace($model)) { $model = "gpt-5.4-nano" }
if ([string]::IsNullOrWhiteSpace($key)) { throw "OPENAI_API_KEY is empty in .env" }

Write-Host "Putting SecureString params (values not printed)..."
aws ssm put-parameter --region $Region --name "/silent-shield/live/OPENAI_API_KEY" --type SecureString --value $key --overwrite | Out-Null
aws ssm put-parameter --region $Region --name "/silent-shield/live/OPENAI_MODEL" --type SecureString --value $model --overwrite | Out-Null
aws ssm put-parameter --region $Region --name "/silent-shield/live/OPENAI_BASE_URL" --type SecureString --value $base --overwrite | Out-Null
Write-Host "SSM params OK. Model=$model Base=$base KeyLen=$($key.Length)"

$paramsUri = "file://" + ($SsmDoc -replace "\\", "/")
Write-Host "Sending SSM RunShellScript to $InstanceId ..."
$cmdId = aws ssm send-command --region $Region --instance-ids $InstanceId --document-name "AWS-RunShellScript" --comment "inject OPENAI into silent-shield-api" --parameters $paramsUri --query "Command.CommandId" --output text
if (-not $cmdId) { throw "send-command failed" }
Write-Host "CommandId=$cmdId - waiting for Success..."

do {
  Start-Sleep -Seconds 5
  $inv = aws ssm get-command-invocation --region $Region --command-id $cmdId --instance-id $InstanceId --output json | ConvertFrom-Json
  Write-Host "Status=$($inv.Status)"
} while ($inv.Status -in @("Pending", "InProgress", "Delayed"))

Write-Host "---- stdout (tail) ----"
if ($inv.StandardOutputContent) { $inv.StandardOutputContent.Trim() }
if ($inv.StandardErrorContent) {
  Write-Host "---- stderr ----"
  $inv.StandardErrorContent.Trim()
}
if ($inv.Status -ne "Success") { throw "SSM command ended with $($inv.Status)" }

Write-Host "Done. Next smoke: https://abg-team.vercel.app POST /agent/turns"
