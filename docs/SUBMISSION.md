# Hackathon Submission Checklist

Google Cloud Rapid Agent Hackathon — OrchestraOS Loop Sentinel

## Project metadata

| Field | Value |
|-------|-------|
| **Project name** | OrchestraOS Loop Sentinel |
| **Tagline** | Every other platform tells you your agent failed. OrchestraOS makes sure it doesn't. |
| **Primary track** | Arize (Phoenix OTLP + MCP) |
| **Secondary tracks** | Dynatrace, Elastic, MongoDB Atlas, GitLab |
| **License** | MIT ([LICENSE](../LICENSE)) |
| **Language** | Python 3.11, TypeScript (dashboard) |

## Submission assets

### Required

- [x] **Public GitHub repository** with README, LICENSE, runnable code
- [x] **104 passing tests** — `poetry run pytest tests/ -v`
- [x] **50+ agent registry** — [AGENT_REGISTRY.md](AGENT_REGISTRY.md) · `poetry run python scripts/list_agents.py`
- [x] **Hackathon audit** — [HACKATHON_AUDIT.md](HACKATHON_AUDIT.md)
- [x] **Architecture documentation** — [ARCHITECTURE.md](ARCHITECTURE.md)
- [x] **Deployment guide** — [DEPLOY.md](DEPLOY.md)
- [ ] **Live demo URL** — deploy to `orchestraos-498316` (see [CLOUD_SHELL_SETUP.md](CLOUD_SHELL_SETUP.md))
- [ ] **3-minute video** — script at [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md)
- [ ] **Screenshots** — see [screenshots/README.md](screenshots/README.md)

### Fill in before submitting

```markdown
Live demo:    (deploy to orchestraos-498316 — TBD)
GCP project:  orchestraos-498316
Collector:    https://orchestraos-collector-XXXX.run.app/v1/traces  (deploy after Memorystore/VPC)
Video:        https://youtube.com/watch?v=XXXX
GitHub:       https://github.com/N-i-k-e-t/orchestraos
```

Copy these into `README.md` under **Hackathon submission**.

---

## Judging alignment

### Problem & solution

| Criterion | How we address it |
|-----------|-------------------|
| Agent reliability | Circuit breaker + remediation recover loops in ≤5 calls |
| Cost control | 99.1% cost reduction demo (400→5 calls, $42→$0.36) |
| Observability | OTel ingestion, Arize Phoenix, Elastic, Dynatrace |
| Google Cloud | Pub/Sub, Cloud Run, Memorystore, Secret Manager, Gemini Flash |

### Technical depth

| Feature | Evidence |
|---------|----------|
| Multi-agent design | 38 agent classes, 81 capabilities, 10 reliability fundamentals — [AGENT_REGISTRY.md](AGENT_REGISTRY.md) |
| Event-driven architecture | 5 Pub/Sub topics, separate worker subscriptions |
| Production deploy | `cloudbuild.yaml`, `scripts/deploy_cloud_run.sh` |
| Test coverage | 99 unit/integration tests across all phases |
| Live health dashboard | `/health/live` + `/health` page (2s poll) |

### Demo scenario

**Live:** AutoGPT infinite loop (`agent_harness/scenario_autogpt.py`)  
**Static replays:** Cursor, Replit, Gemini CLI, Air Canada (`agent_harness/replay_cards/`)

---

## Pre-submit verification

Run locally before recording video or submitting:

```bash
# 1. Tests
poetry run pytest tests/ -v
# Expected: 79 passed

# 2. Demo harness
poetry run orchestraos-demo

# 3. Dashboard (separate terminal)
poetry run orchestraos-dashboard
# Open http://localhost:8080 → Run live demo

# 4. Docker full stack (optional)
docker compose up --build
curl http://localhost:4318/health
curl http://localhost:8080/api/health
```

Cloud Run verification:

```bash
DASH=$(gcloud run services describe orchestraos-dashboard --region=us-central1 --format='value(status.url)')
curl -s "$DASH/api/health"
curl -s "$DASH/api/demo/compare" | head -c 200
```

---

## Team & attribution

- Built with Cursor AI-assisted development
- Gemini Flash for risk classification (Google AI)
- Partner SDKs: httpx (Arize/Elastic/Dynatrace/GitLab), pymongo (MongoDB)

---

## Post-submission

- [ ] Pin demo URL in GitHub repo description
- [ ] Add video link to README
- [ ] Upload screenshots to `docs/screenshots/`
- [ ] Tweet/post with tagline + demo GIF (optional)
