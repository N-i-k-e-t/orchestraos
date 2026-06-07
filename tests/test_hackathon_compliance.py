"""Agent Builder and Phoenix MCP tests."""

from unittest.mock import MagicMock, patch

import pytest

from integrations.phoenix_mcp import PhoenixMcpClient
from monitor_model.agent_builder import MonitorAgentBuilder, AGENT_BUILDER_STEPS
from monitor_model.gemini_client import GeminiClient
from monitor_model.risk_agent import RiskAgent
from shared.schemas import RiskLevel


class TestMonitorAgentBuilder:
    def test_execute_records_steps_with_gemini(self) -> None:
        gemini = MagicMock(spec=GeminiClient)
        gemini.available = True
        gemini.backend = "vertex"
        gemini.classify.return_value = {
            "status": RiskLevel.CRITICAL,
            "risk_score": 0.92,
            "reason": "Gemini: tool loop",
        }
        builder = MonitorAgentBuilder(risk_agent=RiskAgent(gemini=gemini))
        result = builder.execute(
            "sess-1",
            {"loop_score": 1.0, "progress_score": 0.0, "latency_score": 0.1,
             "token_score": 0.1, "context_score": 0.5, "error_score": 0.0},
            loop_detected=True,
        )
        assert result.risk_score > 0.8
        assert builder.last_execution["gemini_backend"] == "vertex"
        assert "gemini_reasoning" in builder.last_execution["agent_builder_steps"]
        assert AGENT_BUILDER_STEPS[0] == "ingest_feature_vector"

    def test_execute_fallback_without_gemini(self) -> None:
        gemini = MagicMock(spec=GeminiClient)
        gemini.available = False
        gemini.backend = "none"
        gemini.classify.return_value = None
        builder = MonitorAgentBuilder(risk_agent=RiskAgent(gemini=gemini))
        builder.execute("sess-2", {"loop_score": 0.0, "progress_score": 0.9,
                                   "latency_score": 0.0, "token_score": 0.0,
                                   "context_score": 0.0, "error_score": 0.0})
        assert "deterministic_fallback" in builder.last_execution["agent_builder_steps"]


class TestPhoenixMcpClient:
    @patch("integrations.phoenix_mcp.is_partner_enabled", return_value=True)
    @patch("integrations.phoenix_mcp.httpx.post")
    def test_mcp_tool_call(self, mock_post, _enabled) -> None:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"result": {"registered": True}}),
        )
        mock_post.return_value.raise_for_status = MagicMock()
        client = PhoenixMcpClient(mcp_url="http://phoenix:6006/mcp", phoenix_base="http://phoenix:6006")
        assert client.enabled
        ok = client.register_session("sess-1", tool_name="web_search", trace_id="trace-1")
        assert ok
        mock_post.assert_called_once()
        body = mock_post.call_args.kwargs.get("json") or mock_post.call_args[0][1]
        assert body["method"] == "tools/call"

    @patch("integrations.phoenix_mcp.is_partner_enabled", return_value=True)
    @patch("integrations.phoenix_mcp.httpx.get")
    def test_rest_fallback_when_no_mcp_url(self, mock_get, _enabled) -> None:
        mock_get.return_value = MagicMock(status_code=200)
        client = PhoenixMcpClient(mcp_url="", phoenix_base="http://phoenix:6006")
        assert client.register_session("sess-1", tool_name="search", trace_id="t1")
        mock_get.assert_called_once()
