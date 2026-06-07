"""Unit tests for ErrorAgent."""

from detectors.error_agent import ErrorAgent


class TestErrorAgent:
    def setup_method(self) -> None:
        self.agent = ErrorAgent()

    def test_no_errors_zero_score(self) -> None:
        r = self.agent.observe("s1", "ok")
        assert r.error_score == 0.0

    def test_error_rate_computed(self) -> None:
        self.agent.observe("s1", "ok")
        self.agent.observe("s1", "ok")
        r = self.agent.observe("s1", "error")
        assert abs(r.error_score - 1 / 3) < 0.01
