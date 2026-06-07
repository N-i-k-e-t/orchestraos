"""Phase 6 agent harness tests."""

from unittest.mock import MagicMock

from agent_harness.metrics import cost_reduction, estimate_unprotected
from agent_harness.protected_agent import ProtectedAgent
from agent_harness.scenario_autogpt import run_autogpt_scenario
from agent_harness.unprotected_agent import UnprotectedAgent
from monitor_model.gemini_client import GeminiClient
from monitor_model.risk_agent import RiskAgent
from tests.conftest import FakeRedisStore


class TestUnprotectedAgent:
    def test_runs_400_calls(self) -> None:
        result = UnprotectedAgent(max_iterations=400).run()
        assert result.calls == 400
        assert result.outcome == "FAILURE"
        assert result.cost_usd == 42.0
        assert all(not e["blocked"] for e in result.log)


class TestProtectedAgent:
    def setup_method(self) -> None:
        self.store = FakeRedisStore()

    def test_recovers_within_five_calls(self) -> None:
        agent = ProtectedAgent(store=self.store, emit_otel=False)  # type: ignore[arg-type]
        # Inject mock gemini via risk agent
        gemini = MagicMock(spec=GeminiClient)
        gemini.available = False
        gemini.classify.return_value = None
        agent._risk = RiskAgent(gemini=gemini)

        result = agent.run()
        assert result.calls <= 5
        assert result.outcome == "RECOVERED"
        assert result.cost_usd <= 0.36

    def test_blocks_loop_and_remediates(self) -> None:
        agent = ProtectedAgent(store=self.store, emit_otel=False)  # type: ignore[arg-type]
        gemini = MagicMock(spec=GeminiClient)
        gemini.classify.return_value = None
        agent._risk = RiskAgent(gemini=gemini)

        result = agent.run()
        blocked = [e for e in result.log if e.get("blocked")]
        assert len(blocked) >= 1
        assert any(e.get("remediation") == "recovered" for e in result.log)


class TestDemoMetrics:
    def test_cost_reduction_target(self) -> None:
        unprot = estimate_unprotected()
        # Simulate protected at target
        from agent_harness.metrics import DemoMetrics

        prot = DemoMetrics(calls=5, duration_sec=47, cost_usd=0.36, tokens=525, outcome="RECOVERED")
        reduction = cost_reduction(unprot, prot)
        assert reduction >= 99.0


class TestScenarioAutogpt:
    def test_scenario_runs_both_sides(self) -> None:
        store = FakeRedisStore()
        summary = run_autogpt_scenario(store=store)  # type: ignore[arg-type]
        assert summary["unprotected"]["calls"] == 400
        assert summary["protected"]["calls"] <= 5
        assert summary["protected"]["outcome"] == "RECOVERED"
        assert summary["cost_reduction_pct"] >= 99.0
