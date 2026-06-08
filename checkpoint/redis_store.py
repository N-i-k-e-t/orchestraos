"""Redis-backed checkpoint and breaker state store."""

import json
import os
from typing import Any

import redis


class RedisStore:
    """Persists agent checkpoints and circuit breaker state in Redis."""

    CHECKPOINT_PREFIX = "orch:checkpoint:"
    BREAKER_PREFIX = "orch:breaker:"
    REMEDIATION_PREFIX = "orch:remediation:"
    REMEDIATION_ATTEMPTS_PREFIX = "orch:remediation-attempts:"
    DEFAULT_TTL = 86400  # 24 hours

    def __init__(self, redis_url: str | None = None, ttl: int = DEFAULT_TTL) -> None:
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = redis.from_url(url, decode_responses=True)
        self._ttl = ttl

    def save_checkpoint(self, session_id: str, data: dict[str, Any]) -> None:
        key = f"{self.CHECKPOINT_PREFIX}{session_id}"
        self._client.setex(key, self._ttl, json.dumps(data))

    def load_checkpoint(self, session_id: str) -> dict[str, Any] | None:
        key = f"{self.CHECKPOINT_PREFIX}{session_id}"
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def store_breaker_state(self, session_id: str, state: dict[str, Any]) -> None:
        key = f"{self.BREAKER_PREFIX}{session_id}"
        serializable = {k: (v.value if hasattr(v, "value") else v) for k, v in state.items()}
        self._client.setex(key, self._ttl, json.dumps(serializable))

    def get_breaker_state(self, session_id: str) -> dict[str, Any] | None:
        key = f"{self.BREAKER_PREFIX}{session_id}"
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def ping(self) -> bool:
        return self._client.ping()

    def increment_remediation_attempts(self, session_id: str) -> int:
        key = f"{self.REMEDIATION_ATTEMPTS_PREFIX}{session_id}"
        count = self._client.incr(key)
        self._client.expire(key, self._ttl)
        return int(count)

    def get_remediation_attempts(self, session_id: str) -> int:
        key = f"{self.REMEDIATION_ATTEMPTS_PREFIX}{session_id}"
        raw = self._client.get(key)
        return int(raw) if raw else 0

    def save_remediation_plan(self, session_id: str, data: dict[str, Any]) -> None:
        key = f"{self.REMEDIATION_PREFIX}{session_id}"
        self._client.setex(key, self._ttl, json.dumps(data))

    def load_remediation_plan(self, session_id: str) -> dict[str, Any] | None:
        key = f"{self.REMEDIATION_PREFIX}{session_id}"
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    # LiveStateStore protocol helpers
    def get(self, key: str) -> str | None:
        return self._client.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        if ex:
            self._client.setex(key, ex, value)
        else:
            self._client.set(key, value)

    def keys(self, pattern: str) -> list[str]:
        return list(self._client.scan_iter(match=pattern))

    def lpush(self, key: str, value: str) -> None:
        self._client.lpush(key, value)

    def ltrim(self, key: str, start: int, end: int) -> None:
        self._client.ltrim(key, start, end)

    def lrange(self, key: str, start: int, end: int) -> list[str]:
        return self._client.lrange(key, start, end)
