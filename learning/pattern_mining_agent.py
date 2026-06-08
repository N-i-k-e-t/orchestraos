"""Pattern mining agent — finds recurring incident patterns in MongoDB history."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Protocol


class IncidentReader(Protocol):
    def list_incidents(self, limit: int = 50) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class PatternResult:
    patterns: tuple[tuple[str, int], ...]
    dominant_pattern: str | None
    repeat_session_ratio: float


class PatternMiningAgent:
    """Mines incident history for recurring type+severity patterns."""

    def __init__(self, store: IncidentReader | None = None) -> None:
        if store is None:
            from integrations.mongodb_store import MongoIncidentStore

            self._store = MongoIncidentStore()
        else:
            self._store = store

    def mine(self, limit: int = 100) -> PatternResult:
        incidents = self._store.list_incidents(limit=limit)
        if not incidents:
            return PatternResult(patterns=(), dominant_pattern=None, repeat_session_ratio=0.0)

        pattern_counter: Counter[str] = Counter()
        sessions: set[str] = set()
        repeat_sessions = 0

        for inc in incidents:
            key = f"{inc.get('incident_type', 'unknown')}:{inc.get('severity', 'info')}"
            pattern_counter[key] += 1
            sid = str(inc.get("session_id", ""))
            if sid in sessions:
                repeat_sessions += 1
            sessions.add(sid)

        patterns = tuple(pattern_counter.most_common(5))
        dominant = patterns[0][0] if patterns else None
        ratio = repeat_sessions / max(1, len(incidents))

        return PatternResult(
            patterns=patterns,
            dominant_pattern=dominant,
            repeat_session_ratio=round(ratio, 4),
        )
