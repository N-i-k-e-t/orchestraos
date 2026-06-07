# Rutuja — quick setup (Antigravity)

**Your branch:** `rutuja/monitor`  
**You own:** Monitor model, remediation, Gemini, docs  
**Repo:** https://github.com/N-i-k-e-t/orchestraos (public — only collaborators can push)

---

## Before you start

- GitHub invite accepted (you are a **collaborator**)
- Install: [Python 3.11+](https://www.python.org/), [Poetry](https://python-poetry.org/), [Node.js 18+](https://nodejs.org/), [Google Cloud SDK](https://cloud.google.com/sdk)

---

## Step 1 — Clone your branch (copy all, paste in terminal)

**Windows (PowerShell):**

```powershell
git clone https://github.com/N-i-k-e-t/orchestraos.git
cd orchestraos
git checkout rutuja/monitor
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
git checkout rutuja/monitor
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

Niket will grant you Secret Manager access. **Do not put API keys in git** — use `.env` locally only.

---

## Step 3 — Verify it works

```bash
poetry run pytest tests/ -v
poetry run orchestraos-demo
```

**Expected:** 79 tests pass, demo runs without errors.

---

## Step 4 — Open in Antigravity

1. Open Antigravity → **Open folder** → select your `orchestraos` folder  
2. Paste this prompt to confirm setup:

```text
I am Rutuja on branch rutuja/monitor. Confirm poetry install works and pytest passes.
Do not change architecture. Report test count and stop.
```

---

## Your folders (edit here)

| Folder | What it does |
|--------|----------------|
| `monitor_model/` | Gemini RiskAgent |
| `remediation/` | Retry, rewrite, rollback, fallback |
| `docs/` | Team docs, submission text |

Shared code (coordinate before changing): `shared/schemas.py`, `shared/config.py`

---

## Every day (3 commands)

```powershell
git checkout dev ; git pull origin dev
git checkout rutuja/monitor ; git merge dev
# ... do your work ...
git add . ; git commit -m "feat: what you changed" ; git push
```

Then on GitHub: **Pull Request → base: `dev`** (not `main`).

Ask Niket or Ayush to approve your PR.

---

## Need help?

| Topic | Doc |
|-------|-----|
| Branching rules | [BRANCHING.md](../BRANCHING.md) |
| GCP secrets | [GCP_SETUP.md](../GCP_SETUP.md) |
| Full team guide | [TEAM_SETUP.md](../TEAM_SETUP.md) |

**Dashboard:** Cloud Run is down for now — ignore live URL. Use local: `poetry run orchestraos-dashboard` → http://localhost:8080
