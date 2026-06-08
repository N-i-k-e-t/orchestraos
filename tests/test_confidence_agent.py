"""ConfidenceAgent tests."""

from monitor_model.confidence_agent import ConfidenceAgent
from monitor_model.grounding_agent import GroundingAgent, GroundingResult


class TestConfidenceAgent:
    def setup_method(self) -> None:
        self.agent = ConfidenceAgent()

    def test_higher_confidence_with_gemini(self) -> None:
        grounding = GroundingResult(grounded=True, grounding_score=0.8, violations=())
        result = self.agent.calibrate(0.7, grounding, gemini_used=True)
        assert result.confidence >= 0.8
        assert result.calibrated_risk == 0.7

    def test_nudges_risk_when_ungrounded(self) -> None:
        grounding = GroundingAgent().assess({"loop_score": 0.1}, loop_detected=True)
        result = self.agent.calibrate(0.5, grounding, gemini_used=False)
        assert result.calibrated_risk >= 0.5
