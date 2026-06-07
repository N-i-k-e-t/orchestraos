"""Token budget tracking per session."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TokenResult:
    token_score: float
    session_tokens: int
    span_tokens: int


class TokenAgent:
    """
    Tracks cumulative token usage per session.
    token_score approaches 1.0 as the session nears its budget.
    """

    DEFAULT_BUDGET = 10_000

    def __init__(self, budget: int = DEFAULT_BUDGET) -> None:
        self._budget = budget
        self._session_totals: dict[str, int] = {}

    def observe(self, session_id: str, span_tokens: int) -> TokenResult:
        total = self._session_totals.get(session_id, 0) + span_tokens
        self._session_totals[session_id] = total
        score = min(1.0, max(0.0, total / self._budget))
        return TokenResult(token_score=score, session_tokens=total, span_tokens=span_tokens)

    def reset(self, session_id: str | None = None) -> None:
        if session_id:
            self._session_totals.pop(session_id, None)
        else:
            self._session_totals.clear()
