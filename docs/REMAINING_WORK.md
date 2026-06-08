# Remaining work — GitHub, GCP, hackathon

**Project:** `orchestraos-498316` · **Region:** `us-central1`  
**Repo:** https://github.com/N-i-k-e-t/orchestraos  
**Deadline:** June 11, 2026

This doc answers: what’s done, what’s left, what to push to GitHub, what to deploy to GCP, and how production usage works.

Related: [CHECKPOINT.md](CHECKPOINT.md) · [DEPLOY.md](DEPLOY.md) · [LIVE_RESOURCES.md](LIVE_RESOURCES.md) · [AGENT_REGISTRY.md](AGENT_REGISTRY.md)

---

## ✅ Done (do not redo)

| Area | Status | Evidence |
|------|--------|----------|
| Full agent pipeline (code) | ✅ | 104 tests · `shared/pipeline.py` · `tests/test_pipeline_agents_working.py` |
| 50+ agents (82 capabilities) | ✅ | `poetry run python scripts/list_agents.py` |
| Gemini primary + fallback | ✅ | `monitor_model/risk_agent.py` |
| Learning agents (MongoDB) | ✅ | `learning/` + `LearningCoordinator` |
| Health dashboard (local) | ✅ | `http://localhost:8080/health` after `poetry run orchestraos-dashboard` |
| GCP project + SA bootstrap | ✅ | `orchestraos-498316` · [CLOUD_SHELL_SETUP.md](CLOUD_SHELL_SETUP.md) |
| Pub/Sub topics (18+) | ✅ | `.\scripts\verify_gcp.ps1` |
| Team branches on GitHub | ✅ | `dev`, `niket/backbone`, `rutuja/monitor`, `ayush/dashboard` |
| Old dashboard on Cloud Run | ⚠️ Partial | `/api/health` works — **old build** (no `/health/live`) |

---

## ⬜ Remaining (priority order)

### P0 — Must ship before Devpost (June 11)

| # | Task | Owner | Blocker? |
|---|------|-------|----------|
| 1 | **Commit + push** all local agent/health work to GitHub | Niket | Yes — teammates + deploy need latest code |
| 2 | **Set real secrets** in Secret Manager | Niket | Yes — Gemini + Redis required for live stack |
| 3 | **VPC connector + Memorystore Redis** | Ayush | Yes — collector/workers need `redis-url` |
| 4 | **Cloud Build** all 7 Docker images | Ayush | Yes |
| 5 | **Deploy all 7 Cloud Run services** to `orchestraos-498316` | Ayush | Yes |
| 6 | **Update** `configs/gcp.yaml` → `live_dashboard_url` | Ayush | For README + Devpost |
| 7 | **Record 3-min video** | All | Devpost required |
| 8 | **Fill Devpost** (repo, URL, video) | Niket | [SUBMISSION.md](SUBMISSION.md) |
| 9 | **Phoenix screenshots** | Rutuja / Niket | Arize track proof |

### P1 — Should do

| # | Task | Owner |
|---|------|-------|
| 10 | Grant teammates `secretmanager.secretAccessor` | Niket |
| 11 | Merge `dev` → `main` after PR review | All |
| 12 | Verify live `/health/live` + `/health/agents` on Cloud Run | Ayush |
| 13 | POST test span to live collector URL | Ayush |
| 14 | Wire Rutuja’s Gemini on `rutuja/monitor` with live Vertex | Rutuja |

### P2 — Nice to have

| # | Task | Owner |
|---|------|-------|
| 15 | MongoDB Atlas URI for learning + partners | Niket |
| 16 | Elastic / Dynatrace / GitLab partner keys | Optional |
| 17 | CI on GitHub Actions | Post-hackathon |

---

## 📤 What to push to GitHub (now)

**~50 uncommitted files** on `niket/backbone` (agents, health dashboard, pipeline, tests, docs). Remote is still at commit `70a0cd8` (before this work).

### Niket — commit & push

```powershell
cd c:\Users\niket\Downloads\os-rapid
git checkout niket/backbone
git add -A
git status   # confirm no .env or secrets

git commit -m "feat: wire 50+ agents into live pipeline, health dashboard, and learning domain"
git push origin niket/backbone

git checkout dev
git merge niket/backbone
git push origin dev

# Sync teammate branches
git checkout rutuja/monitor && git merge dev && git push origin rutuja/monitor
git checkout ayush/dashboard && git merge dev && git push origin ayush/dashboard
git checkout niket/backbone
```

### What teammates pull

