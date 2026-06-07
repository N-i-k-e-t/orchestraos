"""Phase 4 CircuitBreakerAgent tests."""

from unittest.mock import MagicMock

from breaker.circuit_breaker import BreakerState
from breaker.circuit_breaker_agent import CircuitBreakerAgent
from breaker.health_agent import HealthAgent
from shared.schemas import RiskLevel, RiskSchema
from tests.conftest import FakeRedisStore


class TestCircuitBreakerAgent:
    def setup_method(self) -> None:
        self.store = FakeRedisStore()
        self.agent = CircuitBreakerAgent(self.store, threshold=0.8, cooldown_sec=30)

    def _assessment(self, session_id: str, score: float) -> RiskSchema:
        level = RiskLevel.CRITICAL if score > 0.7 else RiskLevel.HEALTHY
        return RiskSchema.from_assessment(
            session_id=session_id,
            status=level,
            risk_score=score,
            reason="test",
            feature_vector={},
        )

    def test_starts_closed_and_allowed(self) -> None:
        event = self.agent.process_assessment(self._assessment("sess-1", 0.2))
        assert event.state == BreakerState.CLOSED.value
        assert event.allowed is True

    def test_trips_on_high_risk(self) -> None:
        event = self.agent.process_assessment(self._assessment("sess-1", 0.85))
        assert event.state == BreakerState.OPEN.value
        assert event.previous_state == BreakerState.CLOSED.value
        assert event.allowed is False

    def test_persists_state_in_redis(self) -> None:
        self.agent.process_assessment(self._assessment("sess-1", 0.9))
        stored = self.store.get_breaker_state("sess-1")
        assert stored is not None
        assert stored["state"] == BreakerState.OPEN.value

    def test_health_agent_reports_redis_up(self) -> None:
        health = HealthAgent(self.store).check()
        assert health["redis"] == "up"
        assert health["status"] == "ok"
