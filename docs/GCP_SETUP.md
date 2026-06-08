# GCP setup — shared team project

Single GCP project for all three teammates. Local dev uses Docker + emulators; Cloud Run uses Secret Manager.

## Project reference

| Setting | Value |
|---------|-------|
| **Project ID** | `orchestraos-498316` |
| **Region** | `us-central1` |
| **Artifact Registry** | `us-central1-docker.pkg.dev/orchestraos-498316/orchestraos` |
| **Deploy SA** | `orchestraos-sa@orchestraos-498316.iam.gserviceaccount.com` |
| **Cloud Run runtime SA** | `orchestra-runtime@orchestraos-498316.iam.gserviceaccount.com` |
| **Live dashboard** | Deploy pending on new project (see [CLOUD_SHELL_SETUP.md](CLOUD_SHELL_SETUP.md)) |

Canonical YAML: [configs/gcp.yaml](../configs/gcp.yaml)

**Cloud Shell bootstrap (done):** [CLOUD_SHELL_SETUP.md](CLOUD_SHELL_SETUP.md) — `orchestraos-sa` IAM roles applied. JSON keys blocked by org policy; use `gcloud auth application-default login` instead.

---

## One-time setup (Niket or Ayush)

### Windows (PowerShell)

```powershell
$env:GCP_PROJECT = "orchestraos-498316"
$env:GCP_REGION = "us-central1"
$env:SKIP_MEMORYSTORE = "1"   # remove after VPC connector works
.\scripts\setup_gcp.ps1
```

### Bash (Git Bash / Linux)

```bash
export GCP_PROJECT=orchestraos-498316
export GCP_REGION=us-central1
bash scripts/setup_gcp.sh
```

This enables APIs, creates Artifact Registry, Pub/Sub topics/subscriptions, Secret Manager placeholders, service account IAM, and attempts the VPC connector.

**Known issue:** VPC connector `orchestraos-connector` may fail with a GCP internal error. Retry:

```powershell
gcloud compute networks vpc-access connectors create orchestraos-connector `
  --region=us-central1 `
  --range=10.8.0.0/28 `
  --project=orchestraos-498316
```

Memorystore Redis (required for collector/workers in prod) — omit `SKIP_MEMORYSTORE` or run setup without it (~15–20 min).

---

## Secret Manager

Secret IDs (must match `shared/config.py`):

| Secret ID | Used by |
|-----------|---------|
| `redis-url` | Collector, breaker, remediation |
| `gemini-api-key` | Monitor (RiskAgent) |
| `phoenix-endpoint` | Collector → Arize Phoenix |
| `mongodb-uri` | Partners worker |
| `elastic-url`, `elastic-api-key` | Partners |
| `dynatrace-url`, `dynatrace-token` | Partners |
| `gitlab-token`, `gitlab-project-id` | Partners (escalation) |

### Set real values (PowerShell)

```powershell
$env:GCP_PROJECT = "orchestraos-498316"
$env:GEMINI_API_KEY = "your-gemini-key"
$env:REDIS_URL = "redis://YOUR_REDIS_HOST:6379/0"
.\scripts\provision_secrets.ps1
```

Never paste keys into git or Slack — use a password manager or 1:1 share for local `.env` only.

### Grant teammates secret access

```powershell
gcloud projects add-iam-policy-binding orchestraos-498316 `
  --member="user:rutuja@example.com" `
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding orchestraos-498316 `
  --member="user:ayush@example.com" `
  --role="roles/secretmanager.secretAccessor"
```

Optional editor role for deploy:

```powershell
gcloud projects add-iam-policy-binding orchestraos-498316 `
  --member="user:ayush@example.com" `
  --role="roles/run.admin"
```

---

## Build and deploy

### Build all images (Cloud Build)

```powershell
cd c:\Users\niket\Downloads\os-rapid
gcloud builds submit --config=cloudbuild.yaml --project=orchestraos-498316
```

Do **not** pass comma-separated `--substitutions` from PowerShell — defaults live in `cloudbuild.yaml`.

### Deploy all services

```powershell
$env:GCP_PROJECT = "orchestraos-498316"
$env:IMAGE_TAG = "latest"
.\scripts\deploy_cloud_run.ps1
```

### Dashboard only (works without VPC/Redis)

Already deployed. To redeploy:

```powershell
gcloud run deploy orchestraos-dashboard `
  --region=us-central1 `
  --project=orchestraos-498316 `
  --image=us-central1-docker.pkg.dev/orchestraos-498316/orchestraos/dashboard:latest `
  --allow-unauthenticated `
  --port=8080 `
  --command=python `
  --args="-m,dashboard.server"
```

---

## Teammate local GCP auth

Each person on their machine:

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project orchestraos-498316
```

Verify:

```powershell
gcloud config get-value project
gcloud secrets list --project=orchestraos-498316
```

---

## Pub/Sub topics (do not rename)

`raw-spans` → `feature-vectors` → `risk-assessments` → `breaker-events` → `remediation-plans`

Partner fan-out subscriptions: `partners-breaker-sub`, `partners-remediation-sub`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| VPC connector failed | Retry create command above; deploy dashboard-only until fixed |
| Cloud Build empty tag | Fixed — uses `${BUILD_ID}` + `:latest` |
| Collector won't start | Set real `redis-url`; needs VPC + Memorystore |
| Secret access denied | Add `secretAccessor` role for user |
| PowerShell `&&` errors | Use `;` between commands |

Full deploy guide: [DEPLOY.md](DEPLOY.md)  
Live keys & test scenarios: [LIVE_RESOURCES.md](LIVE_RESOURCES.md)
