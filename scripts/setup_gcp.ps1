# One-time GCP infrastructure setup for OrchestraOS (PowerShell).
#
# Usage:
#   $env:GCP_PROJECT = "your-project-id"
#   $env:GCP_REGION = "us-central1"
#   .\scripts\setup_gcp.ps1

$ErrorActionPreference = "Continue"

$Project = if ($env:GCP_PROJECT) { $env:GCP_PROJECT } else { (gcloud config get-value project 2>$null) }
$Region = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$Repo = if ($env:ARTIFACT_REPO) { $env:ARTIFACT_REPO } else { "orchestraos" }
$Sa = if ($env:RUNTIME_SA) { $env:RUNTIME_SA } else { "orchestra-runtime" }
$Connector = "orchestraos-connector"
$RedisInstance = "orchestraos-redis"

if (-not $Project -or $Project -eq "(unset)") {
    Write-Error "Set GCP_PROJECT or run: gcloud config set project YOUR_PROJECT"
}

Write-Host "==> Project: $Project  Region: $Region"
gcloud config set project $Project | Out-Null

Write-Host "==> Enabling APIs..."
gcloud services enable `
    run.googleapis.com `
    artifactregistry.googleapis.com `
    pubsub.googleapis.com `
    secretmanager.googleapis.com `
    redis.googleapis.com `
    vpcaccess.googleapis.com `
    cloudbuild.googleapis.com `
    logging.googleapis.com `
    --project=$Project --quiet

Write-Host "==> Artifact Registry..."
gcloud artifacts repositories describe $Repo --location=$Region --project=$Project 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    gcloud artifacts repositories create $Repo `
        --repository-format=docker `
        --location=$Region `
        --description="OrchestraOS container images" `
        --project=$Project --quiet
}

Write-Host "==> Service account..."
$saEmail = "${Sa}@${Project}.iam.gserviceaccount.com"
gcloud iam service-accounts describe $saEmail --project=$Project 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    gcloud iam service-accounts create $Sa `
        --display-name="OrchestraOS Cloud Run runtime" `
        --project=$Project --quiet
}

foreach ($role in @(
        "roles/pubsub.publisher",
        "roles/pubsub.subscriber",
        "roles/secretmanager.secretAccessor",
        "roles/logging.logWriter"
    )) {
    gcloud projects add-iam-policy-binding $Project `
        --member="serviceAccount:$saEmail" `
        --role=$role `
        --quiet | Out-Null
}

Write-Host "==> Pub/Sub topics and subscriptions..."
$topics = @("raw-spans", "feature-vectors", "risk-assessments", "breaker-events", "remediation-plans")
foreach ($topic in $topics) {
    gcloud pubsub topics create $topic --project=$Project --quiet 2>$null
}

function New-Sub($Sub, $Topic) {
    gcloud pubsub subscriptions create $Sub --topic=$Topic --project=$Project --quiet 2>$null
}
New-Sub "raw-spans-sub" "raw-spans"
New-Sub "feature-vectors-sub" "feature-vectors"
New-Sub "risk-assessments-sub" "risk-assessments"
New-Sub "breaker-events-sub" "breaker-events"
New-Sub "remediation-plans-sub" "remediation-plans"
New-Sub "partners-breaker-sub" "breaker-events"
New-Sub "partners-remediation-sub" "remediation-plans"

Write-Host "==> Secret Manager placeholders..."
$secrets = @(
    "redis-url", "gemini-api-key", "mongodb-uri", "phoenix-endpoint", "arize-api-key",
    "elastic-url", "elastic-api-key", "dynatrace-url", "dynatrace-token",
    "gitlab-token", "gitlab-project-id"
)
foreach ($secret in $secrets) {
    gcloud secrets describe $secret --project=$Project 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        "placeholder" | gcloud secrets create $secret --data-file=- --project=$Project --quiet
        Write-Host "  created $secret (update before production deploy)"
    }
}

Write-Host "==> VPC connector..."
gcloud compute networks vpc-access connectors describe $Connector --region=$Region --project=$Project 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    gcloud compute networks vpc-access connectors create $Connector `
        --region=$Region `
        --range=10.8.0.0/28 `
        --project=$Project --quiet
}

if ($env:SKIP_MEMORYSTORE -ne "1") {
    Write-Host "==> Memorystore Redis (may take 10-20 minutes)..."
    gcloud redis instances describe $RedisInstance --region=$Region --project=$Project 2>$null
    if ($LASTEXITCODE -ne 0) {
        gcloud redis instances create $RedisInstance `
            --size=1 `
            --region=$Region `
            --network=default `
            --redis-version=redis_7_0 `
            --tier=BASIC `
            --project=$Project --quiet
    }
    $redisHost = gcloud redis instances describe $RedisInstance --region=$Region --project=$Project --format="value(host)"
    "redis://${redisHost}:6379/0" | gcloud secrets versions add redis-url --data-file=- --project=$Project
    Write-Host "  redis-url secret updated -> Memorystore $redisHost"
} else {
    Write-Host "==> Skipping Memorystore (SKIP_MEMORYSTORE=1). Set redis-url secret manually."
}

Write-Host ""
Write-Host "Setup complete. Next:"
Write-Host "  gcloud builds submit --config=cloudbuild.yaml"
Write-Host "  .\scripts\deploy_cloud_run.ps1"
