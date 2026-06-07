"""Error rate tracking per session."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorResult:
    error_score: float
    error_count: int
    total_spans: int


class ErrorAgent:
    """
    Tracks error spans and computes a rolling error rate.
    error_score is the fraction of spans with status=error in the session.
    """

    def __init__(self) -> None:
        self._error_counts: dict[str, int] = {}
        self._span_counts: dict[str, int] = {}

    def observe(self, session_id: str, status: str = "ok") -> ErrorResult:
        self._span_counts[session_id] = self._span_counts.get(session_id, 0) + 1
        if status == "error":
            self._error_counts[session_id] = self._error_counts.get(session_id, 0) + 1

        total = self._span_counts[session_id]
        errors = self._error_counts.get(session_id, 0)
        score = errors / total if total else 0.0

        return ErrorResult(error_score=score, error_count=errors, total_spans=total)

    def reset(self, session_id: str | None = None) -> None:
        if session_id:
            self._error_counts.pop(session_id, None)
            self._span_counts.pop(session_id, None)
        else:
            self._error_counts.clear()
            self._span_counts.clear()
