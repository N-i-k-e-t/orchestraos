#!/usr/bin/env bash
# Verify GCP project + Pub/Sub access for OrchestraOS teammates.
set -euo pipefail

PROJECT="${GCP_PROJECT:-orchestraos-498316}"

echo "==> Project: ${PROJECT}"
gcloud config set project "${PROJECT}" >/dev/null
gcloud auth application-default set-quota-project "${PROJECT}" 2>/dev/null || true

poetry run python -c "
from google.cloud import pubsub_v1
c = pubsub_v1.PublisherClient()
topics = [t.name.split('/')[-1] for t in c.list_topics(request={'project': 'projects/${PROJECT}'})]
pipeline = [t for t in topics if t in ('raw-spans', 'feature-vectors', 'breaker.events', 'remediation.actions')]
print(f'OK — {len(topics)} topics on ${PROJECT}')
print('Pipeline:', pipeline)
assert 'raw-spans' in topics, 'missing raw-spans — run scripts/setup_gcp.sh'
assert 'feature-vectors' in topics, 'missing feature-vectors'
print('Verify passed.')
"
