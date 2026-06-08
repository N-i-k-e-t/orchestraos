"""Grounding agent — validates detector features against observable span signals."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GroundingResult:
    grounded: bool
    grounding_score: float
    violations: tuple[str, ...]


class GroundingAgent:
    """
    Checks that risk-relevant features are grounded in observable signals.

    Low grounding_score indicates missing or inconsistent feature inputs.
    """

    REQUIRED_FEATURES = (
        "loop_score",
        "progress_score",
        "latency_score",
        "token_score",
        "context_score",
        "error_score",
    )

    def assess(
        self,
        features: dict[str, float],
        *,
        loop_detected: bool = False,
        repeat_count: int = 0,
    ) -> GroundingResult:
        violations: list[str] = []

        for key in self.REQUIRED_FEATURES:
            if key not in features:
                violations.append(f"missing_{key}")
            elif not 0.0 <= float(features[key]) <= 1.0:
                violations.append(f"out_of_range_{key}")

        loop_score = float(features.get("loop_score", 0.0))
        if loop_detected and loop_score < 0.5:
            violations.append("loop_flag_without_loop_score")
        if repeat_count >= 3 and loop_score < 0.8:
            violations.append("repeat_count_without_loop_score")

        penalty = min(1.0, len(violations) * 0.2)
        score = max(0.0, 1.0 - penalty)
        return GroundingResult(
            grounded=score >= 0.6 and not violations,
            grounding_score=round(score, 4),
            violations=tuple(violations),
        )
