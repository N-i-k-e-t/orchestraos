"""Simulated AutoGPT agent — protected by full OrchestraOS pipeline."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx

from agent_harness.metrics import PROTECTED_DURATION_SEC, TOKENS_PER_CALL, estimate_protected
from agent_harness.unprotected_agent import AgentRunResult
from breaker.circuit_breaker import BreakerState
from breaker.circuit_breaker_agent import CircuitBreakerAgent
from checkpoint.redis_store import RedisStore
from detectors.swarm import DetectorSwarm
from monitor_model.risk_agent import RiskAgent
from remediation.orchestrator import RemediationOrchestrator
from shared.schemas import BreakerEventSchema, SpanSchema


@dataclass
class ProtectedAgent:
    """
    AutoGPT simulator wired through OrchestraOS:
    Span → DetectorSwarm → RiskAgent → CircuitBreaker → RemediationOrchestrator
    """

    session_id: str = field(default_factory=lambda: f"protected-{uuid.uuid4().hex[:8]}")
    store: RedisStore | None = None
    max_iterations: int = 400
    collector_url: str | None = None
    emit_otel: bool = True

    def __post_init__(self) -> None:
        self._store = self.store or RedisStore()
        self._swarm = DetectorSwarm()
        self._risk = RiskAgent()
        self._breaker = CircuitBreakerAgent(self._store)
        self._orchestrator = RemediationOrchestrator(self._store)
        self._loop_params = {"query": "server status", "target": "localhost"}
        self._recovered = False
        self._fallback_tool = "read_file"

    def _emit_span(self, span: SpanSchema) -> None:
        if not self.emit_otel or not self.collector_url:
            return
        try:
            httpx.post(
                f"{self.collector_url.rstrip('/')}/v1/traces",
                json=span.model_dump(mode="json"),
                timeout=2.0,
            )
        except Exception:
            pass

    def _tool_call(
        self,
        step: int,
        tool_name: str,
        params: dict[str, Any],
        state_hash: str,
        trace_id: str = "autogpt-trace",
    ) -> dict[str, Any] | None:
        if not self._breaker.is_allowed(self.session_id):
            return {
                "step": step,
                "session_id": self.session_id,
                "blocked": True,
                "reason": "circuit_breaker_open",
                "orchestraos": True,
            }

        span = SpanSchema(
            trace_id=trace_id,
            span_id=f"span-{step}",
            session_id=self.session_id,
            tool_name=tool_name,
            params=params,
            token_count=TOKENS_PER_CALL,
            latency_ms=150.0,
            state_hash=state_hash,
        )
        self._emit_span(span)

        vector = self._swarm.process(span)
        risk = self._risk.assess_vector(vector)
        breaker_event = self._breaker.process_assessment(risk)

        entry: dict[str, Any] = {
            "step": step,
            "session_id": self.session_id,
            "tool_name": tool_name,
            "params": params,
            "token_count": TOKENS_PER_CALL,
            "loop_detected": vector.loop_detected,
            "repeat_count": vector.repeat_count,
            "risk_score": risk.risk_score,
            "status": risk.status.value,
            "breaker_state": breaker_event.state,
            "blocked": breaker_event.state == BreakerState.OPEN.value,
            "orchestraos": True,
        }

        self._store.save_checkpoint(
            self.session_id,
            {"tool_name": tool_name, "params": params, "step": step},
        )

        if breaker_event.state == BreakerState.OPEN.value:
            plan = self._orchestrator.handle_breaker_event(
                BreakerEventSchema(
                    session_id=breaker_event.session_id,
                    state=breaker_event.state,
                    previous_state=breaker_event.previous_state,
                    risk_score=breaker_event.risk_score,
                    allowed=breaker_event.allowed,
                    reason=breaker_event.reason,
                )
            )
            entry["remediation"] = plan.status if plan else None
            if plan and plan.recovered:
                self._recovered = True
                fallback = next(
                    (s for s in plan.steps if s["action"] == "fallback_tool"),
                    None,
                )
                if fallback:
                    self._fallback_tool = fallback["payload"].get("fallback_tool", "read_file")
            return entry

        return entry

    def run(self) -> AgentRunResult:
        start = time.perf_counter()
        log: list[dict[str, Any]] = []
        step = 0
        trace_id = f"trace-{uuid.uuid4().hex[:8]}"

        # Phase 1: loop until breaker trips (~3 identical calls)
        for _ in range(3):
            step += 1
            entry = self._tool_call(
                step, "web_search", self._loop_params, state_hash="stuck-state", trace_id=trace_id
            )
            if entry:
                log.append(entry)
            if entry and entry.get("blocked"):
                break

        # Phase 2: recovery calls with alternate tool/params (≤2 more to finish)
        if self._recovered:
            recovery_params = [
                {"query": "alternative approach", "source": "remediation"},
                {"query": "summarize findings", "source": "remediation"},
            ]
            for params in recovery_params:
                if step >= 5:
                    break
                if not self._breaker.is_allowed(self.session_id):
                    break
                step += 1
                entry = self._tool_call(
                    step,
                    self._fallback_tool,
                    params,
                    state_hash=f"recovery-{step}",
                    trace_id=trace_id,
                )
                if entry:
                    log.append(entry)
                if entry and not entry.get("blocked"):
                    break

        elapsed = time.perf_counter() - start
        calls = len(log)
        metrics = estimate_protected(calls, duration_sec=PROTECTED_DURATION_SEC)

        return AgentRunResult(
            session_id=self.session_id,
            log=log,
            calls=calls,
            tokens=calls * TOKENS_PER_CALL,
            duration_sec=metrics.duration_sec,
            cost_usd=metrics.cost_usd,
            outcome="RECOVERED" if self._recovered else "FAILURE",
            loop_detected=True,
        )


def run_protected_demo(
    collector_url: str | None = None,
    store: RedisStore | None = None,
) -> AgentRunResult:
    agent = ProtectedAgent(
        store=store,
        collector_url=collector_url,
        emit_otel=bool(collector_url),
    )
    result = agent.run()
    print(f"\n{'='*60}")
    print("PROTECTED AutoGPT Agent (OrchestraOS)")
    print(f"{'='*60}")
    print(f"  Calls:    {result.calls}")
    print(f"  Duration: {result.duration_sec:.0f} sec")
    print(f"  Cost:     ${result.cost_usd:.2f}")
    print(f"  Outcome:  {result.outcome}")
    for entry in result.log:
        print(
            f"  step={entry['step']} tool={entry.get('tool_name', '-')} "
            f"repeat={entry.get('repeat_count', '-')} "
            f"risk={entry.get('risk_score', '-')} "
            f"breaker={entry.get('breaker_state', '-')} "
            f"blocked={entry.get('blocked', False)}"
        )
    return result
