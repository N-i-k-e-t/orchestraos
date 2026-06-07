"""End-to-end loop scenario: detectors → risk → breaker opens."""

from unittest.mock import MagicMock

from breaker.circuit_breaker import BreakerState
from breaker.circuit_breaker_agent import CircuitBreakerAgent
from detectors.swarm import DetectorSwarm
from monitor_model.gemini_client import GeminiClient
from monitor_model.risk_agent import RiskAgent
from shared.schemas import RiskLevel, SpanSchema
from tests.conftest import FakeRedisStore


class TestBreakerLoopScenario:
    def test_loop_scenario_opens_breaker(self) -> None:
        """DoD: breaker opens when AutoGPT infinite loop produces risk > 0.8."""
        store = FakeRedisStore()
        swarm = DetectorSwarm()
        gemini = MagicMock(spec=GeminiClient)
        gemini.available = False
        gemini.classify.return_value = None
        risk_agent = RiskAgent(gemini=gemini)
        breaker_agent = CircuitBreakerAgent(store, threshold=0.8)

        params = {"query": "server status", "target": "localhost"}
        event = None
        risk = None

        for i in range(3):
            vector = swarm.process(
                SpanSchema(
                    trace_id="t1",
                    span_id=f"s{i}",
                    session_id="autogpt-demo",
                    tool_name="web_search",
                    params=params,
                    token_count=50 * (i + 1),
                    latency_ms=200,
                    state_hash="fixed-state",
                )
            )
            risk = risk_agent.assess_vector(vector)
            event = breaker_agent.process_assessment(risk)

        assert risk is not None
        assert event is not None
        assert risk.risk_score > 0.8
        assert risk.status == RiskLevel.CRITICAL
        assert event.state == BreakerState.OPEN.value
        assert event.allowed is False
        assert breaker_agent.get_state("autogpt-demo") == BreakerState.OPEN
