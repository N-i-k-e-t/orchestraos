# Hackathon compliance audit — Google Cloud Rapid Agent Hackathon

**Deadline:** June 11, 2026 · **Devpost:** https://rapid-agent.devpost.com  
**Repo:** https://github.com/N-i-k-e-t/orchestraos

Judging criteria: **Technological Implementation · Design · Potential Impact · Quality of the Idea**

---

## Hard requirements — gap scan

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Gemini as reasoning brain | **PASS** (with key/GCP) | `monitor_model/gemini_client.py` — Vertex AI primary, API key secondary; `risk_agent.py` merges Gemini output |
| Google Cloud Agent Builder | **PASS** | `monitor_model/agent_builder.py` — `MonitorAgentBuilder` orchestrates ingest → Gemini → guardrails |
| Arize MCP integration (track) | **PASS** | `integrations/phoenix_mcp.py` + OTLP in `integrations/arize_exporter.py`; wired in `partner_hub.py` |
| Beyond chat (multi-step + tools) | **PASS** | `agent_harness/protected_agent.py` — detect → classify → break → remediate |
| Public repo + MIT license | **PASS** | Public GitHub; `LICENSE` (MIT) |
| Hosted URL (Cloud Run) | **PARTIAL** | Dashboard deployed but URL times out — Ayush must redeploy |
| ~3 min video + Devpost | **PENDING** | Script: `docs/VIDEO_SCRIPT.md` |

---

## Judging criteria alignment

| Criterion | Status | How to prove |
|-----------|--------|--------------|
| 1. Technological Implementation | **STRONG** | Vertex Gemini + Agent Builder + Pub/Sub + Phoenix OTLP/MCP + 79+ tests |
| 2. Design | **STRONG** | Light-theme two-pane dashboard `dashboard/src/pages/DemoPage.tsx` |
| 3. Potential Impact | **STRONG** | 99.1% cost reduction demo; README "Why it matters" |
| 4. Quality of the Idea | **STRONG** | Agents protecting agents — reliability OS, not another chatbot |

---

## Verify locally

```powershell
# All tests (includes Agent Builder + Phoenix MCP)
poetry run pytest tests/ -v

# Demo — multi-step protected agent
poetry run orchestraos-demo

# Gemini path (set key OR use GCP project without emulator)
$env:GEMINI_API_KEY = "your-key"
poetry run python -c "from monitor_model.gemini_client import GeminiClient; c=GeminiClient(); print(c.backend, c.available)"

# Agent Builder orchestration metadata
poetry run python -c "
from monitor_model.agent_builder import MonitorAgentBuilder
b = MonitorAgentBuilder()
r = b.execute('demo', {'loop_score':1,'progress_score':0,'latency_score':0.1,'token_score':0.1,'context_score':0.5,'error_score':0}, loop_detected=True)
print(b.last_execution)
"

# Dashboard
poetry run orchestraos-dashboard
# http://localhost:8080
```

### With Docker + Arize

```powershell
$env:PARTNER_ARIZE_ENABLED = "true"
$env:PHOENIX_COLLECTOR_ENDPOINT = "http://localhost:6006"
$env:PHOENIX_MCP_URL = "http://localhost:6006/mcp"
docker compose up --build
curl http://localhost:4318/health
```

---

## Before Devpost submit

- [ ] Set real `gemini-api-key` in Secret Manager (prod)
- [ ] Redeploy Cloud Run — working public URL
- [ ] Record 3-min video showing: unprotected vs protected + Phoenix traces
- [ ] Capture Arize Phoenix screenshots → `docs/screenshots/`
- [ ] Fill Devpost form with repo, URL, video link

---

## Pitch for judges (30 seconds)

> Most teams build agents that answer questions. OrchestraOS builds agents that **protect other agents** — Gemini classifies loop risk, a circuit breaker stops runaway calls, and remediation recovers the session in five calls instead of four hundred. Arize Phoenix shows every span. It's an immune system for AI agents on Google Cloud.

---

## Related

- [SUBMISSION.md](SUBMISSION.md) · [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) · [ARCHITECTURE.md](ARCHITECTURE.md)
- [LIVE_RESOURCES.md](LIVE_RESOURCES.md) — keys, auth, GCP config, real-world test scenarios
- [CLOUD_SHELL_SETUP.md](CLOUD_SHELL_SETUP.md) — `orchestraos-498316` SA bootstrap (no JSON keys)
