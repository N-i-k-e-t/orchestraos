# Devpost submission — copy/paste guide

**Hackathon:** Google Cloud Rapid Agent Hackathon  
**Deadline:** June 11, 2026  
**GCP project:** `orchestraos-498316` · **Region:** `us-central1`

Fill each Devpost field from the sections below. Replace `[VIDEO_URL]` and screenshot uploads before final submit.

---

## General info

### Project name (max 60 chars)

```
OrbitAgent
```

### Elevator pitch (max 200 chars)

```
Your agent is stuck in orbit. We break the loop before it breaks your budget. ORBIT — Observe, Reason, Break, Intervene, Track — 50+ agents on Google Cloud.
```

*(Character count: ~154)*

### ORBIT backronym (use in story / video)

| Letter | Stage | What happens in OrbitAgent |
|--------|-------|----------------------------|
| **O** | **Observe** | OTLP collector + detector swarm watch every span |
| **R** | **Reason** | Vertex AI Gemini RiskAgent scores risk from fused features |
| **B** | **Break** | Circuit breaker opens at `risk_score > 0.8` |
| **I** | **Intervene** | Remediation chain: retry → rollback → fallback tool |
| **T** | **Track** | OpenTelemetry + Arize Phoenix export full trace proof |

---

## Project details (public page)

### About the project (Markdown)

```markdown
## What inspired us

Production AI agents fail silently. An AutoGPT-style loop can burn **400 tool calls**, **$42**, and **20 minutes** before anyone notices. Dashboards show the crash *after* the damage. We wanted a **reliability OS** that watches external agents (AutoGPT, LangGraph, CrewAI, MCP apps) and **stops + recovers** before budgets are gone.

## What we built

**OrbitAgent** — *your agent is stuck in orbit. We break the loop before it breaks your budget.*

The name is a backronym: every letter is a real pipeline stage on Google Cloud:

- **O — Observe** — OTLP collector + six detector agents flag loops, token burn, latency, errors
- **R — Reason** — Vertex AI Gemini RiskAgent scores risk (grounding + confidence agents)
- **B — Break** — circuit breaker trips at `risk_score > 0.8` (Memorystore Redis)
- **I — Intervene** — remediation chain: retry → rollback → fallback tool → escalation
- **T — Track** — OpenTelemetry + Arize Phoenix OTLP export; live `/health` + Ops Center

Plus a **Learning** layer (incident mining, policy optimization via MongoDB) and **82 registry capabilities** across 10 reliability fundamentals.

**82 registry capabilities** across 10 reliability fundamentals — real Python/TypeScript classes with **110+ tests**, not vanity microservices. **7 Cloud Run services** host the pipeline.

## How we built it

- **Python 3.11** + **Poetry** — collector, workers, agents, pipeline
- **FastAPI** — OTLP ingest + dashboard API
- **React + TypeScript + Vite** — demo dashboard + separate Ops Center (`/ops`)
- **Google Cloud** — Cloud Run (×7), Pub/Sub, Memorystore Redis, Secret Manager, Artifact Registry, Cloud Build, VPC connector, **Vertex AI Gemini**
- **Event-driven pipeline** — `raw-spans` → `feature-vectors` → `risk-assessments` → `breaker-events` → `remediation-plans`
- **Cursor + Antigravity** — team dev on GitHub branches (`niket/backbone`, `rutuja/monitor`, `ayush/dashboard`)

## Demo scenario

AutoGPT infinite loop: identical `web_search` calls. On the **3rd span**, `loop_score > 0.8`. Gemini classifies **critical** risk. Breaker **opens**. Remediation recovers in **≤5 calls** — **99.1% cost reduction** ($42 → $0.36) vs unprotected.

## Challenges we faced

- **Docker image deps** — worker images needed `collector/`, `learning/`, `integrations/` for agent roster; fixed Dockerfiles + defensive `roster.py`
- **Vertex model availability** — `gemini-2.0-flash` 404 on our project; added model fallbacks (`gemini-2.5-flash` smoke-tested)
- **Secret Manager placeholders** — `setup_gcp` seeds `placeholder`; added `check_secrets.py` and `_is_valid_secret()` filtering
- **Team async deploy** — VPC connector + Memorystore blocking; documented in Ops Center connection map

## What we learned

Multi-agent reliability needs **honest boundaries**: external agents emit spans; OrbitAgent never runs the agent itself. Gemini is best as the **Reason** layer on fused detector features, not a replacement for deterministic loop fingerprints. Pub/Sub + Cloud Run maps cleanly to O.R.B.I.T. stages for demos and production.

*(Codebase repo: [orchestraos](https://github.com/N-i-k-e-t/orchestraos) — internal codename retained for GCP services.)*
```

### Built with (technologies — add each as a tag or comma list)

