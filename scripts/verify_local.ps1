# Local submission verification (PowerShell).
# Usage: .\scripts\verify_local.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "==> OrchestraOS local verification"
Write-Host ""

Write-Host "[1/3] pytest..."
poetry run pytest tests/ -v --tb=short
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "[2/3] orchestraos-demo..."
poetry run orchestraos-demo
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "[3/3] dashboard build..."
Push-Location dashboard
npm run build
$buildOk = $LASTEXITCODE
Pop-Location
if ($buildOk -ne 0) { exit $buildOk }

Write-Host ""
Write-Host "All local checks passed."
