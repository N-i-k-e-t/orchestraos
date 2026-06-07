"""Unit tests for ContextAgent."""

from detectors.context_agent import ContextAgent


class TestContextAgent:
    def setup_method(self) -> None:
        self.agent = ContextAgent()

    def test_unchanged_state_raises_score(self) -> None:
        self.agent.observe("s1", "hash-a")
        self.agent.observe("s1", "hash-a")
        r = self.agent.observe("s1", "hash-a")
        assert r.context_score > 0.5
        assert r.state_changed is False

    def test_changed_state_resets(self) -> None:
        self.agent.observe("s1", "hash-a")
        r = self.agent.observe("s1", "hash-b")
        assert r.state_changed is True
        assert r.context_score == 0.0
