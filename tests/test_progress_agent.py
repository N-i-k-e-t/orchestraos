"""Unit tests for ProgressAgent."""

from detectors.progress_agent import ProgressAgent


class TestProgressAgent:
    def setup_method(self) -> None:
        self.agent = ProgressAgent()

    def test_progress_on_token_increase(self) -> None:
        result = self.agent.observe("sess-1", token_count=100, state_hash="abc")
        assert result.token_delta == 100
        assert result.progress_score > 0.0

    def test_stagnation_lowers_score(self) -> None:
        self.agent.observe("sess-1", token_count=100, state_hash="abc")
        r1 = self.agent.observe("sess-1", token_count=100, state_hash="abc")
        r2 = self.agent.observe("sess-1", token_count=100, state_hash="abc")
        assert r2.progress_score <= r1.progress_score

    def test_state_change_contributes(self) -> None:
        r = self.agent.observe("sess-1", token_count=50, state_hash="new-state")
        assert r.state_changed is True
        assert r.progress_score > 0.0

    def test_score_bounded_0_to_1(self) -> None:
        for i in range(20):
            r = self.agent.observe("sess-1", token_count=i * 10, state_hash=f"h-{i}")
            assert 0.0 <= r.progress_score <= 1.0

    def test_reset_session(self) -> None:
        self.agent.observe("sess-1", token_count=100)
        self.agent.reset("sess-1")
        r = self.agent.observe("sess-1", token_count=100)
        assert r.token_delta == 100
