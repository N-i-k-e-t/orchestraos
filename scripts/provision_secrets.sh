#!/usr/bin/env bash
# Update Secret Manager values from environment or .env file.
#
# Usage:
#   export GEMINI_API_KEY=...
#   export REDIS_URL=redis://...
#   bash scripts/provision_secrets.sh
#
# Or load from .env:
#   set -a && source .env && set +a && bash scripts/provision_secrets.sh

set -euo pipefail

PROJECT="${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}"
gcloud config set project "${PROJECT}" 2>/dev/null || true

put_secret() {
  local name="$1" value="$2"
  if [[ -n "${value}" ]]; then
    echo -n "${value}" | gcloud secrets versions add "${name}" --data-file=-
    echo "  updated ${name}"
  fi
}

put_secret redis-url "${REDIS_URL:-}"
put_secret gemini-api-key "${GEMINI_API_KEY:-}"
put_secret mongodb-uri "${MONGODB_URI:-}"
put_secret phoenix-endpoint "${PHOENIX_COLLECTOR_ENDPOINT:-}"
put_secret elastic-url "${ELASTIC_URL:-}"
put_secret elastic-api-key "${ELASTIC_API_KEY:-}"
put_secret dynatrace-url "${DYNATRACE_URL:-}"
put_secret dynatrace-token "${DYNATRACE_API_TOKEN:-}"
put_secret gitlab-token "${GITLAB_TOKEN:-}"
put_secret gitlab-project-id "${GITLAB_PROJECT_ID:-}"

echo "Secrets updated for project ${PROJECT}"
