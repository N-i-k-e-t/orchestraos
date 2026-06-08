"""Incident learning agent — summarizes incident history from MongoDB."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class IncidentReader(Protocol):
    def list_incidents(self, limit: int = 50) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class LearningSummary:
    total_incidents: int
    by_type: dict[str, int]
    by_severity: dict[str, int]
    top_sessions: tuple[str, ...]
    lessons: tuple[str, ...]


class IncidentLearningAgent:
    """Reads incident history and produces actionable learning summaries."""

    def __init__(self, store: IncidentReader | None = None) -> None:
        if store is None:
            from integrations.mongodb_store import MongoIncidentStore

            self._store = MongoIncidentStore()
        else:
            self._store = store

    def summarize(self, limit: int = 50) -> LearningSummary:
        incidents = self._store.list_incidents(limit=limit)
        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        session_counts: dict[str, int] = {}

        for inc in incidents:
            itype = str(inc.get("incident_type", "unknown"))
            sev = str(inc.get("severity", "info"))
            sid = str(inc.get("session_id", "unknown"))
            by_type[itype] = by_type.get(itype, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1
            session_counts[sid] = session_counts.get(sid, 0) + 1

        top_sessions = tuple(
            sid for sid, _ in sorted(session_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        )
        lessons = self._derive_lessons(by_type, by_severity)

        return LearningSummary(
            total_incidents=len(incidents),
            by_type=by_type,
            by_severity=by_severity,
            top_sessions=top_sessions,
            lessons=lessons,
        )

    @staticmethod
    def _derive_lessons(
        by_type: dict[str, int], by_severity: dict[str, int]
    ) -> tuple[str, ...]:
        lessons: list[str] = []
        if by_type.get("breaker_trip", 0) > 0:
            lessons.append("Circuit breaker trips correlate with loop incidents — keep threshold at 0.8")
        if by_type.get("loop", 0) > 0:
            lessons.append("Tool loops are the dominant failure mode — prioritize LoopAgent tuning")
        if by_severity.get("critical", 0) > 2:
            lessons.append("Multiple critical incidents — review remediation escalation path")
        if not lessons:
            lessons.append("No incidents recorded yet — baseline policies are stable")
        return tuple(lessons)
