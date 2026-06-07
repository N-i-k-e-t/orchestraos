"""Phase 2 detector swarm tests."""

from datetime import datetime, timezone

from detectors.swarm import DetectorSwarm
from shared.schemas import SpanSchema


def _make_span(
    session_id: str = "autogpt-demo",
    tool_name: str = "web_search",
    params: dict | None = None,
    span_id: str = "s1",
    token_count: int = 50,
    state_hash: str = "state-v1",
    status: str = "ok",
) -> SpanSchema:
    return SpanSchema(
        trace_id="trace-1",
        span_id=span_id,
        session_id=session_id,
        tool_name=tool_name,
        params=params or {"query": "server status"},
        token_count=token_count,
        latency_ms=200.0,
        state_hash=state_hash,
        status=status,
        timestamp=datetime.now(timezone.utc),
    )


class TestDetectorSwarm:
    def setup_method(self) -> None:
        self.swarm = DetectorSwarm()

    def test_autogpt_infinite_loop_loop_score_exceeds_threshold(self) -> None:
        """DoD: loop_score > 0.8 on the third identical AutoGPT tool call."""
        params = {"query": "server status", "target": "localhost"}
        result = None
        for i in range(3):
            result = self.swarm.process(
                _make_span(span_id=f"s{i}", params=params, token_count=50 * (i + 1))
            )
        assert result is not None
        assert result.loop_detected is True
        assert result.features["loop_score"] > 0.8

    def test_feature_vector_has_all_six_scores(self) -> None:
        fv = self.swarm.process(_make_span())
        expected_keys = {
            "loop_score",
            "progress_score",
            "latency_score",
            "token_score",
            "context_score",
            "error_score",
        }
        assert expected_keys == set(fv.features.keys())

    def test_no_loop_on_first_call(self) -> None:
        fv = self.swarm.process(_make_span())
        assert fv.loop_detected is False
        assert fv.features["loop_score"] == 0.0

    def test_error_span_raises_error_score(self) -> None:
        self.swarm.process(_make_span(span_id="ok-1", status="ok"))
        fv = self.swarm.process(
            SpanSchema(
                trace_id="t1",
                span_id="err-1",
                session_id="autogpt-demo",
                tool_name="web_search",
                params={"query": "fail"},
                status="error",
                error_message="timeout",
            )
        )
        assert fv.features["error_score"] == 0.5
