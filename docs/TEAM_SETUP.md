# Team setup — OrchestraOS Loop Sentinel

Onboard Rutuja and Ayush (Antigravity) and Niket (Cursor) on the same repo and GCP project.

## At a glance

| Who | IDE | Branch | GCP |
|-----|-----|--------|-----|
| Niket | Cursor | `niket/backbone` | `orchestraos-498316` |
| Rutuja | Antigravity | `rutuja/monitor` | Same project |
| Ayush | Antigravity | `ayush/dashboard` | Same project |

**Repo:** https://github.com/N-i-k-e-t/orchestraos

**Live dashboard:** Currently unreachable (Cloud Run timeout). Use **local dashboard** until Ayush redeploys — see [Live status dashboard](#live-status-dashboard) below.

**Full branching guide:** [BRANCHING.md](BRANCHING.md)

**Easy setup guides (share with teammates):**

| Person | Guide |
|--------|-------|
| Rutuja | [setup/RUTUJA_SETUP.md](setup/RUTUJA_SETUP.md) · [Antigravity prompt](setup/ANTIGRAVITY_PROMPT_RUTUJA.md) |
| Ayush | [setup/AYUSH_SETUP.md](setup/AYUSH_SETUP.md) · [Antigravity prompt](setup/ANTIGRAVITY_PROMPT_AYUSH.md) |

**Full project status:** [CHECKPOINT.md](CHECKPOINT.md)

**Secrets:** Public guide [SECRETS_LOCAL.md](SECRETS_LOCAL.md). Niket shares filled [setup/SECRETS_SHARE.template.md](setup/SECRETS_SHARE.template.md) via Slack/WhatsApp only — never GitHub.

**Live resources:** [LIVE_RESOURCES.md](LIVE_RESOURCES.md) — keys, auth, GCP config, test scenarios.

---

## Ready-made branches (already on GitHub)

| Branch | Owner |
|--------|-------|
| `main` | Protected demo-ready |
| `dev` | Shared integration |
| `niket/backbone` | Niket |
| `rutuja/monitor` | Rutuja |
| `ayush/dashboard` | Ayush |

---

## Step 1 — GitHub: public repo + protect `main`

**Important:** On GitHub **Free**, branch protection is **not enforced on private repos** (you will see “Not enforced” next to `main`). Make the repo **public** so your existing rule actually works — see **[GITHUB_SETUP.md](GITHUB_SETUP.md)** for the full walkthrough and security notes.

Summary:

1. **Settings → General → Danger Zone → Make public** (only collaborators can push; public can read only)
2. Refresh **Settings → Branches** — `main` should show **Enforced**
3. Confirm rule: require PR + **1 approval** on `main`
4. **Settings → Collaborators** — only Niket, Rutuja, Ayush (Write access)

Collaborators Rutuja and Ayush are already added.

---

## Step 2 — One command setup per person

PowerShell uses **`;`** not **`&&`**.

### Rutuja

```powershell
git clone https://github.com/N-i-k-e-t/orchestraos.git ; cd orchestraos ; git checkout rutuja/monitor ; poetry install ; cd dashboard ; npm install ; cd .. ; copy .env.example .env
```

### Ayush

```powershell
git clone https://github.com/N-i-k-e-t/orchestraos.git ; cd orchestraos ; git checkout ayush/dashboard ; poetry install ; cd dashboard ; npm install ; cd .. ; copy .env.example .env
```

### Niket (already cloned)

```powershell
cd c:\Users\niket\Downloads\os-rapid ; git fetch origin ; git checkout niket/backbone
```

---

## Step 3 — Connect to GCP (each person, once)

```powershell
gcloud auth login ; gcloud auth application-default login ; gcloud config set project orchestraos-498316
gcloud auth application-default set-quota-project orchestraos-498316
```

### Quick verify (30 seconds)

```powershell
gcloud config set project orchestraos-498316
poetry run python -c "from google.cloud import pubsub_v1; c=pubsub_v1.PublisherClient(); print(list(c.list_topics(request={'project':'projects/orchestraos-498316'})))"
```

**Pass:** you see topics including `raw-spans` and `feature-vectors`. Or run `.\scripts\verify_gcp.ps1`. Full guide: [VERIFY_GCP.md](VERIFY_GCP.md).

Secrets load from Secret Manager in prod via `shared/config.py`. Never commit `.env`.

See [GCP_SETUP.md](GCP_SETUP.md) for secret names and IAM.

---

## Antigravity onboarding prompt

**Rutuja** — copy entire prompt from [setup/ANTIGRAVITY_PROMPT_RUTUJA.md](setup/ANTIGRAVITY_PROMPT_RUTUJA.md)  
**Ayush** — copy entire prompt from [setup/ANTIGRAVITY_PROMPT_AYUSH.md](setup/ANTIGRAVITY_PROMPT_AYUSH.md)

Short version (Rutuja):

```text
EXECUTION MODE — set up OrchestraOS locally and connect to GCP. Do not change architecture.

1. Clone and install:
   git clone https://github.com/N-i-k-e-t/orchestraos.git
   cd orchestraos
   git checkout rutuja/monitor
   poetry install
   cd dashboard
   npm install
   cd ..

2. Environment:
   - Copy .env.example to .env
   - Set REDIS_URL=redis://localhost:6379/0
   - Set PUBSUB_EMULATOR_HOST=localhost:8085
   - Set GOOGLE_CLOUD_PROJECT=orchestraos-498316
   - Do NOT commit .env

3. GCP auth:
   gcloud auth login
   gcloud auth application-default login
   gcloud config set project orchestraos-498316

4. Verify:
   poetry run pytest tests/ -v
   poetry run orchestraos-demo

Report: branch name, GCP project, test count. Then stop.
```

---

## Daily workflow

```powershell
git checkout dev ; git pull origin dev
git checkout <your-branch> ; git merge dev
git add . ; git commit -m "feat: description" ; git push
```

Open PR → **`dev`** on GitHub. See [BRANCHING.md](BRANCHING.md).

---

## Cursor onboarding (Niket)

Before each session:

```powershell
git checkout dev ; git pull origin dev
git checkout niket/backbone ; git merge dev
.\scripts\verify_local.ps1
```

---

## Who does what next

| Task | Owner |
|------|-------|
| Fix Cloud Run dashboard (redeploy + public access) | Ayush |
| Retry VPC connector + full stack deploy | Ayush |
| Gemini API key in Secret Manager | Niket or Rutuja |
| Video + screenshots | Anyone |
| PR reviews on `dev` | Rotate — author cannot approve own PR |

---

## Live status dashboard

Cloud Run URL is currently **not loading** (timeout). For demos and dev:

```powershell
poetry run orchestraos-dashboard
```

Open http://localhost:8080 — Demo, Incidents, and Metrics pages work locally.

After Ayush redeploys, update `configs/gcp.yaml` → `live_dashboard_url` and this doc.

---

## Shared config

| Local dev | Production |
|-----------|------------|
| `.env` (gitignored) | GCP Secret Manager |
| `shared/config.py` | Same code paths |

Niket runs secret setup once — see [GCP_SETUP.md](GCP_SETUP.md).
