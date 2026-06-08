"""Phase 3 RiskAgent tests."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from detectors.swarm import DetectorSwarm
from monitor_model.gemini_client import GeminiClient
from monitor_model.risk_agent import RiskAgent
from shared.schemas import FeatureVectorSchema, RiskLevel, SpanSchema


def _loop_features(loop_score: float = 1.0, progress: float = 0.0) -> dict[str, float]:
    return {
        "loop_score": loop_score,
        "progress_score": progress,
        "latency_score": 0.04,
        "token_score": 0.015,
        "context_score": 0.67,
        "error_score": 0.0,
    }


class TestRiskAgent:
    def setup_method(self) -> None:
        gemini = MagicMock(spec=GeminiClient)
        gemini.available = False
        gemini.classify.return_value = None
        self.agent = RiskAgent(gemini=gemini)

    def test_loop_scenario_risk_score_exceeds_threshold(self) -> None:
        """DoD: risk_score > 0.8 when loop is detected."""
        risk = self.agent.assess(
            "autogpt-demo",
            _loop_features(),
            loop_detected=True,
            repeat_count=3,
        )
        assert risk.risk_score > 0.8
        assert risk.status == RiskLevel.CRITICAL

    def test_healthy_session_low_score(self) -> None:
        features = {
            "loop_score": 0.0,
            "progress_score": 0.9,
            "latency_score": 0.05,
            "token_score": 0.01,
            "context_score": 0.0,
            "error_score": 0.0,
        }
        risk = self.agent.assess("sess-ok", features)
        assert risk.risk_score < 0.4
        assert risk.status == RiskLevel.HEALTHY

    def test_output_has_status_reason_and_score(self) -> None:
        risk = self.agent.assess("sess-1", _loop_features(), loop_detected=True)
        assert risk.status.value in ("healthy", "warning", "critical")
        assert risk.reason
        assert 0.0 <= risk.risk_score <= 1.0

    def test_gemini_primary_when_available(self) -> None:
        gemini = MagicMock(spec=GeminiClient)
        gemini.available = True
        gemini.backend = "api_key"
        gemini.classify.return_value = {
            "status": RiskLevel.CRITICAL,
            "risk_score": 0.95,
            "reason": "Gemini: infinite tool loop detected",
        }
        agent = RiskAgent(gemini=gemini)
        risk = agent.assess("sess-1", _loop_features(loop_score=0.5), loop_detected=True)
        assert agent.last_source == "gemini:api_key"
        assert risk.risk_score >= 0.85
        assert "gemini:api_key" in risk.reason
        gemini.classify.assert_called_once()

    def test_deterministic_fallback_when_gemini_unavailable(self) -> None:
        gemini = MagicMock(spec=GeminiClient)
        gemini.available = False
        gemini.backend = "none"
        gemini.classify.return_value = None
        agent = RiskAgent(gemini=gemini)
        risk = agent.assess("sess-1", _loop_features(), loop_detected=True)
        assert agent.last_source == "deterministic_fallback"
        assert "deterministic" in risk.reason.lower()
        gemini.classify.assert_not_called()

    def test_assess_vector_from_swarm(self) -> None:
        swarm = DetectorSwarm()
        params = {"query": "server status"}
        vector = None
        for i in range(3):
            vector = swarm.process(
                SpanSchema(
                    trace_id="t1",
                    span_id=f"s{i}",
                    session_id="autogpt",
                    tool_name="web_search",
                    params=params,
                    token_count=50,
                    latency_ms=200,
                    state_hash="fixed",
                )
            )
        assert vector is not None
        risk = self.agent.assess_vector(vector)
        assert risk.risk_score > 0.8
        assert risk.status == RiskLevel.CRITICAL


class TestGeminiClientParse:
    def test_parse_json_response(self) -> None:
        text = '{"status":"critical","risk_score":0.91,"reason":"Loop detected"}'
        result = GeminiClient._parse_response(text)
        assert result["status"] == RiskLevel.CRITICAL
        assert result["risk_score"] == pytest.approx(0.91)
