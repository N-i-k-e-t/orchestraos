"""Health checks for breaker service dependencies."""

from __future__ import annotations

from checkpoint.redis_store import RedisStore


class HealthAgent:
    """Reports health of Redis and breaker subsystem."""

    def __init__(self, store: RedisStore) -> None:
        self._store = store

    def check(self) -> dict[str, str]:
        redis_ok = self._store.ping()
        return {
            "status": "ok" if redis_ok else "degraded",
            "redis": "up" if redis_ok else "down",
            "service": "orchestraos-breaker",
        }
