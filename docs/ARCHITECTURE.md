# OrchestraOS Architecture

## Design principles

1. **Observe, don't host** — External agents emit OpenTelemetry spans; OrchestraOS never executes agent logic.
2. **Six services, not fifty** — Logical agents (LoopAgent, RetryAgent, etc.) are grouped into deployable services.
3. **Event-driven** — Google Pub/Sub decouples every pipeline stage.
4. **Fail-safe** — Deterministic rules + Gemini Flash; breaker trips at `risk_score > 0.8`.
5. **Secrets in Secret Manager** — `.env` for local dev only.

## Pipeline stages

### 1. Collector (`collector/`)

- FastAPI app on port 4318 (Cloud Run: `PORT` env)
- Accepts OTLP JSON at `POST /v1/traces`
- Validates `SpanSchema`, publishes to `raw-spans`, writes Redis checkpoint
- Optionally forwards spans to Arize Phoenix

### 2. Detector swarm (`detectors/`)

Six parallel scorers fused into one feature vector:

| Agent | Signal |
|-------|--------|
| LoopAgent | Repeated tool+params fingerprint (O(1) counter) |
| ProgressAgent | Token delta + state change |
| TokenAgent | Budget consumption |
| LatencyAgent | P95 latency drift |
| ContextAgent | Stagnant state hash |
| ErrorAgent | Error rate |

Publishes `FeatureVectorSchema` to `feature-vectors`.

### 3. Monitor model (`monitor_model/`)

- **RiskAgent** calls Gemini Flash for classification
- Deterministic fallback when Gemini unavailable
- Loop floor: if `loop_score > 0.85`, force `risk_score >= 0.85`
- Publishes `RiskSchema` to `risk-assessments`

### 4. Circuit breaker (`breaker/`)

Redis-backed state machine:

```
CLOSED ──(risk > 0.8)──► OPEN ──(cooldown)──► HALF_OPEN ──(success)──► CLOSED
```

Publishes `BreakerEventSchema` to `breaker-events`.

### 5. Remediation (`remediation/`)

On breaker `OPEN`, orchestrator runs:

1. **Retry** — bounded retry with backoff
2. **PromptRewrite** — Gemini-assisted prompt fix
3. **Rollback** — restore Redis checkpoint
4. **FallbackTool** — substitute tool
5. **HumanEscalation** — GitLab issue (via partners)

Publishes `RemediationPlanSchema` to `remediation-plans`. Resets breaker on recovery.

### 6. Partners (`integrations/`)

Dual Pub/Sub subscriber (`partners-breaker-sub`, `partners-remediation-sub`):

- MongoDB — incident documents
- Elastic — `_doc` indexing
- Dynatrace — custom events API
- GitLab — escalation issues
- Arize — OTLP from collector path

### 7. Dashboard (`dashboard/`)

- React 18 + TypeScript + Vite + Tailwind (**light theme only**)
- Pages: Demo (two-pane rose/emerald), Incidents, Metrics
- FastAPI backend serves `/api/*` + static `dist/`

## Pub/Sub topics

| Topic | Publisher | Consumer(s) |
|-------|-----------|-------------|
| `raw-spans` | Collector | Detectors |
| `feature-vectors` | Detectors | Monitor |
| `risk-assessments` | Monitor | Breaker |
| `breaker-events` | Breaker | Remediation, Partners |
| `remediation-plans` | Remediation | Partners |

## Data stores

| Store | Purpose |
|-------|---------|
| Redis / Memorystore | Checkpoints, breaker state |
| MongoDB Atlas | Incident persistence (partners) |
| Secret Manager | API keys, Redis URL, partner creds |

## GCP deployment topology

```
                    ┌─────────────────┐
  Internet ────────►│ Cloud Run       │
                    │ dashboard       │ (public)
                    └─────────────────┘
  Internet ────────►│ Cloud Run       │
                    │ collector       │ (public, VPC → Redis)
                    └────────┬────────┘
                             │ Pub/Sub
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   detectors            monitor               breaker
   remediation          partners              (internal CR)
        │                    │                    │
        └────────────────────┴────────────────────┘
                             │
                    Memorystore Redis
                    Secret Manager
```

See [DEPLOY.md](DEPLOY.md) for setup commands.
