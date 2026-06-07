# Live resources & testing guide

What keys, auth, and GCP configuration you need to run OrchestraOS **live** on Google Cloud, and which **real-world scenarios** to test for the hackathon demo.

**GCP project:** `slimy-497412` · **Region:** `us-central1`  
**Repo:** https://github.com/N-i-k-e-t/orchestraos

Related: [GCP_SETUP.md](GCP_SETUP.md) · [SECRETS_LOCAL.md](SECRETS_LOCAL.md) · [DEPLOY.md](DEPLOY.md) · [HACKATHON_AUDIT.md](HACKATHON_AUDIT.md)

---

## Live run — auth & configuration

### One-time GCP auth (each person deploying)

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project slimy-497412
```

| Who | IAM role needed |
|-----|-----------------|
| **Deploy (Ayush)** | `roles/run.admin`, `roles/cloudbuild.builds.editor`, `roles/artifactregistry.writer` |
| **Secrets (Niket)** | `roles/secretmanager.admin` (create/update secrets) |
| **Teammates (read secrets)** | `roles/secretmanager.secretAccessor` |

Grant teammate access:

```powershell
gcloud projects add-iam-policy-binding slimy-497412 --member="user:EMAIL" --role="roles/secretmanager.secretAccessor"
gcloud projects add-iam-policy-binding slimy-497412 --member="user:EMAIL" --role="roles/run.admin"
```

Cloud Run services use service account **`orchestraos-runtime@slimy-497412.iam.gserviceaccount.com`**. Do not commit personal service-account JSON to git.

---

## Secrets in GCP Secret Manager (live production)

| Secret ID | Required for full stack? | Used by | Where to get it |
|-----------|--------------------------|---------|-----------------|
| **`gemini-api-key`** | **Yes** | Monitor / RiskAgent | [Google AI Studio](https://aistudio.google.com/apikey), or use **Vertex AI** on GCP (`USE_VERTEX_GEMINI=true`, no key needed) |
| **`redis-url`** | **Yes** | Collector, breaker, remediation | Memorystore Redis URL after VPC connector — `redis://HOST:6379/0` |
| **`phoenix-endpoint`** | **Yes (Arize track)** | Collector → Arize Phoenix | Your Phoenix collector URL |
| `mongodb-uri` | Optional | Partners worker | MongoDB Atlas |
| `elastic-url` + `elastic-api-key` | Optional | Partners | Elastic Cloud |
| `dynatrace-url` + `dynatrace-token` | Optional | Partners | Dynatrace tenant |
| `gitlab-token` + `gitlab-project-id` | Optional | Partners | GitLab PAT + project ID |

Set real values:

```powershell
$env:GCP_PROJECT = "slimy-497412"
$env:GEMINI_API_KEY = "your-key"
$env:REDIS_URL = "redis://YOUR_MEMORYSTORE_IP:6379/0"
$env:PHOENIX_COLLECTOR_ENDPOINT = "https://your-phoenix-url"
.\scripts\provision_secrets.ps1
```

For **Arize MCP** (hackathon primary track), also enable:

```env
PARTNER_ARIZE_ENABLED=true
PHOENIX_COLLECTOR_ENDPOINT=https://your-phoenix-url
PHOENIX_MCP_URL=https://your-phoenix-url/mcp
```

Private team key sheet (not on GitHub): copy `docs/setup/SECRETS_SHARE.template.md` → fill → share via Slack/WhatsApp. See [SECRETS_LOCAL.md](SECRETS_LOCAL.md).

---

## GCP infrastructure (one-time)

| Component | Purpose | Status |
|-----------|---------|--------|
| Project `slimy-497412` | All services | Done |
| Artifact Registry `orchestraos` | Docker images | Done |
| Pub/Sub topics/subscriptions | Event pipeline | Done |
| VPC connector `orchestraos-connector` | Reach Memorystore | Retry if failed |
| Memorystore Redis | Circuit breaker state | Needs VPC |
| 7 Cloud Run services | Full pipeline | Dashboard only until full deploy |

Full live deploy:

```powershell
gcloud builds submit --config=cloudbuild.yaml --project=slimy-497412
$env:GCP_PROJECT = "slimy-497412"
.\scripts\deploy_cloud_run.ps1
```

Canonical config: [configs/gcp.yaml](../configs/gcp.yaml)

---

## Two live tiers

| Tier | What runs | Keys needed | Public URL |
|------|-----------|-------------|------------|
| **Demo only** | Dashboard + in-process demo | **None** | Cloud Run dashboard |
| **Full pipeline** | Collector → detectors → Gemini → breaker → remediation → partners | `gemini-api-key`, `redis-url`, `phoenix-endpoint` (+ optional partners) | Dashboard + collector OTLP |

**Hackathon minimum:** dashboard URL + 3-min video with live demo.  
**Full technical proof:** collector URL + Phoenix traces + Gemini classification.

---

## Environment variables reference

### Local dev (`.env` from `.env.example`)

| Variable | Default | Notes |
|----------|---------|-------|
| `REDIS_URL` | `redis://localhost:6379/0` | Docker compose Redis |
| `PUBSUB_EMULATOR_HOST` | `localhost:8085` | Local emulator |
| `GOOGLE_CLOUD_PROJECT` | `orchestraos-local` | Use `slimy-497412` for real GCP |
| `GEMINI_API_KEY` | (unset) | Optional locally; required for live Gemini without Vertex |
| `USE_VERTEX_GEMINI` | `true` | Vertex AI on GCP when no emulator |
| `VERTEX_AI_LOCATION` | `us-central1` | Must match deploy region |
| `GEMINI_MODEL` | `gemini-2.0-flash` | RiskAgent model |
| `BREAKER_RISK_THRESHOLD` | `0.8` | Trip threshold |
| `PARTNER_ARIZE_ENABLED` | `false` | Set `true` for Arize |
| `PHOENIX_COLLECTOR_ENDPOINT` | — | Arize Phoenix OTLP |
| `PHOENIX_MCP_URL` | — | Phoenix MCP tools |

