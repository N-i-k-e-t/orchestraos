"""Simulated AutoGPT agent — unprotected infinite loop (400 calls)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from agent_harness.metrics import TOKENS_PER_CALL, estimate_unprotected


@dataclass
class AgentRunResult:
    session_id: str
    log: list[dict[str, Any]] = field(default_factory=list)
    calls: int = 0
    tokens: int = 0
    duration_sec: float = 0.0
    cost_usd: float = 0.0
    outcome: str = "FAILURE"
    loop_detected: bool = False


class UnprotectedAgent:
    """
    Simulates AutoGPT stuck in a repeated web_search loop.
    No OrchestraOS protection — runs until max_iterations (400).
    """

    DEFAULT_TOOL = "web_search"
    DEFAULT_PARAMS = {"query": "server status", "target": "localhost"}

    def __init__(
        self,
        session_id: str | None = None,
        max_iterations: int = 400,
        simulate_delay: bool = False,
    ) -> None:
        self.session_id = session_id or f"unprotected-{uuid.uuid4().hex[:8]}"
        self.max_iterations = max_iterations
        self.simulate_delay = simulate_delay

    def run(self) -> AgentRunResult:
        start = time.perf_counter()
        log: list[dict[str, Any]] = []
        tokens = 0

        for i in range(self.max_iterations):
            if self.simulate_delay:
                time.sleep(0.001)

            tokens += TOKENS_PER_CALL
            log.append({
                "step": i + 1,
                "session_id": self.session_id,
                "tool_name": self.DEFAULT_TOOL,
                "params": self.DEFAULT_PARAMS,
                "token_count": TOKENS_PER_CALL,
                "blocked": False,
                "orchestraos": False,
            })

        elapsed = time.perf_counter() - start
        baseline = estimate_unprotected()

        return AgentRunResult(
            session_id=self.session_id,
            log=log,
            calls=len(log),
            tokens=tokens,
            duration_sec=baseline.duration_sec if not self.simulate_delay else round(elapsed, 1),
            cost_usd=baseline.cost_usd,
            outcome="FAILURE",
            loop_detected=True,
        )


def run_unprotected_demo(max_iterations: int = 400) -> AgentRunResult:
    agent = UnprotectedAgent(max_iterations=max_iterations)
    result = agent.run()
    print(f"\n{'='*60}")
    print("UNPROTECTED AutoGPT Agent")
    print(f"{'='*60}")
    print(f"  Calls:    {result.calls}")
    print(f"  Duration: {result.duration_sec / 60:.0f} min")
    print(f"  Cost:     ${result.cost_usd:.2f}")
    print(f"  Outcome:  {result.outcome}")
    print(f"  Sample (first 3):")
    for entry in result.log[:3]:
        print(f"    step={entry['step']} tool={entry['tool_name']} blocked={entry['blocked']}")
    print(f"    ... ({result.calls - 3} more identical calls)")
    return result
