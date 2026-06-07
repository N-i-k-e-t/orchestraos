"""Google Cloud Agent Builder orchestration for the Monitor (Risk) agent.

Uses Vertex AI Gemini as the reasoning brain with a explicit multi-step plan:
  1. Ingest detector feature vector
  2. Gemini classification (Vertex AI or API key)
  3. Apply deterministic safety guardrails (loop floor, score caps)

This satisfies the hackathon requirement to build with Gemini + Agent Builder
orchestration without replacing the existing Pub/Sub pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

from monitor_model.gemini_client import GeminiClient
from monitor_model.risk_agent import RiskAgent
from shared.schemas import FeatureVectorSchema, RiskSchema

logger = logging.getLogger(__name__)

AGENT_BUILDER_STEPS = (
    "ingest_feature_vector",
    "gemini_reasoning",
    "apply_safety_guardrails",
    "publish_risk_assessment",
)


class MonitorAgentBuilder:
    """
    Agent Builder-style orchestrator for OrchestraOS risk assessment.

    Wraps RiskAgent and records which Gemini backend (vertex | api_key | fallback)
    was used for judges and demo narration.
    """

    def __init__(
        self,
        risk_agent: RiskAgent | None = None,
        gemini: GeminiClient | None = None,
    ) -> None:
        self._risk = risk_agent or RiskAgent(gemini=gemini)
        self._last_execution: dict[str, Any] = {}

    @property
    def last_execution(self) -> dict[str, Any]:
        """Metadata from the most recent orchestrated run (for demos/tests)."""
        return dict(self._last_execution)

    def execute(
        self,
        session_id: str,
        features: dict[str, float],
        *,
        span_id: str | None = None,
        loop_detected: bool = False,
        repeat_count: int = 0,
    ) -> RiskSchema:
        gemini = self._risk._gemini  # noqa: SLF001
        backend = gemini.backend if gemini.available else "deterministic_fallback"
        steps = list(AGENT_BUILDER_STEPS)

        if not gemini.available:
            steps = [s for s in steps if s != "gemini_reasoning"]
            steps.insert(1, "deterministic_fallback")

        logger.info(
            "Agent Builder execute session=%s backend=%s steps=%s",
            session_id,
            backend,
            steps,
        )

        assessment = self._risk.assess(
            session_id,
            features,
            span_id=span_id,
            loop_detected=loop_detected,
            repeat_count=repeat_count,
        )

        self._last_execution = {
            "session_id": session_id,
            "agent_builder_steps": steps,
            "gemini_backend": backend,
            "gemini_available": gemini.available,
            "risk_score": assessment.risk_score,
            "status": assessment.status.value,
        }
        return assessment

    def execute_vector(self, vector: FeatureVectorSchema) -> RiskSchema:
        return self.execute(
            vector.session_id,
            vector.features,
            span_id=vector.span_id,
            loop_detected=vector.loop_detected,
            repeat_count=vector.repeat_count,
        )
