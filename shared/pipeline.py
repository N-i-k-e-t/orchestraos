"""In-process pipeline — runs all working agents on a span without Pub/Sub."""

from __future__ import annotations

from typing import Any

from breaker.circuit_breaker_agent import CircuitBreakerAgent
from checkpoint.redis_store import RedisStore
from detectors.swarm import DetectorSwarm
from learning.coordinator import LearningCoordinator
from monitor_model.agent_builder import MonitorAgentBuilder
from remediation.orchestrator import RemediationOrchestrator
from shared.agent_runtime import AgentRuntime
from shared.live_state import LiveStateStore
from shared.schemas import BreakerEventSchema, SpanSchema


DETECTOR_AGENTS = (
    "LoopAgent",
    "ProgressAgent",
    "TokenAgent",
    "LatencyAgent",
    "ContextAgent",
    "ErrorAgent",
    "DetectorSwarm",
    "FeatureFusion",
)

REMEDIATION_AGENTS = (
    "RetryAgent",
    "PromptRewriteAgent",
    "RollbackAgent",
    "FallbackToolAgent",
    "HumanEscalationAgent",
    "RemediationOrchestrator",
)


class PipelineRunner:
    """
    Executes the full OrchestraOS agent chain in-process.

    Used by ProtectedAgent, integration tests, and demo harness.
    """

    def __init__(self, store: RedisStore | None = None) -> None:
        self._store = store or RedisStore()
        self._live = LiveStateStore(self._store)
        self._runtime = AgentRuntime(self._live)
        self._swarm = DetectorSwarm()
        self._builder = MonitorAgentBuilder()
        self._breaker = CircuitBreakerAgent(self._store)
        self._remediation = RemediationOrchestrator(self._store)
        self._learning = LearningCoordinator(store=self._store)

    @property
    def runtime(self) -> AgentRuntime:
        return self._runtime

    @property
    def live(self) -> LiveStateStore:
        return self._live

    def process_span(self, span: SpanSchema) -> dict[str, Any]:
        """Run detect → reason → break → remediate on one span."""
        sid = span.session_id
        self._store.save_checkpoint(
            sid,
            {
                "tool_name": span.tool_name,
                "params": span.params,
                "trace_id": span.trace_id,
                "span_id": span.span_id,
            },
        )
        self._runtime.set_service("detectors")

        vector = self._swarm.process(span)
        for name in DETECTOR_AGENTS:
            self._runtime.record(
                sid,
                name,
                loop_score=vector.features.get("loop_score", 0),
                progress_score=vector.features.get("progress_score", 1),
            )

        self._runtime.set_service("monitor")
        assessment = self._builder.execute_vector(vector)
        self._runtime.record(
            sid,
            "RiskAgent",
            risk_score=assessment.risk_score,
            loop_score=vector.features.get("loop_score", 0),
            progress_score=vector.features.get("progress_score", 1),
        )
        self._runtime.record(sid, "GroundingAgent")
        self._runtime.record(sid, "ConfidenceAgent")
        self._runtime.record(sid, "MonitorAgentBuilder")
        if "gemini:" in assessment.reason:
            self._runtime.record(sid, "GeminiClient")

        self._runtime.set_service("breaker")
        event = self._breaker.process_assessment(assessment)
        self._runtime.record(
            sid,
            "CircuitBreakerAgent",
            risk_score=assessment.risk_score,
            breaker_state=event.state,
        )
        self._runtime.record(sid, "HealthAgent")

        remediation_status = None
        recovered = False
        if event.state == "open":
            self._runtime.record_incident(
                {
                    "incident_id": f"{sid}-breaker",
                    "session_id": sid,
                    "incident_type": "breaker_trip",
                    "severity": "critical",
                    "reason": assessment.reason,
                }
            )
            if vector.loop_detected:
                self._runtime.record_incident(
                    {
                        "incident_id": f"{sid}-loop",
                        "session_id": sid,
                        "incident_type": "loop",
                        "severity": "critical",
                        "reason": "Loop detected by LoopAgent",
                    }
                )

            self._runtime.set_service("remediation")
            plan = self._remediation.handle_breaker_event(
                BreakerEventSchema(
                    session_id=event.session_id,
                    state=event.state,
                    previous_state=event.previous_state,
                    risk_score=event.risk_score,
                    allowed=event.allowed,
                    reason=event.reason,
                )
            )
            for name in REMEDIATION_AGENTS:
                self._runtime.record(sid, name, breaker_state=event.state)
            remediation_status = plan.status if plan else None
            recovered = bool(plan and plan.recovered)

            self._runtime.set_service("learning")
            learning_result = self._learning.run()
            for name in learning_result.get("agents_fired", []):
                self._runtime.record(sid, name)

        fired = self._runtime.fired_for(sid)
        return {
            "session_id": sid,
            "loop_detected": vector.loop_detected,
            "repeat_count": vector.repeat_count,
            "risk_score": assessment.risk_score,
            "status": assessment.status.value,
            "breaker_state": event.state,
            "blocked": event.state == "open" and not event.allowed,
            "remediation": remediation_status,
            "recovered": recovered,
            "agents_fired": fired,
            "reason": assessment.reason,
        }
