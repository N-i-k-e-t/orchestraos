"""Policy optimization agent — recommends threshold tweaks from incident history."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class IncidentReader(Protocol):
    def list_incidents(self, limit: int = 50) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class PolicyRecommendation:
    breaker_threshold: float
    loop_threshold: int
    rationale: str
    confidence: float


class PolicyOptimizationAgent:
    """Suggests policy adjustments based on historical breaker and loop incidents."""

    DEFAULT_BREAKER = 0.8
    DEFAULT_LOOP = 3

    def __init__(self, store: IncidentReader | None = None) -> None:
        if store is None:
            from integrations.mongodb_store import MongoIncidentStore

            self._store = MongoIncidentStore()
        else:
            self._store = store

    def recommend(self, limit: int = 50) -> PolicyRecommendation:
        incidents = self._store.list_incidents(limit=limit)
        breaker_trips = sum(1 for i in incidents if i.get("incident_type") == "breaker_trip")
        loops = sum(1 for i in incidents if i.get("incident_type") == "loop")
        total = len(incidents)

        if total == 0:
            return PolicyRecommendation(
                breaker_threshold=self.DEFAULT_BREAKER,
                loop_threshold=self.DEFAULT_LOOP,
                rationale="No history — keep hackathon defaults",
                confidence=0.5,
            )

        trip_ratio = breaker_trips / total
        loop_ratio = loops / total

        threshold = self.DEFAULT_BREAKER
        loop_th = self.DEFAULT_LOOP
        rationale_parts: list[str] = []

        if trip_ratio > 0.4:
            threshold = min(0.9, threshold + 0.05)
            rationale_parts.append("Frequent breaker trips — slightly raise threshold")
        elif trip_ratio < 0.1 and loop_ratio > 0.3:
            threshold = max(0.7, threshold - 0.05)
            rationale_parts.append("Loops without trips — lower threshold for faster protection")

        if loop_ratio > 0.5:
            loop_th = max(2, self.DEFAULT_LOOP - 1)
            rationale_parts.append("High loop rate — detect loops one call earlier")

        confidence = min(0.95, 0.5 + total * 0.02)
        rationale = "; ".join(rationale_parts) if rationale_parts else "Current policies match incident profile"

        return PolicyRecommendation(
            breaker_threshold=round(threshold, 2),
            loop_threshold=loop_th,
            rationale=rationale,
            confidence=round(confidence, 4),
        )
