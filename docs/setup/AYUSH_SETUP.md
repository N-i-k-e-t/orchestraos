# Ayush — quick setup (Antigravity)

**Your branch:** `ayush/dashboard`  
**You own:** Dashboard, Cloud Run, infra, agent harness  
**Repo:** https://github.com/N-i-k-e-t/orchestraos (public — only collaborators can push)

---

## Before you start

- GitHub invite accepted (you are a **collaborator**)
- Install: [Python 3.11+](https://www.python.org/), [Poetry](https://python-poetry.org/), [Node.js 18+](https://nodejs.org/), [Google Cloud SDK](https://cloud.google.com/sdk), [Docker](https://www.docker.com/) (optional, for `docker compose`)

---

## Step 1 — Clone your branch (copy all, paste in terminal)

**Windows (PowerShell):**

```powershell
git clone https://github.com/N-i-k-e-t/orchestraos.git
cd orchestraos
git checkout ayush/dashboard
poetry install
cd dashboard
npm install
cd ..
copy .env.example .env
```

**Mac / Linux:**

```bash
git clone https://github.com/N-i-k-e-t/orchestraos.git
cd orchestraos
git checkout ayush/dashboard
poetry install
cd dashboard && npm install && cd ..
cp .env.example .env
```

---

## Step 2 — Connect to GCP (once)

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project slimy-497412
```

You need deploy access on project `slimy-497412`. Ask Niket if `gcloud run services list` fails.

---

## Step 3 — Verify it works

```bash
poetry run pytest tests/ -v
cd dashboard
npm run build
cd ..
poetry run orchestraos-dashboard
```

Open **http://localhost:8080** — Demo page should load.

**Expected:** 79 tests pass, dashboard builds, local server runs.

---

## Step 4 — Open in Antigravity

1. Open Antigravity → **Open folder** → select your `orchestraos` folder  
2. Copy the **full prompt** from [ANTIGRAVITY_PROMPT_AYUSH.md](ANTIGRAVITY_PROMPT_AYUSH.md) and paste it into Antigravity chat

Or paste this short confirm prompt:

```text
I am Ayush on branch ayush/dashboard. Confirm pytest passes and dashboard builds.
Do not change architecture. Report test count and stop.
```

---

## Your folders (edit here)

| Folder | What it does |
|--------|----------------|
| `dashboard/` | React UI (Demo, Incidents, Metrics) |
| `infra/` | Dockerfiles, Cloud Run YAML |
| `scripts/` | `deploy_cloud_run.ps1`, `setup_gcp.ps1` |
| `agent_harness/` | Protected vs unprotected demo agents |
| `cloudbuild.yaml` | Cloud Build config |

Shared code (coordinate before changing): `shared/cloudrun.py`, `configs/gcp.yaml`

---

## Your top tasks

| Priority | Task | Command |
|----------|------|---------|
| 1 | Fix live dashboard (currently times out) | `.\scripts\deploy_cloud_run.ps1` or `bash scripts/deploy_cloud_run.sh` |
| 2 | Retry VPC connector + full stack | See [DEPLOY.md](../DEPLOY.md) |
| 3 | Update live URL in `configs/gcp.yaml` after deploy | Edit `live_dashboard_url` |

Live URL (broken now): https://orchestraos-dashboard-397417416325.us-central1.run.app

---

## Every day (3 commands)

```powershell
git checkout dev ; git pull origin dev
git checkout ayush/dashboard ; git merge dev
# ... do your work ...
git add . ; git commit -m "feat: what you changed" ; git push
```

Then on GitHub: **Pull Request → base: `dev`** (not `main`).

Ask Niket or Rutuja to approve your PR.

---

## Deploy dashboard (when ready)

```powershell
gcloud config set project slimy-497412
.\scripts\deploy_cloud_run.ps1
```

Or on Mac/Linux:

```bash
gcloud config set project slimy-497412
bash scripts/deploy_cloud_run.sh
```

After deploy, test:

```bash
curl https://YOUR-NEW-URL/api/health
```

Should return: `{"status":"ok","service":"orchestraos-dashboard-api"}`

---

## Need help?

| Topic | Doc |
|-------|-----|
| Deploy steps | [DEPLOY.md](../DEPLOY.md) |
| GCP project + secrets | [GCP_SETUP.md](../GCP_SETUP.md) |
| Branching rules | [BRANCHING.md](../BRANCHING.md) |
| Full team guide | [TEAM_SETUP.md](../TEAM_SETUP.md) |
