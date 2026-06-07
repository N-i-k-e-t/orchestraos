# Update Secret Manager values from environment (PowerShell).
# Usage:
#   $env:GEMINI_API_KEY = "..."
#   $env:REDIS_URL = "redis://..."
#   .\scripts\provision_secrets.ps1

$ErrorActionPreference = "Continue"
$Project = if ($env:GCP_PROJECT) { $env:GCP_PROJECT } else { (gcloud config get-value project 2>$null) }
gcloud config set project $Project | Out-Null

function Set-Secret($Name, $Value) {
    if ($Value) {
        $Value | gcloud secrets versions add $Name --data-file=- --project=$Project
        Write-Host "  updated $Name"
    }
}

Set-Secret "redis-url" $env:REDIS_URL
Set-Secret "gemini-api-key" $env:GEMINI_API_KEY
Set-Secret "mongodb-uri" $env:MONGODB_URI
Set-Secret "phoenix-endpoint" $env:PHOENIX_COLLECTOR_ENDPOINT
Set-Secret "elastic-url" $env:ELASTIC_URL
Set-Secret "elastic-api-key" $env:ELASTIC_API_KEY
Set-Secret "dynatrace-url" $env:DYNATRACE_URL
Set-Secret "dynatrace-token" $env:DYNATRACE_API_TOKEN
Set-Secret "gitlab-token" $env:GITLAB_TOKEN
Set-Secret "gitlab-project-id" $env:GITLAB_PROJECT_ID

Write-Host "Secrets updated for project $Project"
