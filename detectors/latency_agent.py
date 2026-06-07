"""Latency anomaly detection per session."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LatencyResult:
    latency_score: float
    latency_ms: float
    avg_latency_ms: float


class LatencyAgent:
    """
    Scores span latency against a threshold and session rolling average.
    Higher latency_score indicates slower / degraded performance.
    """

    DEFAULT_THRESHOLD_MS = 5_000.0

    def __init__(self, threshold_ms: float = DEFAULT_THRESHOLD_MS) -> None:
        self._threshold_ms = threshold_ms
        self._session_latencies: dict[str, list[float]] = {}

    def observe(self, session_id: str, latency_ms: float) -> LatencyResult:
        history = self._session_latencies.setdefault(session_id, [])
        history.append(latency_ms)
        avg = sum(history) / len(history)

        instant = min(1.0, max(0.0, latency_ms / self._threshold_ms))
        rolling = min(1.0, max(0.0, avg / self._threshold_ms))
        score = 0.6 * instant + 0.4 * rolling

        return LatencyResult(latency_score=score, latency_ms=latency_ms, avg_latency_ms=avg)

    def reset(self, session_id: str | None = None) -> None:
        if session_id:
            self._session_latencies.pop(session_id, None)
        else:
            self._session_latencies.clear()
