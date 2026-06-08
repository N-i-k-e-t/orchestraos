# Verify GCP project + Pub/Sub access (PowerShell).
# Usage: .\scripts\verify_gcp.ps1

$Project = if ($env:GCP_PROJECT) { $env:GCP_PROJECT } else { "orchestraos-498316" }

Write-Host "==> Project: $Project"
gcloud config set project $Project | Out-Null
gcloud auth application-default set-quota-project $Project 2>$null

poetry run python -c "from google.cloud import pubsub_v1; c=pubsub_v1.PublisherClient(); topics=[t.name.split('/')[-1] for t in c.list_topics(request={'project':'projects/$Project'})]; print('OK', len(topics), 'topics on $Project'); print('Pipeline:', [t for t in topics if t in ('raw-spans','feature-vectors','breaker.events','remediation.actions')]); assert 'raw-spans' in topics; assert 'feature-vectors' in topics; print('Verify passed.')"

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