```powershell
git pull origin ayush/dashboard   # Ayush
git pull origin rutuja/monitor    # Rutuja
poetry install
poetry run pytest tests/ -q       # expect 104 passed
```

### Do NOT push

- `.env`, `TEAM_SECRETS_SHARE.md`, `orchestraos-key.json`, any API keys
- Verify: `git status` shows no secret files staged

---

## ☁️ What to push / deploy to GCP

GCP has **two layers**: infrastructure (once) and **container images** (each deploy).

### Layer 1 — Infrastructure (one-time / retry)

```powershell
gcloud config set project orchestraos-498316
$env:GCP_PROJECT = "orchestraos-498316"
$env:GCP_REGION = "us-central1"

# If VPC failed before, retry without skipping memorystore:
.\scripts\setup_gcp.ps1
```

Creates / verifies:

| Resource | Purpose |
|----------|---------|
| APIs enabled | Cloud Run, Pub/Sub, Secret Manager, Redis, VPC, Cloud Build |
| Artifact Registry `orchestraos` | Docker images |
| Pub/Sub topics + subscriptions | Event pipeline |
| Secret Manager placeholders | `gemini-api-key`, `redis-url`, etc. |
| VPC connector `orchestraos-connector` | Reach Memorystore |
| Memorystore `orchestraos-redis` | Breaker + live state |

### Layer 2 — Real secret values

```powershell
$env:GCP_PROJECT = "orchestraos-498316"
$env:GEMINI_API_KEY = "your-gemini-key"          # or use Vertex only on GCP
$env:REDIS_URL = "redis://10.x.x.x:6379/0"       # from Memorystore after setup
$env:PHOENIX_COLLECTOR_ENDPOINT = "https://..."   # Arize Phoenix
$env:MONGODB_URI = "mongodb+srv://..."            # optional, for learning
$env:ARIZE_API_KEY = "..."                        # optional
.\scripts\provision_secrets.ps1
```

**Minimum for full stack:** `gemini-api-key` + `redis-url`  
**Minimum for Arize track:** + `phoenix-endpoint` + `PARTNER_ARIZE_ENABLED=true`

### Layer 3 — Build images (Cloud Build)

```powershell
cd c:\Users\niket\Downloads\os-rapid
gcloud builds submit --config=cloudbuild.yaml --project=orchestraos-498316
```

Builds 7 images → `us-central1-docker.pkg.dev/orchestraos-498316/orchestraos/`:

| Image | Service |
|-------|---------|
| `collector:latest` | OTLP ingest |
| `detectors:latest` | Detector swarm worker |
| `monitor:latest` | Risk / Gemini worker |
| `breaker:latest` | Circuit breaker worker |
| `remediation:latest` | Recovery chain worker |
| `partners:latest` | Arize / MongoDB / etc. |
| `dashboard:latest` | UI + `/health/live` |

### Layer 4 — Deploy to Cloud Run

```powershell
$env:GCP_PROJECT = "orchestraos-498316"
$env:IMAGE_TAG = "latest"
.\scripts\deploy_cloud_run.ps1
```

| Cloud Run service | Public? | URL use |
|-------------------|---------|---------|
| `orchestraos-dashboard` | **Yes** | Devpost demo URL · `/health` page |
| `orchestraos-collector` | **Yes** | External agents POST `/v1/traces` |
| `orchestraos-detectors` | Internal | Pub/Sub worker |
| `orchestraos-monitor` | Internal | Pub/Sub worker |
| `orchestraos-breaker` | Internal | Pub/Sub worker |
| `orchestraos-remediation` | Internal | Pub/Sub worker |
| `orchestraos-partners` | Internal | Arize / MongoDB export |

### Layer 5 — Verify live GCP

```powershell
# URLs
gcloud run services list --project=orchestraos-498316 --region=us-central1

# Dashboard
curl.exe https://YOUR-DASHBOARD-URL/api/health
curl.exe https://YOUR-DASHBOARD-URL/health/live
curl.exe https://YOUR-DASHBOARD-URL/health/agents

# Collector
curl.exe -X POST "https://YOUR-COLLECTOR-URL/v1/traces" `
  -H "Content-Type: application/json" `
  -d '{"trace_id":"t1","span_id":"s1","session_id":"real-world-test","tool_name":"web_search","params":{"q":"test"},"token_count":100,"latency_ms":200,"state_hash":"abc"}'
```

Update after deploy:

- `configs/gcp.yaml` → `live_dashboard_url`
- `README.md` → Hackathon submission section
- `docs/SUBMISSION.md` → live URLs

---

## 🌍 How OrchestraOS is used on GCP (real world)

