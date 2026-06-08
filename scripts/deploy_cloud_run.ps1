# Deploy OrchestraOS services to Cloud Run (PowerShell).
#
# Usage:
#   $env:GCP_PROJECT = "your-project-id"
#   $env:IMAGE_TAG = "latest"
#   .\scripts\deploy_cloud_run.ps1

$ErrorActionPreference = "Continue"

$Project = if ($env:GCP_PROJECT) { $env:GCP_PROJECT } else { (gcloud config get-value project 2>$null) }
$Region = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$Repo = if ($env:ARTIFACT_REPO) { $env:ARTIFACT_REPO } else { "orchestraos" }
$Tag = if ($env:IMAGE_TAG) { $env:IMAGE_TAG } else { "latest" }
$Sa = if ($env:RUNTIME_SA) { $env:RUNTIME_SA } else { "orchestra-runtime" }
$Connector = "orchestraos-connector"
$SaEmail = "${Sa}@${Project}.iam.gserviceaccount.com"
$Registry = "${Region}-docker.pkg.dev/${Project}/${Repo}"

$CommonEnv = "GOOGLE_CLOUD_PROJECT=${Project},GEMINI_MODEL=gemini-2.0-flash,BREAKER_RISK_THRESHOLD=0.8,BREAKER_COOLDOWN_SEC=30"
$CommonSecrets = "REDIS_URL=redis-url:latest,GEMINI_API_KEY=gemini-api-key:latest"

gcloud config set project $Project | Out-Null

function Deploy-Worker($Name, $Image, $Module) {
    Write-Host "==> Deploying $Name..."
    gcloud run deploy $Name `
        --platform=managed `
        --region=$Region `
        --service-account=$SaEmail `
        --vpc-connector=$Connector `
        --min-instances=1 `
        --max-instances=3 `
        --cpu=1 `
        --memory=512Mi `
        --no-cpu-throttling `
        --ingress=internal `
        --no-allow-unauthenticated `
        --set-env-vars=$CommonEnv `
        --set-secrets=$CommonSecrets `
        --image="${Registry}/${Image}:${Tag}" `
        --command=python `
        --args="-m,$Module" `
        --project=$Project `
        --quiet
}

Write-Host "==> Deploying workers (internal ingress)..."
Deploy-Worker "orchestraos-detectors" "detectors" "detectors.main"
Deploy-Worker "orchestraos-monitor" "monitor" "monitor_model.main"
Deploy-Worker "orchestraos-breaker" "breaker" "breaker.main"
Deploy-Worker "orchestraos-remediation" "remediation" "remediation.main"

$PartnerSecrets = "${CommonSecrets},MONGODB_URI=mongodb-uri:latest"
$PartnerEnv = "${CommonEnv},PARTNER_MONGODB_ENABLED=true"
Write-Host "==> Deploying orchestraos-partners..."
gcloud run deploy orchestraos-partners `
    --platform=managed `
    --region=$Region `
    --service-account=$SaEmail `
    --vpc-connector=$Connector `
    --min-instances=1 `
    --max-instances=3 `
    --cpu=1 `
    --memory=512Mi `
    --no-cpu-throttling `
    --ingress=internal `
    --no-allow-unauthenticated `
    --set-env-vars=$PartnerEnv `
    --set-secrets=$PartnerSecrets `
    --image="${Registry}/partners:${Tag}" `
    --command=python `
    --args="-m,integrations.main" `
    --project=$Project `
    --quiet

Write-Host "==> Deploying public HTTP services..."
gcloud run deploy orchestraos-collector `
    --platform=managed `
    --region=$Region `
    --service-account=$SaEmail `
    --vpc-connector=$Connector `
    --min-instances=1 `
    --max-instances=5 `
    --cpu=1 `
    --memory=512Mi `
    --port=8080 `
    --allow-unauthenticated `
    --set-env-vars="${CommonEnv},OTEL_SERVICE_NAME=orchestraos-collector,PARTNER_ARIZE_ENABLED=true" `
    --set-secrets="${CommonSecrets},PHOENIX_COLLECTOR_ENDPOINT=phoenix-endpoint:latest" `
    --image="${Registry}/collector:${Tag}" `
    --command=python `
    --args="-m,collector.main" `
    --project=$Project `
    --quiet

$CollectorUrl = gcloud run services describe orchestraos-collector --region=$Region --project=$Project --format="value(status.url)"

gcloud run deploy orchestraos-dashboard `
    --platform=managed `
    --region=$Region `
    --service-account=$SaEmail `
    --min-instances=1 `
    --max-instances=3 `
    --cpu=1 `
    --memory=1Gi `
    --port=8080 `
    --allow-unauthenticated `
    --set-env-vars=$CommonEnv `
    --image="${Registry}/dashboard:${Tag}" `
    --command=python `
    --args="-m,dashboard.server" `
    --project=$Project `
    --quiet

$DashboardUrl = gcloud run services describe orchestraos-dashboard --region=$Region --project=$Project --format="value(status.url)"

Write-Host ""
Write-Host "========================================================"
Write-Host "  OrchestraOS deployed"
Write-Host "  Dashboard (public):  $DashboardUrl"
Write-Host "  Collector (public):  $CollectorUrl"
Write-Host "  OTLP ingest:         ${CollectorUrl}/v1/traces"
Write-Host "  Health:              ${CollectorUrl}/health"
Write-Host "========================================================"
