# OrchestraOS — setup checkpoint

Last updated after team onboarding docs and public repo setup.

**Repo:** https://github.com/N-i-k-e-t/orchestraos (public)  
**GCP project:** `orchestraos-498316`  
**Region:** `us-central1`

---

## Status overview

| Stage | Status | Notes |
|-------|--------|-------|
| Phases 1–10 built | ✅ Done | Full pipeline: collector → detectors → risk → breaker → remediation → dashboard |
| 104 tests passing | ✅ Done | `poetry run pytest tests/ -v` |
| 50+ agent registry (81 entries) | ✅ Done | [AGENT_REGISTRY.md](AGENT_REGISTRY.md) · `scripts/list_agents.py` |
| Light-theme dashboard + demo | ✅ Done | Local: `poetry run orchestraos-dashboard` → http://localhost:8080 |
| Git push to GitHub | ✅ Done | `main`, `dev`, + 3 team branches |
| Repo public (Free plan protection) | ✅ Done | `visibility: public` — branch rules can enforce |
| Ready-made team branches | ✅ Done | `niket/backbone`, `rutuja/monitor`, `ayush/dashboard` |
| Team docs + setup guides | ✅ Done | See [setup/](setup/) |
| Collaborators (Rutuja + Ayush) | ✅ Done | Write access — only they can push |
| Branch protection on `main` | ✅ Done | Classic rule: PR + 1 approval (verify **Enforced** in Settings → Branches) |
| Secrets in GCP Secret Manager | ✅ Done | 10 secrets created — verify real values for `gemini-api-key`, `redis-url` |
| Teammate Secret Manager IAM | ⬜ Pending | Niket grants `roles/secretmanager.secretAccessor` to Rutuja + Ayush |
| Antigravity onboarding | ⬜ Next | Teammates paste prompts in [setup/](setup/) |
| GCP project migrated | ✅ Done | `orchestraos-498316` (was `slimy-497412`) |
| Cloud Shell SA bootstrap | ✅ Done | `orchestraos-sa` IAM roles — no JSON keys (org policy) |
| Cloud Run live dashboard | ⬜ Pending | Ayush deploys to `orchestraos-498316` via `scripts/deploy_cloud_run.ps1` |
| Full stack Cloud Run (7 services) | ⬜ Pending | VPC connector + Memorystore blocked earlier |
| Hackathon video + screenshots | ⬜ Pending | See [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) |

---

## Branches on GitHub

```
main              ← protected, demo-ready
  └── dev         ← integration (PRs target here)
        ├── niket/backbone
        ├── rutuja/monitor
        └── ayush/dashboard
```

---

## Pre-flight (confirmed before Antigravity onboarding)

| Check | Status |
|-------|--------|
| `git push origin main` done | ✅ |
| `dev` branch exists on remote | ✅ |
| `.env.example` committed | ✅ |
| `.env` in `.gitignore` | ✅ |
| Collaborators can clone public repo | ✅ |
| Only collaborators can push | ✅ |

---

## What each person does next

| Person | Action |
|--------|--------|
| **Niket** | Grant Secret Manager access to teammates; keep working on `niket/backbone` |
| **Rutuja** | Paste [ANTIGRAVITY_PROMPT_RUTUJA.md](setup/ANTIGRAVITY_PROMPT_RUTUJA.md) in Antigravity |
| **Ayush** | Paste [ANTIGRAVITY_PROMPT_AYUSH.md](setup/ANTIGRAVITY_PROMPT_AYUSH.md) in Antigravity; fix Cloud Run dashboard |

---

## After teammates connect — deploy flow

Ayush runs (when GCP deploy access confirmed):

```powershell
gcloud config set project orchestraos-498316
.\scripts\deploy_cloud_run.ps1
```

Then update `configs/gcp.yaml` → `live_dashboard_url` and README with the working URL.

---

## Quick links

| Doc | Purpose |
|-----|---------|
| [setup/RUTUJA_SETUP.md](setup/RUTUJA_SETUP.md) | Rutuja easy guide |
| [setup/AYUSH_SETUP.md](setup/AYUSH_SETUP.md) | Ayush easy guide |
| [setup/ANTIGRAVITY_PROMPT_RUTUJA.md](setup/ANTIGRAVITY_PROMPT_RUTUJA.md) | Rutuja Antigravity paste prompt |
| [setup/ANTIGRAVITY_PROMPT_AYUSH.md](setup/ANTIGRAVITY_PROMPT_AYUSH.md) | Ayush Antigravity paste prompt |
| [BRANCHING.md](BRANCHING.md) | Daily git workflow |
| [GITHUB_SETUP.md](GITHUB_SETUP.md) | Public repo + security |
| [GCP_SETUP.md](GCP_SETUP.md) | Secrets + IAM |
| [LIVE_RESOURCES.md](LIVE_RESOURCES.md) | Live keys, auth, test scenarios |
| [CLOUD_SHELL_SETUP.md](CLOUD_SHELL_SETUP.md) | SA bootstrap on orchestraos-498316 |
| [VERIFY_GCP.md](VERIFY_GCP.md) | One-command Pub/Sub verify for teammates |
| [AGENT_REGISTRY.md](AGENT_REGISTRY.md) | 50+ agents claim + 10 fundamentals audit |
| [REMAINING_WORK.md](REMAINING_WORK.md) | What's left: GitHub push, GCP deploy, Devpost |
