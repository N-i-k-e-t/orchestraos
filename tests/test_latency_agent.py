"""Unit tests for LatencyAgent."""

from detectors.latency_agent import LatencyAgent


class TestLatencyAgent:
    def setup_method(self) -> None:
        self.agent = LatencyAgent(threshold_ms=1000.0)

    def test_low_latency_low_score(self) -> None:
        r = self.agent.observe("s1", 100.0)
        assert r.latency_score < 0.2

    def test_high_latency_high_score(self) -> None:
        r = self.agent.observe("s1", 5000.0)
        assert r.latency_score > 0.8
