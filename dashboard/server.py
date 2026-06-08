"""Dashboard API — serves demo, incidents, and metrics to the React frontend."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent_harness.metrics import cost_reduction, estimate_unprotected
from agent_harness.protected_agent import ProtectedAgent
from agent_harness.unprotected_agent import UnprotectedAgent
from dashboard.health_api import agents_payload, get_live_store, live_payload
from shared.cloudrun import get_listen_port
from tests.conftest import FakeRedisStore

REPLAY_DIR = Path(__file__).resolve().parent.parent / "agent_harness" / "replay_cards"
DIST_DIR = Path(__file__).parent / "dist"

app = FastAPI(title="OrchestraOS Dashboard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _format_unprotected(calls: int, cost: float, outcome: str) -> dict:
    return {
        "calls": calls,
        "duration": "20 min",
        "cost_usd": cost,
        "outcome": outcome,
        "tokens": calls * 105,
    }


def _format_protected(calls: int, cost: float, duration_sec: float, outcome: str) -> dict:
    return {
        "calls": calls,
        "duration": f"{int(duration_sec)} sec",
        "cost_usd": cost,
        "outcome": outcome,
        "tokens": calls * 105,
    }


def _run_live_demo() -> dict:
    store = FakeRedisStore()
    live = get_live_store()
    unprot = UnprotectedAgent(max_iterations=400).run()
    agent = ProtectedAgent(store=store, emit_otel=False)  # type: ignore[arg-type]
    prot = agent.run()

    for entry in prot.log:
        live.update_session(
            prot.session_id,
            breaker_state=str(entry.get("breaker_state", "closed")),
            risk_score=float(entry.get("risk_score", 0)),
            loop_score=1.0 if entry.get("loop_detected") else 0.0,
            progress_score=0.2,
            active_agents=["LoopAgent", "RiskAgent", "CircuitBreakerAgent", "FallbackToolAgent"],
        )
        if entry.get("loop_detected"):
            live.append_incident(
                {
                    "incident_id": str(uuid.uuid4()),
                    "session_id": prot.session_id,
                    "incident_type": "loop",
                    "severity": "critical",
                    "reason": "Live demo loop detected",
                }
            )

    unprot_m = estimate_unprotected()
    reduction = cost_reduction(
        type("M", (), {"cost_usd": unprot.cost_usd})(),
        type("M", (), {"cost_usd": prot.cost_usd})(),
    )

    return {
        "scenario": "autogpt",
        "title": "AutoGPT Infinite Loop",
        "unprotected": _format_unprotected(unprot.calls, unprot.cost_usd, unprot.outcome),
        "protected": _format_protected(prot.calls, prot.cost_usd, prot.duration_sec, prot.outcome),
        "cost_reduction_pct": reduction,
        "protected_log": prot.log,
    }


def _static_demo() -> dict:
    card = json.loads((REPLAY_DIR / "autogpt.json").read_text())
    return {
        "scenario": card["scenario"],
        "title": card["title"],
        "unprotected": {
            "calls": card["unprotected"]["calls"],
            "duration": f"{card['unprotected']['duration_min']} min",
            "cost_usd": card["unprotected"]["cost_usd"],
            "outcome": card["unprotected"]["outcome"],
            "tokens": card["unprotected"]["calls"] * 105,
        },
        "protected": {
            "calls": card["protected"]["calls"],
            "duration": f"{card['protected']['duration_sec']} sec",
            "cost_usd": card["protected"]["cost_usd"],
            "outcome": card["protected"]["outcome"],
            "tokens": card["protected"]["calls"] * 105,
        },
        "cost_reduction_pct": round(
            (1 - card["protected"]["cost_usd"] / card["unprotected"]["cost_usd"]) * 100, 1
        ),
    }


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "orchestraos-dashboard-api"}


@app.get("/health/agents")
async def health_agents() -> dict:
    return agents_payload()


@app.get("/health/live")
async def health_live() -> dict:
    return live_payload()


@app.get("/api/demo/compare")
async def demo_compare() -> dict:
    return _static_demo()


@app.post("/api/demo/run")
async def demo_run() -> dict:
    return _run_live_demo()


@app.get("/api/incidents")
async def list_incidents() -> dict:
    incidents = []
    now = datetime.now(timezone.utc).isoformat()

    # Live AutoGPT incident
    incidents.append({
        "incident_id": str(uuid.uuid4()),
        "session_id": "autogpt-demo",
        "incident_type": "loop",
        "severity": "critical",
        "scenario": "AutoGPT",
        "reason": "Repeated web_search with identical params (3rd call)",
        "created_at": now,
    })
    incidents.append({
        "incident_id": str(uuid.uuid4()),
        "session_id": "autogpt-demo",
        "incident_type": "breaker_trip",
        "severity": "critical",
        "scenario": "AutoGPT",
        "reason": "Circuit breaker opened at risk_score 0.85",
        "created_at": now,
    })
    incidents.append({
        "incident_id": str(uuid.uuid4()),
        "session_id": "autogpt-demo",
        "incident_type": "escalation",
        "severity": "info",
        "scenario": "AutoGPT",
        "reason": "Remediation recovered session via fallback tool",
        "created_at": now,
    })

    # Static replay card incidents
    for path in sorted(REPLAY_DIR.glob("*.json")):
        if path.stem == "autogpt":
            continue
        card = json.loads(path.read_text())
        incidents.append({
            "incident_id": str(uuid.uuid4()),
            "session_id": f"{path.stem}-replay",
            "incident_type": "loop",
            "severity": "warning",
            "scenario": card.get("title", path.stem),
            "reason": card.get("description", "Static replay"),
            "created_at": now,
        })

    return {"incidents": incidents}


@app.get("/api/metrics")
async def metrics_summary() -> dict:
    card = json.loads((REPLAY_DIR / "autogpt.json").read_text())
    saved = card["unprotected"]["cost_usd"] - card["protected"]["cost_usd"]
    return {
        "total_sessions": 6,
        "loops_detected": 5,
        "breakers_tripped": 1,
        "recoveries": 1,
        "avg_risk_score": 0.42,
        "cost_saved_usd": round(saved, 2),
    }


if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")


def main() -> None:
    import uvicorn

    from shared.console import configure_stdout_utf8

    configure_stdout_utf8()
    uvicorn.run(
        "dashboard.server:app",
        host="0.0.0.0",
        port=get_listen_port(default=8080),
        reload=False,
    )


if __name__ == "__main__":
    main()
