"""Loop detection via O(1) fingerprint counting."""

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LoopResult:
    loop_detected: bool
    repeat_count: int
    fingerprint: str
    loop_score: float


class LoopAgent:
    """
    Detects repeated tool calls within a session.

    Fingerprints are built from session_id + tool_name + sorted params.
    A loop is flagged on the third identical repetition (repeat_count >= 3).
    Counting is O(1) per call via a hash map keyed by fingerprint.
    """

    LOOP_THRESHOLD = 3

    def __init__(self) -> None:
        # fingerprint -> repeat count
        self._counts: dict[str, int] = {}

    @staticmethod
    def fingerprint(session_id: str, tool_name: str, params: dict[str, Any]) -> str:
        """Deterministic hash of session, tool, and sorted parameters."""
        canonical = json.dumps(
            {"session_id": session_id, "tool_name": tool_name, "params": params},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    def observe(self, session_id: str, tool_name: str, params: dict[str, Any]) -> LoopResult:
        """Record a tool call and return loop detection result."""
        fp = self.fingerprint(session_id, tool_name, params)
        count = self._counts.get(fp, 0) + 1
        self._counts[fp] = count

        loop_detected = count >= self.LOOP_THRESHOLD
        # Score ramps from 0 at first call to 1.0 at threshold and beyond
        loop_score = min(1.0, max(0.0, (count - 1) / (self.LOOP_THRESHOLD - 1)))

        return LoopResult(
            loop_detected=loop_detected,
            repeat_count=count,
            fingerprint=fp,
            loop_score=loop_score,
        )

    def reset(self) -> None:
        """Clear all fingerprint counts."""
        self._counts.clear()
