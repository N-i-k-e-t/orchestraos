"""Unit tests for TokenAgent."""

from detectors.token_agent import TokenAgent


class TestTokenAgent:
    def setup_method(self) -> None:
        self.agent = TokenAgent(budget=1000)

    def test_zero_on_first_small_span(self) -> None:
        r = self.agent.observe("s1", 50)
        assert r.session_tokens == 50
        assert r.token_score == 0.05

    def test_approaches_one_at_budget(self) -> None:
        self.agent.observe("s1", 900)
        r = self.agent.observe("s1", 100)
        assert r.token_score == 1.0
