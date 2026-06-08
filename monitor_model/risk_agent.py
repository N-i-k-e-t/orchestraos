"""Risk assessment agent — Gemini Flash PRIMARY, deterministic fallback only."""

from __future__ import annotations

from monitor_model.confidence_agent import ConfidenceAgent
from monitor_model.gemini_client import GeminiClient
from monitor_model.grounding_agent import GroundingAgent
from shared.schemas import FeatureVectorSchema, RiskLevel, RiskSchema


class RiskAgent:
    """
    Evaluates a feature vector and produces {status, risk_score, reason}.

    **Primary path:** Vertex AI Gemini or API-key Gemini when configured.
    **Fallback only:** weighted deterministic rules when Gemini is unavailable.
    Loop detection applies a hard floor so risk_score exceeds 0.8 on loops.
    """

    WARNING_THRESHOLD = 0.4
    CRITICAL_THRESHOLD = 0.7
    LOOP_RISK_FLOOR = 0.85
    LOOP_SCORE_FLOOR_TRIGGER = 0.8

    WEIGHTS = {
        "loop_score": 0.40,
        "progress_score": 0.20,
        "latency_score": 0.10,
        "token_score": 0.10,
        "context_score": 0.10,
        "error_score": 0.10,
    }

    def __init__(
        self,
        gemini: GeminiClient | None = None,
        grounding: GroundingAgent | None = None,
        confidence: ConfidenceAgent | None = None,
    ) -> None:
        self._gemini = gemini if gemini is not None else GeminiClient()
        self._grounding = grounding or GroundingAgent()
        self._confidence = confidence or ConfidenceAgent()
        self.last_source: str = "deterministic_fallback"

    def assess(
        self,
        session_id: str,
        features: dict[str, float],
        *,
        span_id: str | None = None,
        loop_detected: bool = False,
        repeat_count: int = 0,
    ) -> RiskSchema:
        grounding = self._grounding.assess(
            features, loop_detected=loop_detected, repeat_count=repeat_count
        )

        gemini_result = None
        gemini_used = False
        if self._gemini.available:
            gemini_result = self._gemini.classify(
                features, loop_detected=loop_detected, repeat_count=repeat_count
            )
            gemini_used = gemini_result is not None

        if gemini_result:
            self.last_source = f"gemini:{self._gemini.backend}"
            risk_score = gemini_result["risk_score"]
            status = gemini_result["status"]
            reason = gemini_result["reason"] or self._explain(features, status)
        else:
            self.last_source = "deterministic_fallback"
            risk_score = self._compute_score(features)
            status = self._classify(risk_score)
            reason = self._explain(features, status)

        if loop_detected or features.get("loop_score", 0) >= self.LOOP_SCORE_FLOOR_TRIGGER:
            risk_score = max(risk_score, self.LOOP_RISK_FLOOR)
            status = RiskLevel.CRITICAL

        calibrated = self._confidence.calibrate(
            risk_score,
            grounding,
            gemini_used=gemini_used,
            loop_detected=loop_detected,
        )
        risk_score = calibrated.calibrated_risk

        prefix = f"[{self.last_source}] "
        full_reason = prefix + reason
        if not grounding.grounded:
            full_reason += f" | {calibrated.reason}"

        return RiskSchema.from_assessment(
            session_id=session_id,
            span_id=span_id,
            status=status,
            risk_score=round(risk_score, 4),
            reason=full_reason,
            feature_vector=features,
        )

    def assess_vector(self, vector: FeatureVectorSchema) -> RiskSchema:
        """Assess a fused FeatureVector from the detector swarm."""
        return self.assess(
            vector.session_id,
            vector.features,
            span_id=vector.span_id,
            loop_detected=vector.loop_detected,
            repeat_count=vector.repeat_count,
        )

    def _compute_score(self, features: dict[str, float]) -> float:
        loop = features.get("loop_score", 0.0)
        progress = features.get("progress_score", 1.0)
        latency = features.get("latency_score", 0.0)
        token = features.get("token_score", 0.0)
        context = features.get("context_score", 0.0)
        error = features.get("error_score", 0.0)
        inverted_progress = 1.0 - progress

        weighted = sum(
            self.WEIGHTS[key] * val
            for key, val in [
                ("loop_score", loop),
                ("progress_score", inverted_progress),
                ("latency_score", latency),
                ("token_score", token),
                ("context_score", context),
                ("error_score", error),
            ]
        )
        return max(0.0, min(1.0, weighted))

    def _classify(self, risk_score: float) -> RiskLevel:
        if risk_score >= self.CRITICAL_THRESHOLD:
            return RiskLevel.CRITICAL
        if risk_score >= self.WARNING_THRESHOLD:
            return RiskLevel.WARNING
        return RiskLevel.HEALTHY

    def _explain(self, features: dict[str, float], level: RiskLevel) -> str:
        triggers: list[str] = []
        if features.get("loop_score", 0) >= 0.5:
            triggers.append("repeated tool loop detected")
        if features.get("progress_score", 1) <= 0.3:
            triggers.append("agent progress stalled")
        if features.get("latency_score", 0) >= 0.7:
            triggers.append("high latency")
        if features.get("token_score", 0) >= 0.8:
            triggers.append("token budget nearly exhausted")
        if features.get("error_score", 0) >= 0.3:
            triggers.append("elevated error rate")

        if not triggers:
            return f"Session is {level.value} (deterministic fallback)"
        return f"Risk {level.value}: {', '.join(triggers)} (deterministic fallback)"
