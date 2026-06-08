#!/usr/bin/env bash
# One-time GCP infrastructure setup for OrchestraOS Loop Sentinel.
#
# Usage:
#   export GCP_PROJECT=your-project-id
#   export GCP_REGION=us-central1
#   bash scripts/setup_gcp.sh
#
# Prerequisites: gcloud CLI authenticated, billing enabled.

set -euo pipefail

PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-us-central1}"
REPO="${ARTIFACT_REPO:-orchestraos}"
SA="${RUNTIME_SA:-orchestra-runtime}"
CONNECTOR="orchestraos-connector"
REDIS_INSTANCE="orchestraos-redis"

if [[ -z "${PROJECT}" || "${PROJECT}" == "(unset)" ]]; then
  echo "Set GCP_PROJECT or run: gcloud config set project YOUR_PROJECT"
  exit 1
fi

echo "==> Project: ${PROJECT}  Region: ${REGION}"

gcloud config set project "${PROJECT}"

echo "==> Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  pubsub.googleapis.com \
  secretmanager.googleapis.com \
  redis.googleapis.com \
  vpcaccess.googleapis.com \
  cloudbuild.googleapis.com \
  logging.googleapis.com

echo "==> Artifact Registry..."
if ! gcloud artifacts repositories describe "${REPO}" --location="${REGION}" &>/dev/null; then
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="OrchestraOS container images"
fi

echo "==> Service account..."
if ! gcloud iam service-accounts describe "${SA}@${PROJECT}.iam.gserviceaccount.com" &>/dev/null; then
  gcloud iam service-accounts create "${SA}" \
    --display-name="OrchestraOS Cloud Run runtime"
fi

SA_EMAIL="${SA}@${PROJECT}.iam.gserviceaccount.com"
for role in \
  roles/pubsub.publisher \
  roles/pubsub.subscriber \
  roles/secretmanager.secretAccessor \
  roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "${PROJECT}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${role}" \
    --quiet >/dev/null
done

echo "==> Pub/Sub topics and subscriptions..."
TOPICS=(raw-spans feature-vectors risk-assessments breaker-events remediation-plans)
for topic in "${TOPICS[@]}"; do
  gcloud pubsub topics create "${topic}" --quiet 2>/dev/null || true
done

create_sub() {
  local sub="$1" topic="$2"
  gcloud pubsub subscriptions create "${sub}" --topic="${topic}" --quiet 2>/dev/null || true
}
create_sub raw-spans-sub raw-spans
create_sub feature-vectors-sub feature-vectors
create_sub risk-assessments-sub risk-assessments
create_sub breaker-events-sub breaker-events
create_sub remediation-plans-sub remediation-plans
create_sub partners-breaker-sub breaker-events
create_sub partners-remediation-sub remediation-plans

echo "==> Secret Manager placeholders..."
SECRETS=(redis-url gemini-api-key mongodb-uri phoenix-endpoint arize-api-key elastic-url elastic-api-key dynatrace-url dynatrace-token gitlab-token gitlab-project-id)
for secret in "${SECRETS[@]}"; do
  if ! gcloud secrets describe "${secret}" &>/dev/null; then
    echo -n "placeholder" | gcloud secrets create "${secret}" --data-file=- --quiet
    echo "  created ${secret} (update with real value before deploy)"
  fi
done

echo "==> VPC connector (for Memorystore)..."
if ! gcloud compute networks vpc-access connectors describe "${CONNECTOR}" --region="${REGION}" &>/dev/null; then
  gcloud compute networks vpc-access connectors create "${CONNECTOR}" \
    --region="${REGION}" \
    --range=10.8.0.0/28 \
    --quiet
fi

if [[ "${SKIP_MEMORYSTORE:-}" != "1" ]]; then
  echo "==> Memorystore Redis (may take 10-20 minutes)..."
  if ! gcloud redis instances describe "${REDIS_INSTANCE}" --region="${REGION}" &>/dev/null; then
    gcloud redis instances create "${REDIS_INSTANCE}" \
      --size=1 \
      --region="${REGION}" \
      --network=default \
      --redis-version=redis_7_0 \
      --tier=BASIC
  fi
  REDIS_HOST="$(gcloud redis instances describe "${REDIS_INSTANCE}" --region="${REGION}" --format='value(host)')"
  echo -n "redis://${REDIS_HOST}:6379/0" | gcloud secrets versions add redis-url --data-file=-
  echo "  redis-url secret updated -> Memorystore ${REDIS_HOST}"
else
  echo "==> Skipping Memorystore (SKIP_MEMORYSTORE=1). Set redis-url secret manually."
fi

echo ""
echo "Setup complete. Next steps:"
echo "  1. Update secrets:  bash scripts/provision_secrets.sh"
echo "  2. Build images:      gcloud builds submit --config=cloudbuild.yaml"
echo "  3. Deploy services:   bash scripts/deploy_cloud_run.sh"
