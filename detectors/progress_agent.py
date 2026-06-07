"""Progress measurement for agent sessions."""

from dataclasses import dataclass


@dataclass
class ProgressResult:
    progress_score: float
    token_delta: int
    state_changed: bool
    total_tokens: int


@dataclass
class _SessionState:
    last_token_count: int = 0
    last_state_hash: str | None = None
    stagnant_steps: int = 0


class ProgressAgent:
    """
    Measures whether an agent session is making forward progress.

    progress_score ranges 0–1 where lower values indicate stagnation.
    Considers token usage deltas and agent state changes.
    """

    STAGNANT_PENALTY = 0.25

    def __init__(self) -> None:
        self._sessions: dict[str, _SessionState] = {}

    def observe(
        self,
        session_id: str,
        token_count: int,
        state_hash: str | None = None,
    ) -> ProgressResult:
        state = self._sessions.setdefault(session_id, _SessionState())

        token_delta = max(0, token_count - state.last_token_count)
        state_changed = state_hash is not None and state_hash != state.last_state_hash

        if token_delta == 0 and not state_changed:
            state.stagnant_steps += 1
        else:
            state.stagnant_steps = 0

        state.last_token_count = token_count
        if state_hash is not None:
            state.last_state_hash = state_hash

        # Base score: reward token usage and state changes
        token_component = min(1.0, token_delta / 100.0) if token_delta > 0 else 0.0
        state_component = 1.0 if state_changed else 0.0
        raw_score = 0.6 * token_component + 0.4 * state_component

        # Penalize consecutive stagnant steps
        penalty = min(1.0, state.stagnant_steps * self.STAGNANT_PENALTY)
        progress_score = max(0.0, min(1.0, raw_score - penalty))

        return ProgressResult(
            progress_score=progress_score,
            token_delta=token_delta,
            state_changed=state_changed,
            total_tokens=token_count,
        )

    def reset(self, session_id: str | None = None) -> None:
        if session_id:
            self._sessions.pop(session_id, None)
        else:
            self._sessions.clear()
