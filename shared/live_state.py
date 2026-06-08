"""Live health snapshots in Redis for the dashboard."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol


class LiveStateBackend(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ex: int | None = None) -> None: ...
    def keys(self, pattern: str) -> list[str]: ...
    def lpush(self, key: str, value: str) -> None: ...
    def ltrim(self, key: str, start: int, end: int) -> None: ...
    def lrange(self, key: str, start: int, end: int) -> list[str]: ...
    def ping(self) -> bool: ...


SERVICES = (
    "collector",
    "detectors",
    "monitor",
    "breaker",
    "remediation",
    "partners",
    "dashboard",
)


class LiveStateStore:
    """Reads/writes live breaker, scores, and service health in Redis."""

    LIVE_PREFIX = "orch:live:"
    SERVICE_PREFIX = "orch:service:"
    INCIDENTS_KEY = "orch:incidents:stream"
    TTL = 3600

    def __init__(self, backend: LiveStateBackend) -> None:
        self._redis = backend

    def ping(self) -> bool:
        return self._redis.ping()

    def update_session(
        self,
        session_id: str,
        *,
        breaker_state: str = "closed",
        risk_score: float = 0.0,
        loop_score: float = 0.0,
        progress_score: float = 1.0,
        active_agents: list[str] | None = None,
    ) -> None:
        payload = {
            "session_id": session_id,
            "breaker_state": breaker_state,
            "risk_score": risk_score,
            "loop_score": loop_score,
            "progress_score": progress_score,
            "active_agents": active_agents or [],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        key = f"{self.LIVE_PREFIX}{session_id}"
        self._redis.set(key, json.dumps(payload), ex=self.TTL)

    def list_sessions(self) -> list[dict[str, Any]]:
        keys = self._redis.keys(f"{self.LIVE_PREFIX}*")
        sessions: list[dict[str, Any]] = []
        for key in sorted(keys):
            raw = self._redis.get(key)
            if raw:
                sessions.append(json.loads(raw))
        return sessions

    def set_service_health(self, service: str, status: str, detail: str = "") -> None:
        payload = {
            "service": service,
            "status": status,
            "detail": detail,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._redis.set(f"{self.SERVICE_PREFIX}{service}", json.dumps(payload), ex=self.TTL)

    def get_service_health(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for service in SERVICES:
            raw = self._redis.get(f"{self.SERVICE_PREFIX}{service}")
            if raw:
                result.append(json.loads(raw))
            else:
                result.append({"service": service, "status": "unknown", "detail": "", "updated_at": None})
        return result

    def seed_defaults(self) -> None:
        for service in SERVICES:
            self.set_service_health(service, "ok" if service == "dashboard" else "standby")

    def append_incident(self, incident: dict[str, Any]) -> None:
        incident = {**incident, "created_at": incident.get("created_at") or datetime.now(timezone.utc).isoformat()}
        self._redis.lpush(self.INCIDENTS_KEY, json.dumps(incident))
        self._redis.ltrim(self.INCIDENTS_KEY, 0, 99)

    def list_incidents(self, limit: int = 20) -> list[dict[str, Any]]:
        raw = self._redis.lrange(self.INCIDENTS_KEY, 0, limit - 1)
        return [json.loads(item) for item in raw]
