"""Context stagnation detection via state hash tracking."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextResult:
    context_score: float
    unchanged_steps: int
    state_changed: bool


class ContextAgent:
    """
    Detects context stagnation when agent state hash stops changing.
    context_score rises toward 1.0 as the same state persists.
    """

    STAGNATION_THRESHOLD = 3

    def __init__(self) -> None:
        self._last_hash: dict[str, str | None] = {}
        self._unchanged: dict[str, int] = {}

    def observe(self, session_id: str, state_hash: str | None) -> ContextResult:
        prev = self._last_hash.get(session_id)
        changed = state_hash is not None and state_hash != prev

        if changed or state_hash is None:
            self._unchanged[session_id] = 0
        else:
            self._unchanged[session_id] = self._unchanged.get(session_id, 0) + 1

        if state_hash is not None:
            self._last_hash[session_id] = state_hash

        steps = self._unchanged.get(session_id, 0)
        score = min(1.0, steps / self.STAGNATION_THRESHOLD)

        return ContextResult(context_score=score, unchanged_steps=steps, state_changed=changed)

    def reset(self, session_id: str | None = None) -> None:
        if session_id:
            self._last_hash.pop(session_id, None)
            self._unchanged.pop(session_id, None)
        else:
            self._last_hash.clear()
            self._unchanged.clear()