```
Python, TypeScript, FastAPI, React, Vite, Tailwind CSS, Poetry, pytest, Docker, Google Cloud Run, Google Cloud Pub/Sub, Google Cloud Secret Manager, Google Cloud Memorystore (Redis), Google Cloud Artifact Registry, Google Cloud Build, Google Vertex AI, Gemini 2.5 Flash, OpenTelemetry, Redis, MongoDB Atlas, Arize Phoenix, httpx, Pydantic, Uvicorn, GitHub, Cursor, Antigravity
```

### Try it out links

| Label | URL |
|-------|-----|
| **Live dashboard (demo)** | https://orchestraos-dashboard-ew3uwemnxq-uc.a.run.app |
| **Ops Center (monitoring)** | https://orchestraos-dashboard-ew3uwemnxq-uc.a.run.app/ops |
| **Health / agents API** | https://orchestraos-dashboard-ew3uwemnxq-uc.a.run.app/health/agents |
| **OTLP collector** | https://orchestraos-collector-ew3uwemnxq-uc.a.run.app/v1/traces |
| **GitHub (MIT)** | https://github.com/N-i-k-e-t/orchestraos |

### Video demo link

```
[VIDEO_URL]   ← upload 3-min video; script: docs/VIDEO_SCRIPT.md
```

### Image gallery (upload manually)

Suggested screenshots (JPG/PNG, 3:2 ratio):

1. Demo page — unprotected vs protected side-by-side
2. `/health` — live agent firing + breaker state
3. `/ops` — connection map (GitHub → GCP → Cursor → Antigravity)
4. Arize Phoenix traces (when `phoenix-endpoint` configured)
5. `poetry run python scripts/list_agents.py` terminal output

---

## Additional info (judges / organizers)

| Field | Value |
|-------|-------|
| **Submitter type** | Team |
| **Organization name** | N/A |
| **Government employee?** | No |
| **Country of residence** | India |
| **Canada province** | N/A |
| **Partner track** | **Arize** (primary) |
| **Project new or existing (prior to May 5, 2026)?** | New |
| **Open source repository URL** | https://github.com/N-i-k-e-t/orchestraos |
| **OSI license** | MIT — https://github.com/N-i-k-e-t/orchestraos/blob/main/LICENSE |
| **Hosted project URL (judging)** | https://orchestraos-dashboard-ew3uwemnxq-uc.a.run.app |

### Google Cloud products used

```
Vertex AI (Gemini 2.5 Flash), Cloud Run, Cloud Pub/Sub, Secret Manager, Memorystore for Redis, Artifact Registry, Cloud Build, VPC Access Connector, Cloud Logging, IAM Service Accounts
```

### Other tools / products used

```
Arize Phoenix (OTLP + MCP), MongoDB Atlas, Elastic (integration ready), Dynatrace (integration ready), GitLab (fallback integration), OpenTelemetry, FastAPI, React, Redis, Docker, GitHub, Cursor IDE, Google Antigravity
```

### First-time partner tool questions

| Partner | Answer |
|---------|--------|
| **Arize** | Yes, this is my first time using Arize tools. |
| **Elastic** | N/A, I am not submitting for the Elastic track. |
| **Fivetran** | N/A, I am not submitting for the Fivetran track. |
| **GitLab** | N/A, I am not submitting for the GitLab track. |
| **MongoDB** | Yes, this is my first time using MongoDB tools. *(or N/A if only Arize track)* |
| **Dynatrace** | N/A, I am not submitting for the Dynatrace track. |

> **Note:** If you also want MongoDB gallery visibility, select **MongoDB** as secondary and answer MongoDB first-time = Yes. Primary track should remain **Arize**.

---

## Team members (add in Devpost team section if available)

| Name | Role | Branch |
|------|------|--------|
| Niket Patil | Pipeline, agents, Gemini, backbone | `niket/backbone` |
| Rutuja | Monitor / Gemini / Vertex | `rutuja/monitor` |
| Ayush | GCP deploy, dashboard, Cloud Run | `ayush/dashboard` |

---

## Pre-submit checklist

- [ ] Upload 3-minute video → paste URL in **Video demo link**
- [ ] Upload 3–5 screenshots to **Image gallery**
- [ ] Confirm live dashboard loads: `/api/health`, `/health/live`, `/ops`
- [ ] Confirm GitHub `main` is public with MIT LICENSE
- [ ] Set `phoenix-endpoint` in Secret Manager for Arize judge demo (optional live traces)
- [ ] Run locally before recording:
  ```powershell
  poetry run pytest tests/ -q
  poetry run python scripts/check_secrets.py
  poetry run python scripts/check_gemini.py
  ```

---

## Quick copy block (all URLs)

```
Dashboard:  https://orchestraos-dashboard-ew3uwemnxq-uc.a.run.app
Ops:        https://orchestraos-dashboard-ew3uwemnxq-uc.a.run.app/ops
Collector:  https://orchestraos-collector-ew3uwemnxq-uc.a.run.app/v1/traces
GitHub:     https://github.com/N-i-k-e-t/orchestraos
GCP:        orchestraos-498316 (us-central1)
License:    MIT
Track:      Arize (Phoenix)
```
