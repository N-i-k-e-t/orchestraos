"""DoD: agent recovers within 5 calls after remediation."""

from unittest.mock import MagicMock

from breaker.circuit_breaker import BreakerState, CircuitBreaker
from breaker.circuit_breaker_agent import CircuitBreakerAgent
from detectors.swarm import DetectorSwarm
from monitor_model.gemini_client import GeminiClient
from monitor_model.risk_agent import RiskAgent
from remediation.orchestrator import RemediationOrchestrator
from shared.schemas import BreakerEventSchema, SpanSchema
from tests.conftest import FakeRedisStore


class TestRemediationRecovery:
    def test_recovers_within_five_calls(self) -> None:
        """
        Simulate AutoGPT loop → breaker trip → remediation → recovery
        with ≤5 post-remediation tool calls.
        """
        store = FakeRedisStore()
        swarm = DetectorSwarm()
        gemini = MagicMock(spec=GeminiClient)
        gemini.available = False
        gemini.classify.return_value = None
        risk_agent = RiskAgent(gemini=gemini)
        breaker_agent = CircuitBreakerAgent(store, threshold=0.8)
        orchestrator = RemediationOrchestrator(store)

        session_id = "autogpt-demo"
        loop_params = {"query": "server status"}
        store.save_checkpoint(
            session_id,
            {"tool_name": "web_search", "params": loop_params, "step": 2},
        )

        # Phase A: infinite loop — 3 identical calls trip the breaker
        for i in range(3):
            vector = swarm.process(
                SpanSchema(
                    trace_id="t1",
                    span_id=f"loop-{i}",
                    session_id=session_id,
                    tool_name="web_search",
                    params=loop_params,
                    token_count=50 * (i + 1),
                    latency_ms=200,
                    state_hash="stuck",
                )
            )
            risk = risk_agent.assess_vector(vector)
            breaker_event = breaker_agent.process_assessment(risk)

        assert breaker_event.state == BreakerState.OPEN.value
        assert breaker_event.allowed is False

        # Phase B: remediation resets breaker
        plan = orchestrator.handle_breaker_event(
            BreakerEventSchema(
                session_id=session_id,
                state=breaker_event.state,
                previous_state=breaker_event.previous_state,
                risk_score=breaker_event.risk_score,
                allowed=breaker_event.allowed,
                reason=breaker_event.reason,
            )
        )
        assert plan is not None
        assert plan.recovered is True
        assert breaker_agent.get_state(session_id) == BreakerState.CLOSED

        # Phase C: agent resumes with varied calls — must stay healthy within 5 calls
        recovery_calls = 0
        alternate_params = [
            {"query": "alternative approach"},
            {"query": "read docs"},
            {"query": "check logs"},
            {"query": "summarize"},
            {"query": "finalize"},
        ]
        swarm.reset()
        for i, params in enumerate(alternate_params):
            recovery_calls += 1
            vector = swarm.process(
                SpanSchema(
                    trace_id="t2",
                    span_id=f"recovery-{i}",
                    session_id=session_id,
                    tool_name="read_file",
                    params=params,
                    token_count=100,
                    latency_ms=150,
                    state_hash=f"state-{i}",
                )
            )
            risk = risk_agent.assess_vector(vector)
            event = breaker_agent.process_assessment(risk)
            if event.state == BreakerState.CLOSED.value and risk.risk_score <= 0.8:
                break

        assert recovery_calls <= 5
        assert breaker_agent.get_state(session_id) == BreakerState.CLOSED
        assert breaker_agent.is_allowed(session_id) is True
