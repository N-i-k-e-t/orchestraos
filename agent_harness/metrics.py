"""Demo metrics for harness comparison."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DemoMetrics:
    calls: int
    duration_sec: float
    cost_usd: float
    tokens: int
    outcome: str

    @property
    def cost_reduction_pct(self) -> float:
        return 0.0


# AutoGPT infinite-loop scenario (unprotected baseline)
UNPROTECTED_CALLS = 400
UNPROTECTED_DURATION_SEC = 20 * 60  # 20 minutes
UNPROTECTED_COST_USD = 42.0
TOKENS_PER_CALL = 105  # ~42k tokens / 400 calls

# OrchestraOS protected target
PROTECTED_CALLS = 5
PROTECTED_DURATION_SEC = 47.0
PROTECTED_COST_USD = 0.36


def estimate_unprotected(tokens_per_call: int = TOKENS_PER_CALL) -> DemoMetrics:
    calls = UNPROTECTED_CALLS
    return DemoMetrics(
        calls=calls,
        duration_sec=UNPROTECTED_DURATION_SEC,
        cost_usd=UNPROTECTED_COST_USD,
        tokens=calls * tokens_per_call,
        outcome="FAILURE",
    )


def estimate_protected(
    calls: int,
    duration_sec: float | None = None,
    tokens_per_call: int = TOKENS_PER_CALL,
) -> DemoMetrics:
    duration = duration_sec if duration_sec is not None else PROTECTED_DURATION_SEC * (calls / PROTECTED_CALLS)
    cost = PROTECTED_COST_USD * (calls / PROTECTED_CALLS)
    return DemoMetrics(
        calls=calls,
        duration_sec=round(duration, 1),
        cost_usd=round(cost, 2),
        tokens=calls * tokens_per_call,
        outcome="RECOVERED",
    )


def cost_reduction(unprotected: DemoMetrics, protected: DemoMetrics) -> float:
    if unprotected.cost_usd == 0:
        return 0.0
    return round((1 - protected.cost_usd / unprotected.cost_usd) * 100, 1)