### Who sends data?

**External AI agents** (AutoGPT, LangGraph, CrewAI, custom apps) — OrchestraOS does **not** run the agent. They emit OpenTelemetry-style spans to your collector.

### Production flow

```
┌─────────────────┐
│  External Agent │  (customer's AutoGPT / LangGraph / MCP app)
│  on any host    │
└────────┬────────┘
         │ POST /v1/traces  (JSON span)
         ▼
┌─────────────────┐     Pub/Sub        ┌──────────────────┐
│ Cloud Run       │ ── raw-spans ──► │ detectors worker │ LoopAgent, TokenAgent, …
│ collector       │                  └────────┬─────────┘
│ + Redis checkpoint                  feature-vectors
└─────────────────┘                           ▼
                                     ┌──────────────────┐
                                     │ monitor worker   │ RiskAgent + Gemini (Vertex)
                                     └────────┬─────────┘
                                              │ risk-assessments
                                              ▼
                                     ┌──────────────────┐
                                     │ breaker worker   │ CircuitBreakerAgent
                                     └────────┬─────────┘
                                              │ breaker-events
                         ┌────────────────────┼────────────────────┐
                         ▼                    ▼                    ▼
              ┌──────────────────┐  ┌──────────────┐   ┌─────────────────┐
              │ remediation      │  │ partners     │   │ Memorystore     │
              │ Retry→Rollback→  │  │ Arize Phoenix│   │ Redis           │
              │ Fallback→Learn   │  │ MongoDB      │   │ breaker + live  │
              └──────────────────┘  └──────────────┘   └─────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │ dashboard (public)│  /health · /health/live · demo UI
              └──────────────────┘
```

### What happens on a loop (real world)

1. Agent calls `web_search` with same params 3× → spans hit collector  
2. **Detector worker** sets `loop_score > 0.8`  
3. **Monitor worker** calls **Vertex Gemini** → `risk_score > 0.8`  
4. **Breaker worker** opens circuit → blocks further calls  
5. **Remediation worker** runs Retry → Rollback → Fallback tool  
6. **Learning agents** read incident history from MongoDB (if configured)  
7. **Partners worker** exports traces to **Arize Phoenix**  
8. **Dashboard** shows live breaker state at `/health`

### How users / judges interact

| User | Action |
|------|--------|
| **Dev / judge** | Open dashboard URL → Demo + Health tabs |
| **External agent** | Configure OTLP HTTP exporter → collector URL |
| **Ops** | `gcloud logging read` · Phoenix UI for traces |
| **Team** | `poetry run orchestraos-demo` locally if Cloud Run down |

### GCP services used (hackathon ecosystem)

| GCP product | Role |
|-------------|------|
| **Cloud Run** | 7 services (serverless containers) |
| **Pub/Sub** | Async pipeline between stages |
| **Memorystore Redis** | Breaker state + live health snapshots |
| **Secret Manager** | API keys (never in git) |
| **Vertex AI / Gemini** | Risk classification (primary) |
| **Artifact Registry** | Docker images |
| **Cloud Build** | CI build to registry |
| **VPC connector** | Cloud Run → Redis |

---

## 👥 Who does what (this week)

| Person | Branch | Tasks |
|--------|--------|-------|
| **Niket** | `niket/backbone` | Push agent work · set secrets · Devpost · video script |
| **Ayush** | `ayush/dashboard` | `setup_gcp.ps1` · Cloud Build · `deploy_cloud_run.ps1` · fix live URL |
| **Rutuja** | `rutuja/monitor` | Live Gemini/Vertex test · Phoenix screenshots · monitor worker verify |

---

## 📋 Pre-Devpost checklist

- [ ] Git: latest code on `dev` and teammate branches
- [ ] GCP: all 7 Cloud Run services `Ready`
- [ ] Secrets: `gemini-api-key`, `redis-url`, `phoenix-endpoint` have real values
- [ ] Live dashboard URL loads `/health` and `/api/demo/compare`
- [ ] Live collector accepts `POST /v1/traces`
- [ ] `configs/gcp.yaml` `live_dashboard_url` updated
- [ ] 3-min video uploaded
- [ ] Devpost form complete
- [ ] README has public URL + video link

---

## 🖥️ What works TODAY without GCP deploy

For demos while Ayush deploys:

```powershell
poetry run orchestraos-demo
poetry run orchestraos-dashboard   # http://localhost:8080/health
poetry run python scripts/list_agents.py
poetry run pytest tests/ -q        # 104 passed
```

This proves all agents work; GCP deploy makes it **internet-accessible** for judges and external agents.
