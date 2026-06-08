#!/usr/bin/env bash
# Idempotent OrchestraOS deploy service account bootstrap (Cloud Shell).
# JSON key creation is intentionally omitted — org policy blocks SA keys.
#
# Usage:
#   gcloud config set project orchestraos-498316
#   bash scripts/bootstrap_sa.sh

set -euo pipefail

PROJECT_ID="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
SA_NAME="${SA_NAME:-orchestraos-sa}"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "Set GCP project: gcloud config set project orchestraos-498316"
  exit 1
fi

echo "==> Project: ${PROJECT_ID}"
echo "==> Service account: ${SA_EMAIL}"

gcloud iam service-accounts create "${SA_NAME}" \
  --display-name="OrchestraOS Service Account" \
  --project="${PROJECT_ID}" 2>/dev/null || echo "SA already exists (ok)"

for ROLE in \
  roles/aiplatform.user \
  roles/pubsub.editor \
  roles/secretmanager.secretAccessor \
  roles/run.developer \
  roles/artifactregistry.writer \
  roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --quiet
done

echo "==> Done: ${SA_EMAIL}"
echo "==> Use gcloud ADC / Cloud Run SA — do not create JSON keys (org policy blocks them)"
