"""Pytest configuration and shared fixtures."""

import json
from typing import Any


class FakeRedisStore:
    """In-memory store mirroring RedisStore interface for unit tests."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, dict[str, Any]] = {}
        self._breakers: dict[str, dict[str, Any]] = {}
        self._remediation_plans: dict[str, dict[str, Any]] = {}
        self._remediation_attempts: dict[str, int] = {}

    def save_checkpoint(self, session_id: str, data: dict[str, Any]) -> None:
        self._checkpoints[session_id] = data

    def load_checkpoint(self, session_id: str) -> dict[str, Any] | None:
        return self._checkpoints.get(session_id)

    def store_breaker_state(self, session_id: str, state: dict[str, Any]) -> None:
        serializable = {k: (v.value if hasattr(v, "value") else v) for k, v in state.items()}
        self._breakers[session_id] = serializable

    def get_breaker_state(self, session_id: str) -> dict[str, Any] | None:
        return self._breakers.get(session_id)

    def ping(self) -> bool:
        return True

    def increment_remediation_attempts(self, session_id: str) -> int:
        self._remediation_attempts[session_id] = self._remediation_attempts.get(session_id, 0) + 1
        return self._remediation_attempts[session_id]

    def get_remediation_attempts(self, session_id: str) -> int:
        return self._remediation_attempts.get(session_id, 0)

    def save_remediation_plan(self, session_id: str, data: dict[str, Any]) -> None:
        self._remediation_plans[session_id] = data

    def load_remediation_plan(self, session_id: str) -> dict[str, Any] | None:
        return self._remediation_plans.get(session_id)
