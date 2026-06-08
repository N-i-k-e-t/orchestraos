# Cloud Shell bootstrap — `orchestraos-498316`

One-time GCP identity setup run in **Google Cloud Shell** for the hackathon project.  
Canonical config: [configs/gcp.yaml](../configs/gcp.yaml)

---

## Project

| Setting | Value |
|---------|-------|
| **Project ID** | `orchestraos-498316` |
| **Region** | `us-central1` |
| **Owners** | niketpatil1624@gmail.com, kulkarnirutuja127@gmail.com, ayushpatel7869595243@gmail.com |

Switch locally:

```bash
gcloud config set project orchestraos-498316
```

---

## Service accounts

| Account | Email | Purpose |
|---------|-------|---------|
| **Deploy / CI** | `orchestraos-sa@orchestraos-498316.iam.gserviceaccount.com` | Build, deploy, Vertex, Pub/Sub, secrets |
| **Cloud Run runtime** | `orchestra-runtime@orchestraos-498316.iam.gserviceaccount.com` | Services at runtime (Pub/Sub publish) |

`orchestraos-sa` **already existed** when re-run — that is expected. IAM role bindings were applied successfully.

### Roles on `orchestraos-sa` (hackathon-allowed ecosystem)

| Role | Why |
|------|-----|
| `roles/aiplatform.user` | Vertex AI / Gemini |
| `roles/pubsub.editor` | Event pipeline |
| `roles/secretmanager.secretAccessor` | Read secrets at deploy/runtime |
| `roles/run.developer` | Deploy Cloud Run services |
| `roles/artifactregistry.writer` | Push Docker images |
| `roles/logging.logWriter` | Cloud Logging |

---

## JSON key file — blocked (use ADC instead)

Key creation failed with org policy:

```
FAILED_PRECONDITION: Key creation is not allowed on this service account.
type: constraints/iam.disableServiceAccountKeyCreation
```

**Do not rely on `orchestraos-key.json`.** Use one of these instead:

| Method | When |
|--------|------|
| `gcloud auth application-default login` | Local dev on your laptop |
| Cloud Shell default credentials | Scripts in Cloud Shell |
| Cloud Run attached SA | Production (`orchestra-runtime@...`) |
| `gcloud auth login` | Deploy from teammate machine |

Never commit service-account JSON to git.

---

## Cloud Shell script (idempotent)

Run in Cloud Shell (or use [scripts/bootstrap_sa.sh](../scripts/bootstrap_sa.sh)):

```bash
export PROJECT_ID=$(gcloud config get-value project)
export SA_NAME="orchestraos-sa"
export SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create SA (skip if exists)
gcloud iam service-accounts create $SA_NAME \
  --display-name="OrchestraOS Service Account" 2>/dev/null || true

for ROLE in \
  roles/aiplatform.user \
  roles/pubsub.editor \
  roles/secretmanager.secretAccessor \
  roles/run.developer \
  roles/artifactregistry.writer \
  roles/logging.logWriter ; do
    gcloud projects add-iam-policy-binding $PROJECT_ID \
      --member="serviceAccount:${SA_EMAIL}" \
      --role="$ROLE" --quiet
done

echo "SA ready: $SA_EMAIL"
echo "Auth: use gcloud ADC — JSON keys blocked by org policy"
```

---

## Next steps after bootstrap

1. **Enable APIs + infra** — `.\scripts\setup_gcp.ps1` or `bash scripts/setup_gcp.sh` with `GCP_PROJECT=orchestraos-498316`
2. **Provision secrets** — `.\scripts\provision_secrets.ps1`
3. **Build + deploy** — `gcloud builds submit` then `.\scripts\deploy_cloud_run.ps1`
4. **Teammate auth** — each person runs `gcloud auth login` + `gcloud auth application-default login`

---

## Verify setup (each teammate — copy/paste)

```powershell
gcloud config set project orchestraos-498316
gcloud auth application-default set-quota-project orchestraos-498316
poetry run python -c "from google.cloud import pubsub_v1; c=pubsub_v1.PublisherClient(); print(list(c.list_topics(request={'project':'projects/orchestraos-498316'})))"
```

**Pass:** list includes `raw-spans`, `feature-vectors`, and other pipeline topics (~18 total).  
**Script:** `.\scripts\verify_gcp.ps1` or `bash scripts/verify_gcp.sh`  
**Guide:** [VERIFY_GCP.md](VERIFY_GCP.md)

See [GCP_SETUP.md](GCP_SETUP.md) · [LIVE_RESOURCES.md](LIVE_RESOURCES.md)
