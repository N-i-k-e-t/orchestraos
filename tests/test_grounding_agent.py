"""GroundingAgent tests."""

from monitor_model.grounding_agent import GroundingAgent


class TestGroundingAgent:
    def setup_method(self) -> None:
        self.agent = GroundingAgent()

    def test_grounded_when_features_complete(self) -> None:
        features = {
            "loop_score": 1.0,
            "progress_score": 0.1,
            "latency_score": 0.1,
            "token_score": 0.1,
            "context_score": 0.5,
            "error_score": 0.0,
        }
        result = self.agent.assess(features, loop_detected=True, repeat_count=3)
        assert result.grounded is True
        assert result.grounding_score >= 0.6

    def test_not_grounded_when_loop_flag_mismatch(self) -> None:
        features = {k: 0.1 for k in GroundingAgent.REQUIRED_FEATURES}
        result = self.agent.assess(features, loop_detected=True, repeat_count=5)
        assert result.grounded is False
        assert "loop_flag_without_loop_score" in result.violations
