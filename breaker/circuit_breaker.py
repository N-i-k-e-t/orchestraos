"""Redis-backed circuit breaker state machine."""

from __future__ import annotations

import time
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from checkpoint.redis_store import RedisStore


class BreakerState(str, Enum):
    CLOSED = "closed"
    HALF_OPEN = "half_open"
    OPEN = "open"


class CircuitBreaker:
    """
    Protects agent sessions by tripping when risk_score exceeds threshold.

    States:
      - CLOSED: normal operation
      - OPEN: calls blocked after trip
      - HALF_OPEN: probing recovery after cooldown
    """

    DEFAULT_THRESHOLD = 0.8
    DEFAULT_COOLDOWN_SEC = 30
    HALF_OPEN_MAX_CALLS = 3

    def __init__(
        self,
        store: RedisStore,
        session_id: str,
        threshold: float = DEFAULT_THRESHOLD,
        cooldown_sec: int = DEFAULT_COOLDOWN_SEC,
    ) -> None:
        self._store = store
        self._session_id = session_id
        self._threshold = threshold
        self._cooldown_sec = cooldown_sec
        self._half_open_calls = 0

    @property
    def state(self) -> BreakerState:
        return self._load_state()["state"]

    def allow_call(self) -> bool:
        """Return True if the session is permitted to proceed."""
        current = self._load_state()
        state = current["state"]

        if state == BreakerState.OPEN:
            if time.time() - current.get("tripped_at", 0) >= self._cooldown_sec:
                self._transition(BreakerState.HALF_OPEN)
                self._half_open_calls = 0
                return True
            return False

        if state == BreakerState.HALF_OPEN:
            if self._half_open_calls >= self.HALF_OPEN_MAX_CALLS:
                return False
            self._half_open_calls += 1
            return True

        return True

    def record_risk(self, risk_score: float) -> BreakerState:
        """Evaluate risk score and potentially trip the breaker."""
        if risk_score > self._threshold:
            self._transition(BreakerState.OPEN, tripped_at=time.time(), risk_score=risk_score)
            return BreakerState.OPEN

        current = self._load_state()
        if current["state"] == BreakerState.HALF_OPEN:
            self._transition(BreakerState.CLOSED, risk_score=risk_score)
            return BreakerState.CLOSED

        self._transition(BreakerState.CLOSED, risk_score=risk_score)
        return BreakerState.CLOSED

    def reset(self) -> None:
        self._store.store_breaker_state(
            self._session_id,
            {"state": BreakerState.CLOSED.value, "tripped_at": 0},
        )

    def _load_state(self) -> dict:
        raw = self._store.get_breaker_state(self._session_id) or {
            "state": BreakerState.CLOSED.value,
            "tripped_at": 0,
        }
        state_val = raw.get("state", BreakerState.CLOSED.value)
        if isinstance(state_val, str):
            raw["state"] = BreakerState(state_val)
        return raw

    def _transition(self, new_state: BreakerState, **extra) -> None:
        payload: dict = {"state": new_state.value, **extra}
        self._store.store_breaker_state(self._session_id, payload)
