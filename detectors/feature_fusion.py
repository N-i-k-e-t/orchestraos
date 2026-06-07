"""Feature fusion for risk assessment input."""


class FeatureFusion:
    """
    Combines individual detector scores into a unified feature vector
    consumed by the RiskAgent.
    """

    @staticmethod
    def fuse(
        loop_score: float,
        progress_score: float,
        latency_score: float,
        token_score: float,
        context_score: float,
        error_score: float = 0.0,
    ) -> dict[str, float]:
        """Merge scores into a named feature dictionary (all in [0, 1])."""
        return {
            "loop_score": _clamp(loop_score),
            "progress_score": _clamp(progress_score),
            "latency_score": _clamp(latency_score),
            "token_score": _clamp(token_score),
            "context_score": _clamp(context_score),
            "error_score": _clamp(error_score),
        }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
