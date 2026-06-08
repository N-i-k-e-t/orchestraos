"""Confidence agent — calibrates trust in risk assessments."""

from __future__ import annotations

from dataclasses import dataclass

from monitor_model.grounding_agent import GroundingResult


@dataclass(frozen=True)
class ConfidenceResult:
    confidence: float
    calibrated_risk: float
    reason: str


class ConfidenceAgent:
    """
    Adjusts effective risk based on grounding quality and backend source.

    High confidence when features are grounded and reasoning backend is Gemini.
    """

    def calibrate(
        self,
        risk_score: float,
        grounding: GroundingResult,
        *,
        gemini_used: bool = False,
        loop_detected: bool = False,
    ) -> ConfidenceResult:
        confidence = grounding.grounding_score
        if gemini_used:
            confidence = min(1.0, confidence + 0.15)
        if loop_detected:
            confidence = min(1.0, confidence + 0.1)

        if not grounding.grounded:
            calibrated = min(1.0, risk_score + (1.0 - confidence) * 0.1)
            reason = "Low grounding — risk nudged upward for safety"
        else:
            calibrated = risk_score
            reason = "Grounded features with calibrated confidence"

        return ConfidenceResult(
            confidence=round(confidence, 4),
            calibrated_risk=round(calibrated, 4),
            reason=reason,
        )
