# Antigravity prompt — Ayush (copy everything below)

Paste this entire block into **Google Antigravity** after accepting the GitHub collaborator invite.

---

```text
EXECUTION MODE — Onboard me onto the OrchestraOS Loop Sentinel project in Antigravity.
Do NOT change architecture, scope, or the repo structure. Follow strict rules:
allowed ecosystem only (Gemini, Vertex AI, Cloud Run, Pub/Sub, Secret Manager,
Arize, MongoDB, Elastic, Dynatrace, GitLab). Never hardcode secrets.

I am Ayush. My ready-made branch already exists: ayush/dashboard
Repo: https://github.com/N-i-k-e-t/orchestraos
GCP project: slimy-497412

STEP 1 — Clone & checkout my branch
- git clone https://github.com/N-i-k-e-t/orchestraos.git
- cd orchestraos
- git checkout ayush/dashboard
- git pull origin ayush/dashboard

STEP 2 — Install dependencies
- poetry install
- cd dashboard ; npm install ; cd ..
(PowerShell uses ';' not '&&')

STEP 3 — Local environment
- Copy .env.example to .env
- Set REDIS_URL=redis://localhost:6379/0
- Set PUBSUB_EMULATOR_HOST=localhost:8085
- Set GOOGLE_CLOUD_PROJECT=slimy-497412
- Confirm .env is in .gitignore and is NOT staged for commit

STEP 4 — Connect Antigravity to Google Cloud
- gcloud auth login
- gcloud auth application-default login
- gcloud config set project slimy-497412
- gcloud config list
- gcloud run services list --region=us-central1

STEP 5 — Verify Secret Manager + deploy access
- gcloud secrets list
- If deploy fails, ask Niket for Cloud Run Admin / appropriate IAM on slimy-497412

STEP 6 — Verify locally (Cloud Run URL is currently broken — fix is my top task)
- poetry run pytest tests/ -v
  Expected: 79 tests pass
- cd dashboard ; npm run build ; cd ..
- poetry run orchestraos-dashboard
  Open http://localhost:8080 — Demo page should load

STEP 7 — Confirm my ownership areas (read only, do not refactor yet)
- dashboard/ — React UI (DemoPage, Incidents, Metrics)
- infra/ — Dockerfiles, Cloud Run YAML
- scripts/ — deploy_cloud_run.ps1, setup_gcp.ps1
- agent_harness/ — protected vs unprotected demo
- cloudbuild.yaml

STEP 8 — Fix live dashboard (priority after onboarding)
- gcloud config set project slimy-497412
- Run: .\scripts\deploy_cloud_run.ps1  (Windows) or bash scripts/deploy_cloud_run.sh
- Test: curl https://YOUR-URL/api/health → {"status":"ok",...}
- Update configs/gcp.yaml live_dashboard_url and README

MY WORKFLOW (remember for later):
- Daily: git checkout dev ; git pull ; git checkout ayush/dashboard ; git merge dev
- Push work: git add . ; git commit -m "feat: ..." ; git push
- Open Pull Request → base: dev (NOT main)

OUTPUT: Report branch name (ayush/dashboard), active GCP project, pytest result (X/79 passed),
dashboard build status, local dashboard URL, Cloud Run services list. Then stop and wait.
```

---

Also see: [AYUSH_SETUP.md](AYUSH_SETUP.md)
