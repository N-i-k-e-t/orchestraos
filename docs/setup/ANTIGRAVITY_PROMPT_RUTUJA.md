# Antigravity prompt — Rutuja (copy everything below)

Paste this entire block into **Google Antigravity** after accepting the GitHub collaborator invite.

---

```text
EXECUTION MODE — Onboard me onto the OrchestraOS Loop Sentinel project in Antigravity.
Do NOT change architecture, scope, or the repo structure. Follow strict rules:
allowed ecosystem only (Gemini, Vertex AI, Cloud Run, Pub/Sub, Secret Manager,
Arize, MongoDB, Elastic, Dynatrace, GitLab). Never hardcode secrets.

I am Rutuja. My ready-made branch already exists: rutuja/monitor
Repo: https://github.com/N-i-k-e-t/orchestraos
GCP project: orchestraos-498316

STEP 1 — Clone & checkout my branch
- git clone https://github.com/N-i-k-e-t/orchestraos.git
- cd orchestraos
- git checkout rutuja/monitor
- git pull origin rutuja/monitor

STEP 2 — Install dependencies
- poetry install
- cd dashboard ; npm install ; cd ..
(PowerShell uses ';' not '&&')

STEP 3 — Local environment
- Copy .env.example to .env
- Set REDIS_URL=redis://localhost:6379/0
- Set PUBSUB_EMULATOR_HOST=localhost:8085
- Set GOOGLE_CLOUD_PROJECT=orchestraos-498316
- Confirm .env is in .gitignore and is NOT staged for commit

STEP 4 — Connect Antigravity to Google Cloud
- gcloud auth login
- gcloud auth application-default login
- gcloud config set project orchestraos-498316
- gcloud config list

STEP 5 — Verify Secret Manager access (keys live here, not in code)
- gcloud secrets list
  Expected names: gemini-api-key, mongodb-uri, redis-url, phoenix-endpoint, etc.
- shared/config.py loads Secret Manager in prod and .env locally — do NOT edit keys into code
- If secrets list fails, ask Niket to grant roles/secretmanager.secretAccessor

STEP 6 — Verify the stack runs
- poetry run pytest tests/ -v
  Expected: 79 tests pass
- poetry run orchestraos-demo
  Expected: demo completes without errors
- Optional: docker compose up --build (Redis + Pub/Sub emulator)
- Optional: curl http://localhost:4318/health after compose is up

STEP 7 — Confirm my ownership areas (read only, do not refactor yet)
- monitor_model/ — Gemini RiskAgent
- remediation/ — retry, rewrite, rollback, fallback
- docs/ — team documentation

MY WORKFLOW (remember for later):
- Daily: git checkout dev ; git pull ; git checkout rutuja/monitor ; git merge dev
- Push work: git add . ; git commit -m "feat: ..." ; git push
- Open Pull Request → base: dev (NOT main)

OUTPUT: Report branch name (rutuja/monitor), active GCP project, secret names visible,
pytest result (X/79 passed), demo status. Then stop and wait for my next task.
```

---

Also see: [RUTUJA_SETUP.md](RUTUJA_SETUP.md)
