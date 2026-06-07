"""Phase 5 remediation orchestrator tests."""

from breaker.circuit_breaker import BreakerState, CircuitBreaker
from remediation.agents import RemediationAction
from remediation.orchestrator import RemediationOrchestrator
from shared.schemas import BreakerEventSchema
from tests.conftest import FakeRedisStore


class TestRemediationOrchestrator:
    def setup_method(self) -> None:
        self.store = FakeRedisStore()
        self.orchestrator = RemediationOrchestrator(self.store)

    def _open_event(self, session_id: str = "autogpt-demo") -> BreakerEventSchema:
        return BreakerEventSchema(
            session_id=session_id,
            state=BreakerState.OPEN.value,
            previous_state=BreakerState.CLOSED.value,
            risk_score=0.85,
            allowed=False,
            reason="repeated tool loop detected",
        )

    def test_ignores_closed_breaker(self) -> None:
        event = BreakerEventSchema(
            session_id="s1",
            state=BreakerState.CLOSED.value,
            risk_score=0.1,
            allowed=True,
        )
        assert self.orchestrator.handle_breaker_event(event) is None

    def test_runs_full_chain_on_open(self) -> None:
        self.store.save_checkpoint(
            "autogpt-demo",
            {"tool_name": "web_search", "params": {"q": "status"}},
        )
        self.store.store_breaker_state(
            "autogpt-demo",
            {"state": BreakerState.OPEN.value, "tripped_at": 0},
        )

        plan = self.orchestrator.handle_breaker_event(self._open_event())
        assert plan is not None
        assert plan.recovered is True
        assert plan.status == "recovered"
        assert plan.total_steps == 4
        actions = [s["action"] for s in plan.steps]
        assert actions == [
            RemediationAction.RETRY.value,
            RemediationAction.REWRITE_PROMPT.value,
            RemediationAction.ROLLBACK.value,
            RemediationAction.FALLBACK_TOOL.value,
        ]

    def test_resets_breaker_on_recovery(self) -> None:
        self.store.save_checkpoint("autogpt-demo", {"tool_name": "check_status", "params": {}})
        self.store.store_breaker_state(
            "autogpt-demo",
            {"state": BreakerState.OPEN.value, "tripped_at": 0},
        )
        self.orchestrator.handle_breaker_event(self._open_event())
        breaker = CircuitBreaker(self.store, "autogpt-demo")
        assert breaker.state == BreakerState.CLOSED

    def test_escalates_after_max_attempts(self) -> None:
        self.store.save_checkpoint("autogpt-demo", {"tool_name": "web_search", "params": {}})
        for _ in range(RemediationOrchestrator.MAX_RECOVERY_CALLS):
            self.orchestrator.handle_breaker_event(self._open_event())
        plan = self.orchestrator.handle_breaker_event(self._open_event())
        assert plan is not None
        assert plan.status == "escalated"
        assert plan.steps[-1]["action"] == RemediationAction.ESCALATE.value
