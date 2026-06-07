# Team setup — OrchestraOS Loop Sentinel

Onboard Rutuja and Ayush (Antigravity) and Niket (Cursor) on the same repo and GCP project.

## At a glance

| Who | IDE | Clone | GCP |
|-----|-----|-------|-----|
| Niket | Cursor | Already local | `slimy-497412` |
| Rutuja | Antigravity | `git clone` | Same project |
| Ayush | Antigravity | `git clone` | Same project |

**Live dashboard (status board):** https://orchestraos-dashboard-397417416325.us-central1.run.app

---

## Step 1 — Push repo (Niket, one time)

Replace `<your-org>` with your GitHub org or username.

```powershell
cd c:\Users\niket\Downloads\os-rapid
git init
git add .
git commit -m "chore: OrchestraOS backbone — phases 1-10 complete, 79 tests passing"
git branch -M main
git checkout -b dev
git remote add origin https://github.com/N-i-k-e-t/orchestraos.git
git push -u origin main
git push -u origin dev
```

## Step 2 — GitHub access

1. Repo → **Settings → Collaborators** → invite Rutuja and Ayush.
2. **Settings → Branches → Add rule** on `main`:
   - Require pull request
   - Require 1 approval
   - (Optional) Require status checks when CI is added

## Step 3 — Branching

Everyone branches from `dev`:

```
main → dev → niket/* | rutuja/* | ayush/*
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full workflow.

---

## Antigravity onboarding prompt

Paste into **Google Antigravity** (replace `<your-org>` and branch name):

```text
EXECUTION MODE — set up OrchestraOS locally and connect to GCP. Do not change architecture.

1. Clone and install:
   git clone https://github.com/N-i-k-e-t/orchestraos.git
   cd orchestraos
   git checkout dev
   git pull origin dev
   git checkout -b rutuja/my-feature
   poetry install
   cd dashboard
   npm install
   cd ..

2. Environment:
   - Copy .env.example to .env
   - Set REDIS_URL=redis://localhost:6379/0
   - Set PUBSUB_EMULATOR_HOST=localhost:8085
   - Set GOOGLE_CLOUD_PROJECT=slimy-497412
   - Do NOT commit .env

3. GCP auth:
   gcloud auth login
   gcloud auth application-default login
   gcloud config set project slimy-497412

4. Verify:
   docker compose up --build
   poetry run pytest tests/ -v
   poetry run orchestraos-demo

Report: branch name, GCP project, test count. Then stop.
```

Ayush should use branch prefix `ayush/` (e.g. `ayush/vpc-connector-fix`).

---

## Cursor onboarding (Niket)

Already on the codebase. Before each session:

```powershell
git checkout dev
git pull origin dev
git checkout -b niket/my-feature
.\scripts\verify_local.ps1
```

---

## Shared config (no keys in git)

| Local dev | Production |
|-----------|------------|
| `.env` (gitignored) | GCP Secret Manager |
| `shared/config.py` reads both | Same code paths |

Niket runs secret setup once — see [GCP_SETUP.md](GCP_SETUP.md).

Teammates with `roles/secretmanager.secretAccessor` on project `slimy-497412` can read secrets after `gcloud auth application-default login`.

---

## Who does what next

| Task | Owner |
|------|-------|
| Retry VPC connector + full Cloud Run deploy | Ayush |
| Gemini API key in Secret Manager | Niket or Rutuja |
| Video + screenshots for submission | Anyone |
| PR reviews on `dev` | Rotate — author cannot approve own PR |

---

## Live status dashboard

After deploy, the dashboard shows:

- **Demo** — two-pane AutoGPT comparison (`dashboard/src/pages/DemoPage.tsx`)
- **Incidents** — loop / breaker / recovery entries
- **Metrics** — cost saved summary

Open the live URL above or run locally:

```powershell
poetry run orchestraos-dashboard
```

Then visit http://localhost:8080
