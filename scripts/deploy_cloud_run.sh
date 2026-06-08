#!/usr/bin/env bash
# Deploy all OrchestraOS services to Cloud Run.
#
# Usage:
#   export GCP_PROJECT=your-project-id
#   export GCP_REGION=us-central1
#   export IMAGE_TAG=latest          # or SHORT_SHA from Cloud Build
#   bash scripts/deploy_cloud_run.sh
#
# DoD: prints public dashboard + collector URLs when complete.

set -euo pipefail

PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
REPO="${ARTIFACT_REPO:-orchestraos}"
TAG="${IMAGE_TAG:-latest}"
SA="${RUNTIME_SA:-orchestra-runtime}"
CONNECTOR="orchestraos-connector"
SA_EMAIL="${SA}@${PROJECT}.iam.gserviceaccount.com"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT}/${REPO}"

COMMON_ENV="GOOGLE_CLOUD_PROJECT=${PROJECT},GEMINI_MODEL=gemini-2.0-flash,BREAKER_RISK_THRESHOLD=0.8,BREAKER_COOLDOWN_SEC=30"
COMMON_SECRETS="REDIS_URL=redis-url:latest,GEMINI_API_KEY=gemini-api-key:latest"
WORKER_FLAGS=(
  --platform=managed
  --region="${REGION}"
  --service-account="${SA_EMAIL}"
  --vpc-connector="${CONNECTOR}"
  --min-instances=1
  --max-instances=3
  --cpu=1
  --memory=512Mi
  --no-cpu-throttling
  --ingress=internal
  --no-allow-unauthenticated
  --set-env-vars="${COMMON_ENV}"
  --set-secrets="${COMMON_SECRETS}"
  --quiet
)

gcloud config set project "${PROJECT}"

echo "==> Deploying workers (internal ingress)..."

gcloud run deploy orchestraos-detectors \
  "${WORKER_FLAGS[@]}" \
  --image="${REGISTRY}/detectors:${TAG}" \
  --command=python \
  --args=-m,detectors.main

gcloud run deploy orchestraos-monitor \
  "${WORKER_FLAGS[@]}" \
  --image="${REGISTRY}/monitor:${TAG}" \
  --command=python \
  --args=-m,monitor_model.main

gcloud run deploy orchestraos-breaker \
  "${WORKER_FLAGS[@]}" \
  --image="${REGISTRY}/breaker:${TAG}" \
  --command=python \
  --args=-m,breaker.main

gcloud run deploy orchestraos-remediation \
  "${WORKER_FLAGS[@]}" \
  --image="${REGISTRY}/remediation:${TAG}" \
  --command=python \
  --args=-m,remediation.main

PARTNER_SECRETS="${COMMON_SECRETS},MONGODB_URI=mongodb-uri:latest"
gcloud run deploy orchestraos-partners \
  "${WORKER_FLAGS[@]}" \
  --image="${REGISTRY}/partners:${TAG}" \
  --set-secrets="${PARTNER_SECRETS}" \
  --set-env-vars="${COMMON_ENV},PARTNER_MONGODB_ENABLED=true" \
  --command=python \
  --args=-m,integrations.main

echo "==> Deploying public HTTP services..."

gcloud run deploy orchestraos-collector \
  --platform=managed \
  --region="${REGION}" \
  --service-account="${SA_EMAIL}" \
  --vpc-connector="${CONNECTOR}" \
  --min-instances=1 \
  --max-instances=5 \
  --cpu=1 \
  --memory=512Mi \
  --port=8080 \
  --allow-unauthenticated \
  --set-env-vars="${COMMON_ENV},OTEL_SERVICE_NAME=orchestraos-collector,PARTNER_ARIZE_ENABLED=true" \
  --set-secrets="${COMMON_SECRETS},PHOENIX_COLLECTOR_ENDPOINT=phoenix-endpoint:latest" \
  --image="${REGISTRY}/collector:${TAG}" \
  --command=python \
  --args=-m,collector.main \
  --quiet

COLLECTOR_URL="$(gcloud run services describe orchestraos-collector --region="${REGION}" --format='value(status.url)')"

gcloud run deploy orchestraos-dashboard \
  --platform=managed \
  --region="${REGION}" \
  --service-account="${SA_EMAIL}" \
  --min-instances=1 \
  --max-instances=3 \
  --cpu=1 \
  --memory=1Gi \
  --port=8080 \
  --allow-unauthenticated \
  --set-env-vars="${COMMON_ENV}" \
  --image="${REGISTRY}/dashboard:${TAG}" \
  --command=python \
  --args=-m,dashboard.server \
  --quiet

DASHBOARD_URL="$(gcloud run services describe orchestraos-dashboard --region="${REGION}" --format='value(status.url)')"

echo ""
echo "========================================================"
echo "  OrchestraOS deployed"
echo "  Dashboard (public):  ${DASHBOARD_URL}"
echo "  Collector (public):  ${COLLECTOR_URL}"
echo "  OTLP ingest:         ${COLLECTOR_URL}/v1/traces"
echo "  Health:              ${COLLECTOR_URL}/health"
echo "========================================================"
