# OrchestraOS — 3-Minute Demo Video Script

**Target length:** 2:45 – 3:00  
**Format:** Screen recording + voiceover (Loom, OBS, or similar)  
**Resolution:** 1920×1080 preferred

---

## Pre-recording checklist

- [ ] Dashboard running (`poetry run orchestraos-dashboard` or Cloud Run URL)
- [ ] Browser at demo page, zoom 100%, no personal bookmarks visible
- [ ] Terminal ready with `poetry run orchestraos-demo` (optional live pipeline shot)
- [ ] Close notifications, use light / clean desktop wallpaper

---

## Script

### 0:00 – 0:20 | Hook — The problem

**Visual:** Text slide or terminal showing an agent looping endlessly.

**Voiceover:**

> "Your AI agent just made the same tool call four hundred times. Twenty minutes. Forty-two dollars. And every observability platform told you… after it already failed.
>
> OrchestraOS Loop Sentinel is different. We don't just tell you your agent failed — we make sure it doesn't."

---

### 0:20 – 0:45 | What it is

**Visual:** Architecture diagram from README or `docs/ARCHITECTURE.md`.

**Voiceover:**

> "OrchestraOS is a multi-agent reliability operating system built for the Google Cloud Rapid Agent Hackathon. It watches external agents — AutoGPT, LangGraph, CrewAI, anything that speaks OpenTelemetry — and protects them in real time.
>
> Spans flow in through our collector, six detector agents score loop risk and progress, Gemini Flash classifies the threat, a circuit breaker trips at eighty percent risk, and a remediation chain recovers the session — usually in five calls or fewer."

---

### 0:45 – 1:30 | Architecture walkthrough

**Visual:** Scroll through README architecture table OR animate the mermaid flowchart.

**Voiceover:**

> "The pipeline is event-driven on Google Pub/Sub. LoopAgent uses O-one fingerprint counting — on the third identical call, loop score crosses zero point eight. RiskAgent combines that with Gemini and forces a critical score. The breaker opens in Redis. Then remediation runs: retry, prompt rewrite, rollback, fallback tool — and human escalation to GitLab if needed.
>
> We export traces to Arize Phoenix, incidents to MongoDB, logs to Elastic, and events to Dynatrace. Six deployable services — not fifty microservices."

---

### 1:30 – 2:15 | Live demo — The money shot

**Visual:** Dashboard Demo page (`/`) — two-pane comparison.

**Actions on screen:**
1. Show static comparison: LEFT rose pane (400 calls, $42, FAILURE) vs RIGHT emerald pane (5 calls, $0.36, RECOVERED)
2. Point to **99.1% cost reduction** banner
3. Click **Run live demo** — show protected log with breaker trip + recovery steps
4. Briefly open **Incidents** tab — loop + breaker_trip entries
5. Briefly open **Metrics** tab — cost saved

**Voiceover:**

> "Here's AutoGPT stuck in an infinite web search loop. Without OrchestraOS: four hundred calls, twenty minutes, forty-two dollars, failure.
>
> With OrchestraOS: five calls, forty-seven seconds, thirty-six cents, recovered. Ninety-nine percent cost reduction.
>
> Watch the protected log — loop detected on call three, breaker opens, remediation chain runs, session recovered. That's the money shot."

---

### 2:15 – 2:45 | GCP + partners

**Visual:** `docs/DEPLOY.md` or Cloud Run console showing services; optional Arize Phoenix trace view.

**Voiceover:**

> "Everything deploys to Google Cloud Run with Memorystore Redis, Secret Manager, and Artifact Registry. The collector accepts OTLP on a public URL. Workers run with minimum one instance so Pub/Sub never misses an event.
>
> Primary track integration: Arize Phoenix gets every span as OpenTelemetry. Secondary tracks: MongoDB for incidents, Elastic for logs, Dynatrace for APM, GitLab for escalations. Gemini Flash powers risk classification — no OpenAI, no Anthropic — fully within the allowed ecosystem."

---

### 2:45 – 3:00 | Close

**Visual:** Dashboard hero line + GitHub repo URL + tagline card.

**Voiceover:**

> "OrchestraOS Loop Sentinel. Every other platform tells you your agent failed. OrchestraOS makes sure it doesn't.
>
> Repo link in the description. MIT licensed. Try the live demo — link below. Thank you."

---

## B-roll shots (optional, cut in during voiceover)

| Shot | File to capture |
|------|-----------------|
| Terminal demo | `poetry run orchestraos-demo` output |
| Tests green | `poetry run pytest tests/ -v` (79 passed) |
| Collector health | `curl localhost:4318/health` |
| Docker stack | `docker compose ps` all services up |
| Cloud Run URLs | Output of `deploy_cloud_run.sh` |

---

## Post-production

- Add lower-third: **OrchestraOS Loop Sentinel | GCP Rapid Agent Hackathon**
- Background music: optional, low volume, royalty-free
- Export: MP4 H.264, upload to YouTube (unlisted) or Loom
- Add URL to `README.md` under **Video URL**

---

## One-liner descriptions (for Devpost / submission form)

**Short (150 chars):**  
Multi-agent reliability OS that detects AI agent infinite loops, trips a circuit breaker, and auto-recovers in ≤5 calls — 99% cost reduction on AutoGPT demo.

**Medium (500 chars):**  
OrchestraOS Loop Sentinel observes external AI agents via OpenTelemetry, runs six parallel detectors + Gemini Flash risk scoring, trips a Redis-backed circuit breaker at 80% risk, and executes a five-step remediation chain. Built on Google Cloud (Pub/Sub, Cloud Run, Memorystore, Secret Manager) with Arize Phoenix, MongoDB, Elastic, and Dynatrace integrations. Demo: AutoGPT loop — 400 calls/$42 unprotected vs 5 calls/$0.36 protected.
