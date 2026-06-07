# Deploy OrchestraOS to Google Cloud

Phase 9 deploys the full pipeline to **Cloud Run** with **Pub/Sub**, **Secret Manager**, and **Memorystore (Redis)**.

## Architecture on GCP

```
Internet → Cloud Run (dashboard)     ← public URL (DoD)
Internet → Cloud Run (collector)     ← OTLP /v1/traces
           Cloud Run workers (×5)    ← internal, min-instances=1
                ↕ Pub/Sub topics
                ↕ Memorystore Redis (via VPC connector)
                ↕ Secret Manager
```

## Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI authenticated (`gcloud auth login`)
- Docker not required locally if using Cloud Build

## Quick deploy (3 commands)

```bash
export GCP_PROJECT=your-project-id
export GCP_REGION=us-central1

# 1. One-time infra: APIs, Pub/Sub, secrets, Memorystore, VPC connector
bash scripts/setup_gcp.sh

# 2. Set real secret values (Gemini key, optional partners)
export GEMINI_API_KEY=your-key
bash scripts/provision_secrets.sh

# 3. Build + deploy
gcloud builds submit --config=cloudbuild.yaml
bash scripts/deploy_cloud_run.sh
```

The deploy script prints the **public dashboard URL** and collector OTLP endpoint.

### Windows (PowerShell)

Use `;` instead of `&&` to chain commands. Setup and deploy scripts:

```powershell
$env:GCP_PROJECT = "your-project-id"
$env:GCP_REGION = "us-central1"
.\scripts\setup_gcp.ps1
$env:GEMINI_API_KEY = "your-key"
.\scripts\provision_secrets.ps1   # optional wrapper; or bash scripts/provision_secrets.sh in Git Bash
gcloud builds submit --config=cloudbuild.yaml
.\scripts\deploy_cloud_run.ps1
```

Local verification:

```powershell
.\scripts\verify_local.ps1
```

## Verify (DoD)

```bash
# Dashboard loads
curl -s "$(gcloud run services describe orchestraos-dashboard --region=us-central1 --format='value(status.url)')/api/health"

# Collector accepts spans
COLLECTOR=$(gcloud run services describe orchestraos-collector --region=us-central1 --format='value(status.url)')
curl -X POST "${COLLECTOR}/v1/traces" \
  -H "Content-Type: application/json" \
  -d '{"trace_id":"t1","span_id":"s1","session_id":"deploy-test","tool_name":"check_status","params":{},"token_count":10,"latency_ms":50}'
```

Open the dashboard URL in a browser — the two-pane AutoGPT demo should load.

## Services

| Cloud Run service | Image | Ingress | Notes |
|-------------------|-------|---------|-------|
| `orchestraos-dashboard` | `dashboard` | Public | React UI + API |
| `orchestraos-collector` | `collector` | Public | OTLP on `/v1/traces` |
| `orchestraos-detectors` | `detectors` | Internal | Pub/Sub consumer |
| `orchestraos-monitor` | `monitor` | Internal | Gemini risk agent |
| `orchestraos-breaker` | `breaker` | Internal | Redis breaker |
| `orchestraos-remediation` | `remediation` | Internal | Recovery chain |
| `orchestraos-partners` | `partners` | Internal | Arize/MongoDB/Elastic |

## Secret Manager

| Secret ID | Used by |
|-----------|---------|
| `redis-url` | collector, breaker, remediation |
| `gemini-api-key` | monitor |
| `phoenix-endpoint` | collector (Arize) |
| `mongodb-uri` | partners |
| `elastic-url`, `elastic-api-key` | partners |
| `dynatrace-url`, `dynatrace-token` | partners |
| `gitlab-token`, `gitlab-project-id` | partners |

Production code reads secrets via `shared/config.py` — never commit real values.

## Memorystore

`setup_gcp.sh` provisions a **Basic tier 1 GB** Redis instance and writes `redis-url` to Secret Manager. Provisioning takes ~10–20 minutes.

Skip Memorystore for faster local testing against external Redis:

```bash
SKIP_MEMORYSTORE=1 bash scripts/setup_gcp.sh
export REDIS_URL=redis://your-redis-host:6379/0
bash scripts/provision_secrets.sh
```

Cloud Run services use the **VPC connector** (`orchestraos-connector`) to reach Memorystore on the private network.

## Cloud Run YAML (optional)

Reference Knative manifests live in `infra/cloudrun/`:

- `dashboard.yaml` — public dashboard
- `collector.yaml` — public OTLP collector
- `worker.yaml` — template for internal workers

Apply with `envsubst` or use `scripts/deploy_cloud_run.sh` (recommended).

## CI/CD (GitLab / Cloud Build)

`cloudbuild.yaml` builds and pushes all seven images to Artifact Registry. Run manually (defaults in yaml — no `--substitutions` on PowerShell):

```bash
gcloud builds submit --config=cloudbuild.yaml
```

Images are tagged with `${BUILD_ID}` and `:latest`. Deploy with `$env:IMAGE_TAG = "latest"`.

## Cost notes (hackathon)

- Set `--min-instances=0` on workers after demo to reduce cost (may add cold-start latency).
- Memorystore Basic 1 GB has a fixed hourly cost even when idle.
- Pub/Sub and Cloud Run scale to near-zero when idle (except min-instances).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Collector `Redis unreachable` | Check VPC connector + `redis-url` secret |
| Workers not processing | Ensure all 5 workers deployed with `min-instances=1` |
| Gemini errors | Update `gemini-api-key` secret |
| VPC connector create failed | Retry `gcloud compute networks vpc-access connectors create orchestraos-connector --region=us-central1 --range=10.8.0.0/28` or deploy dashboard-only first |
| 403 on secrets | Grant `roles/secretmanager.secretAccessor` to `orchestraos-runtime` SA |
