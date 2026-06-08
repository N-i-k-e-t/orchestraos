"""Health API helpers for the dashboard."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from checkpoint.memory_store import MemoryRedisBackend
from checkpoint.redis_store import RedisStore
from shared.roster import load_all_registries
from shared.config import get_redis_url
from shared.live_state import LiveStateStore


def _seed_demo_live(store: LiveStateStore) -> None:
    store.update_session(
        "autogpt-demo",
        breaker_state="open",
        risk_score=0.87,
        loop_score=1.0,
        progress_score=0.1,
        active_agents=["LoopAgent", "RiskAgent", "CircuitBreakerAgent", "FallbackToolAgent"],
    )
    store.update_session(
        "cursor-replay",
        breaker_state="half_open",
        risk_score=0.62,
        loop_score=0.7,
        progress_score=0.35,
        active_agents=["ProgressAgent", "ContextAgent", "RiskAgent"],
    )
    store.append_incident(
        {
            "incident_id": str(uuid.uuid4()),
            "session_id": "autogpt-demo",
            "incident_type": "loop",
            "severity": "critical",
            "reason": "Repeated web_search with identical params",
        }
    )
    store.append_incident(
        {
            "incident_id": str(uuid.uuid4()),
            "session_id": "autogpt-demo",
            "incident_type": "breaker_trip",
            "severity": "critical",
            "reason": "Circuit breaker opened at risk_score 0.87",
        }
    )


@lru_cache(maxsize=1)
def get_live_store() -> LiveStateStore:
    try:
        backend = RedisStore(get_redis_url())
        if backend.ping():
            store = LiveStateStore(backend)
            store.seed_defaults()
            return store
    except Exception:
        pass
    backend = MemoryRedisBackend()
    store = LiveStateStore(backend)
    store.seed_defaults()
    _seed_demo_live(store)
    return store


def agents_payload() -> dict[str, Any]:
    roster = load_all_registries()
    agents = [e for e in roster if e.kind == "agent"]
    capabilities = [e for e in roster if e.kind == "capability-of"]
    firing = set()
    for session in get_live_store().list_sessions():
        firing.update(session.get("active_agents", []))
    return {
        "total": len(roster),
        "agent_count": len(agents),
        "capability_count": len(capabilities),
        "agents_firing": sorted(firing),
        "roster": [e.to_dict() for e in roster],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def live_payload() -> dict[str, Any]:
    store = get_live_store()
    sessions = store.list_sessions()
    return {
        "redis": "up" if store.ping() else "down",
        "services": store.get_service_health(),
        "sessions": sessions,
        "active_agent_count": sum(len(s.get("active_agents", [])) for s in sessions),
        "incidents": store.list_incidents(20),
        "aggregate": {
            "risk_score": max((s.get("risk_score", 0) for s in sessions), default=0.0),
            "loop_score": max((s.get("loop_score", 0) for s in sessions), default=0.0),
            "progress_score": min((s.get("progress_score", 1) for s in sessions), default=1.0),
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
