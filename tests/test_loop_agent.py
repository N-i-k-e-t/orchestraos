"""Unit tests for LoopAgent."""

from detectors.loop_agent import LoopAgent


class TestLoopAgent:
    def setup_method(self) -> None:
        self.agent = LoopAgent()

    def test_no_loop_on_first_call(self) -> None:
        result = self.agent.observe("sess-1", "search", {"q": "hello"})
        assert result.loop_detected is False
        assert result.repeat_count == 1
        assert result.loop_score == 0.0

    def test_loop_detected_on_third_repetition(self) -> None:
        params = {"q": "hello"}
        for _ in range(2):
            self.agent.observe("sess-1", "search", params)
        result = self.agent.observe("sess-1", "search", params)
        assert result.loop_detected is True
        assert result.repeat_count == 3
        assert result.loop_score == 1.0

    def test_different_params_different_fingerprint(self) -> None:
        r1 = self.agent.observe("sess-1", "search", {"q": "a"})
        r2 = self.agent.observe("sess-1", "search", {"q": "b"})
        assert r1.fingerprint != r2.fingerprint

    def test_fingerprint_is_deterministic(self) -> None:
        fp1 = LoopAgent.fingerprint("s", "tool", {"b": 2, "a": 1})
        fp2 = LoopAgent.fingerprint("s", "tool", {"a": 1, "b": 2})
        assert fp1 == fp2

    def test_reset_clears_counts(self) -> None:
        self.agent.observe("sess-1", "search", {"q": "x"})
        self.agent.reset()
        result = self.agent.observe("sess-1", "search", {"q": "x"})
        assert result.repeat_count == 1
