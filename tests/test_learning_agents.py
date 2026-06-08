"""Learning domain agent tests."""

from learning.incident_learning_agent import IncidentLearningAgent
from learning.pattern_mining_agent import PatternMiningAgent
from learning.policy_optimization_agent import PolicyOptimizationAgent


class FakeIncidentStore:
    def list_incidents(self, limit: int = 50) -> list[dict]:
        return [
            {"incident_type": "loop", "severity": "critical", "session_id": "s1"},
            {"incident_type": "breaker_trip", "severity": "critical", "session_id": "s1"},
            {"incident_type": "loop", "severity": "warning", "session_id": "s2"},
            {"incident_type": "remediation", "severity": "info", "session_id": "s3"},
        ][:limit]


class TestIncidentLearningAgent:
    def test_summarize_incidents(self) -> None:
        agent = IncidentLearningAgent(store=FakeIncidentStore())
        summary = agent.summarize()
        assert summary.total_incidents == 4
        assert summary.by_type["loop"] == 2
        assert len(summary.lessons) >= 1


class TestPatternMiningAgent:
    def test_mine_patterns(self) -> None:
        agent = PatternMiningAgent(store=FakeIncidentStore())
        result = agent.mine()
        assert result.dominant_pattern is not None
        assert len(result.patterns) >= 1


class TestPolicyOptimizationAgent:
    def test_recommend_policy(self) -> None:
        agent = PolicyOptimizationAgent(store=FakeIncidentStore())
        rec = agent.recommend()
        assert 0.7 <= rec.breaker_threshold <= 0.9
        assert rec.loop_threshold >= 2
        assert rec.rationale

    def test_defaults_without_history(self) -> None:
        class EmptyStore:
            def list_incidents(self, limit: int = 50) -> list:
                return []

        agent = PolicyOptimizationAgent(store=EmptyStore())
        rec = agent.recommend()
        assert rec.breaker_threshold == 0.8
