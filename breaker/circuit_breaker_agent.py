"""Circuit breaker agent — session-scoped breaker management."""

from __future__ import annotations

from breaker.circuit_breaker import BreakerState, CircuitBreaker
from checkpoint.redis_store import RedisStore
from shared.config import get_settings
from shared.schemas import BreakerEventSchema, RiskSchema


class CircuitBreakerAgent:
    """Manages per-session circuit breakers backed by Redis."""

    def __init__(
        self,
        store: RedisStore,
        threshold: float | None = None,
        cooldown_sec: int | None = None,
    ) -> None:
        settings = get_settings()
        self._store = store
        self._threshold = threshold if threshold is not None else settings.breaker_risk_threshold
        self._cooldown = cooldown_sec if cooldown_sec is not None else settings.breaker_cooldown_sec
        self._breakers: dict[str, CircuitBreaker] = {}

    def _get_breaker(self, session_id: str) -> CircuitBreaker:
        if session_id not in self._breakers:
            self._breakers[session_id] = CircuitBreaker(
                self._store,
                session_id,
                threshold=self._threshold,
                cooldown_sec=self._cooldown,
            )
        return self._breakers[session_id]

    def process_assessment(self, assessment: RiskSchema) -> BreakerEventSchema:
        """Apply risk assessment and return breaker event."""
        breaker = self._get_breaker(assessment.session_id)
        previous = breaker.state
        new_state = breaker.record_risk(assessment.risk_score)
        allowed = breaker.allow_call()

        return BreakerEventSchema(
            session_id=assessment.session_id,
            state=new_state.value,
            previous_state=previous.value,
            risk_score=assessment.risk_score,
            allowed=allowed,
            reason=assessment.reason,
        )

    def get_state(self, session_id: str) -> BreakerState:
        return self._get_breaker(session_id).state

    def is_allowed(self, session_id: str) -> bool:
        return self._get_breaker(session_id).allow_call()
