"""AutoGPT infinite-loop scenario — live demo entry point."""

from __future__ import annotations

from agent_harness.metrics import cost_reduction
from agent_harness.protected_agent import run_protected_demo
from agent_harness.unprotected_agent import run_unprotected_demo
from checkpoint.redis_store import RedisStore


def run_autogpt_scenario(
    collector_url: str | None = None,
    store: RedisStore | None = None,
) -> dict:
    """
    Run the money-shot demo: unprotected vs protected side-by-side.

    Target:
      LEFT:  400 calls · 20 min · $42 · FAILURE
      RIGHT: 5 calls · 47 sec · $0.36 · RECOVERED
    """
    unprotected = run_unprotected_demo(max_iterations=400)
    protected = run_protected_demo(collector_url=collector_url, store=store)

    reduction = cost_reduction(
        type("M", (), {"cost_usd": unprotected.cost_usd})(),
        type("M", (), {"cost_usd": protected.cost_usd})(),
    )

    print(f"\n{'='*60}")
    print("COMPARISON - OrchestraOS Loop Sentinel")
    print(f"{'='*60}")
    print(f"  {'':20} {'UNPROTECTED':>14} {'PROTECTED':>14}")
    print(f"  {'Calls:':20} {unprotected.calls:>14} {protected.calls:>14}")
    print(f"  {'Duration:':20} {unprotected.duration_sec / 60:>11.0f} min {protected.duration_sec:>11.0f} sec")
    print(f"  {'Cost:':20} ${unprotected.cost_usd:>12.2f} ${protected.cost_usd:>12.2f}")
    print(f"  {'Outcome:':20} {unprotected.outcome:>14} {protected.outcome:>14}")
    print(f"  Cost reduction: {reduction}%")

    return {
        "unprotected": {
            "calls": unprotected.calls,
            "duration_sec": unprotected.duration_sec,
            "cost_usd": unprotected.cost_usd,
            "outcome": unprotected.outcome,
        },
        "protected": {
            "calls": protected.calls,
            "duration_sec": protected.duration_sec,
            "cost_usd": protected.cost_usd,
            "outcome": protected.outcome,
        },
        "cost_reduction_pct": reduction,
    }


if __name__ == "__main__":
    from shared.console import configure_stdout_utf8

    configure_stdout_utf8()
    run_autogpt_scenario()