### Production (Cloud Run)

Secrets load from **Secret Manager** via `shared/config.py`. No `.env` on Cloud Run — inject via `--set-secrets` in deploy scripts.

---

## Where to test live

| What | URL / command | Pass criteria |
|------|---------------|---------------|
| Dashboard health | `{dashboard-url}/api/health` | `{"status":"ok","service":"orchestraos-dashboard-api"}` |
| Dashboard UI | Browser → dashboard URL | Two-pane demo; **Run live demo** works |
| Collector health | `{collector-url}/health` | `"redis":"up"` |
| OTLP ingest | `POST {collector-url}/v1/traces` | Span accepted |
| Local full stack | `docker compose up --build` | `curl http://localhost:4318/health` |
| Tests | `poetry run pytest tests/ -v` | 83 tests pass |
| Money-shot demo | `poetry run orchestraos-demo` | ~5 calls, breaker trips, RECOVERED |
| Local dashboard | `poetry run orchestraos-dashboard` | http://localhost:8080 |
| Arize Phoenix | Phoenix UI | Traces/sessions visible |
| Gemini backend | See verify command below | `vertex` or `api_key` |

Current dashboard URL (update after redeploy): https://orchestraos-dashboard-397417416325.us-central1.run.app

### Verify Gemini path

```powershell
$env:GEMINI_API_KEY = "your-key"
poetry run python -c "from monitor_model.gemini_client import GeminiClient; c=GeminiClient(); print(c.backend, c.available)"
```

### Verify collector ingest (after full deploy)

```powershell
$collector = "https://YOUR-COLLECTOR-URL"
curl.exe -X POST "$collector/v1/traces" -H "Content-Type: application/json" -d "{\"trace_id\":\"t1\",\"span_id\":\"s1\",\"session_id\":\"deploy-test\",\"tool_name\":\"web_search\",\"params\":{\"q\":\"test\"},\"token_count\":100,\"latency_ms\":200,\"state_hash\":\"abc123\"}"
```

---

## Real-world scenarios to test

Built-in scenarios: `agent_harness/replay_cards/`

| Scenario | Real-world analogue | Live or replay | How to run |
|----------|---------------------|----------------|------------|
| **AutoGPT infinite loop** | Agent repeats `web_search` with identical params | **Live** | `poetry run orchestraos-demo` or dashboard **Run live demo** |
| **Cursor agent tool loop** | IDE agent re-reads same file, no progress | Replay | Dashboard Incidents / replay cards |
| **Replit agent loop** | Cloud IDE stuck in deploy/retry loop | Replay | `replay_cards/replit.json` |
| **Gemini CLI loop** | CLI agent repeats tool calls | Replay | `replay_cards/gemini_cli.json` |
| **Air Canada chatbot** | Bot repeats refund policy, never resolves | Replay | `replay_cards/air_canada.json` |

### Recommended test order (video + judges)

1. **AutoGPT live loop** — primary demo (400 → 5 calls, ~99% cost reduction).
2. **POST OTLP spans to live collector** — proves production ingestion path.
3. **Send 3 identical spans** — triggers loop detection → Gemini risk → breaker (full stack).
4. **Open Arize Phoenix** — confirm traces + MCP session registration.
5. **Dashboard** — unprotected vs protected side-by-side.

### What each scenario proves

| Scenario | Detects | Gemini | Breaker | Remediation |
|----------|---------|--------|---------|-------------|
| AutoGPT loop | LoopAgent (call 3) | Risk score + reason | Opens at >0.8 | Fallback tool / recover |
| Cursor file loop | Progress + loop scores | Classifies stall | Trips | Rewrite / rollback |
| Air Canada bot | Context stagnation | Escalation risk | Trips | Human escalation path |

---

## Pre-demo checklist

- [ ] `gemini-api-key` in Secret Manager (or Vertex AI on GCP)
- [ ] `redis-url` set (Memorystore + VPC connector)
- [ ] `phoenix-endpoint` set + `PARTNER_ARIZE_ENABLED=true`
- [ ] All 7 Cloud Run services deployed
- [ ] Dashboard URL loads in browser
- [ ] `poetry run orchestraos-demo` passes locally
- [ ] Phoenix shows traces from a test session
- [ ] 3-min video recorded ([VIDEO_SCRIPT.md](VIDEO_SCRIPT.md))
- [ ] Devpost form filled ([SUBMISSION.md](SUBMISSION.md))

---

## Quick reference — who needs what locally

| Person | `.env` keys | GCP auth |
|--------|-------------|----------|
| **Everyone** | Redis + Pub/Sub emulator defaults | Optional for local pytest |
| **Rutuja** | `GEMINI_API_KEY` (if not using Secret Manager) | `gcloud auth application-default login` |
| **Ayush** | Deploy uses gcloud, not `.env` keys | `run.admin` + deploy scripts |
| **Niket** | Partner keys when testing integrations | Secret Manager admin |

**83 tests pass with zero API keys** — keys only needed for live Gemini, Phoenix, and full Cloud Run stack.
