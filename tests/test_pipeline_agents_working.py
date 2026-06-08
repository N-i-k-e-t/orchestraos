"""Prove all fundamental agents execute in the live pipeline."""

from tests.conftest import FakeRedisStore

from checkpoint.memory_store import MemoryRedisBackend
from collector.agents import OtelParserAgent, SpanIngestAgent
from learning.coordinator import LearningCoordinator
from shared.live_state import LiveStateStore
from shared.pipeline import PipelineRunner
from shared.schemas import SpanSchema


class TestPipelineAgentsWorking:
    def test_collector_agents_ingest_span(self) -> None:
        store = FakeRedisStore()
        published: list[dict] = []

        class Pub:
            def publish(self, span: dict) -> str:
                published.append(span)
                return "msg-1"

        parser = OtelParserAgent()
        spans = parser.parse(
            {
                "trace_id": "t1",
                "span_id": "s1",
                "session_id": "sess-collector",
                "tool_name": "web_search",
                "params": {"q": "test"},
            }
        )
        ingest = SpanIngestAgent(store, Pub())
        msg_id = ingest.ingest(spans[0])
        assert msg_id == "msg-1"
        assert store.load_checkpoint("sess-collector") is not None
        assert published[0]["session_id"] == "sess-collector"

    def test_full_pipeline_fires_all_fundamental_agents(self) -> None:
        store = FakeRedisStore()
        pipeline = PipelineRunner(store)  # type: ignore[arg-type]
        params = {"query": "server status"}
        result = None
        for i in range(3):
            result = pipeline.process_span(
                SpanSchema(
                    trace_id="t1",
                    span_id=f"s{i}",
                    session_id="pipeline-test",
                    tool_name="web_search",
                    params=params,
                    token_count=50,
                    latency_ms=200,
                    state_hash="fixed",
                )
            )
        assert result is not None
        fired = set(result["agents_fired"])
        assert result["loop_detected"] is True
        assert result["risk_score"] > 0.8
        assert result["breaker_state"] == "open"

        expected = {
            "LoopAgent",
            "DetectorSwarm",
            "RiskAgent",
            "GroundingAgent",
            "ConfidenceAgent",
            "MonitorAgentBuilder",
            "CircuitBreakerAgent",
            "HealthAgent",
            "RemediationOrchestrator",
            "FallbackToolAgent",
            "IncidentLearningAgent",
            "PatternMiningAgent",
            "PolicyOptimizationAgent",
        }
        assert expected.issubset(fired), f"Missing agents: {expected - fired}"

    def test_learning_coordinator_runs_three_agents(self) -> None:
        from learning.incident_learning_agent import IncidentLearningAgent
        from learning.pattern_mining_agent import PatternMiningAgent
        from learning.policy_optimization_agent import PolicyOptimizationAgent
        from tests.test_learning_agents import FakeIncidentStore

        backend = MemoryRedisBackend()
        fake = FakeIncidentStore()
        coord = LearningCoordinator(
            store=backend,
            incident_agent=IncidentLearningAgent(store=fake),
            pattern_agent=PatternMiningAgent(store=fake),
            policy_agent=PolicyOptimizationAgent(store=fake),
        )
        out = coord.run()
        assert len(out["agents_fired"]) == 3
        assert backend.get("orch:learning:latest") is not None
