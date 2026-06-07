"""Remediation orchestrator — sequential recovery pipeline."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from breaker.circuit_breaker import BreakerState, CircuitBreaker
from remediation.agents import (
    FallbackToolAgent,
    HumanEscalationAgent,
    PromptRewriteAgent,
    RemediationAction,
    RemediationResult,
    RetryAgent,
    RollbackAgent,
)
from shared.schemas import BreakerEventSchema, RemediationPlanSchema

if TYPE_CHECKING:
    from checkpoint.redis_store import RedisStore


class RemediationOrchestrator:
    """
    Executes recovery chain on breaker trip:
    Retry → PromptRewrite → Rollback → FallbackTool → HumanEscalation (if needed)

    Resets the circuit breaker when rollback + fallback succeed within the call budget.
    """

    MAX_RECOVERY_CALLS = 5

    def __init__(self, store: RedisStore) -> None:
        self._store = store
        self._retry = RetryAgent()
        self._rewrite = PromptRewriteAgent()
        self._rollback = RollbackAgent()
        self._fallback = FallbackToolAgent()
        self._escalate = HumanEscalationAgent()

    def handle_breaker_event(self, event: BreakerEventSchema) -> RemediationPlanSchema | None:
        """Run remediation when breaker opens. Returns None if no action needed."""
        if event.state != BreakerState.OPEN.value:
            return None

        session_id = event.session_id
        attempt = self._store.increment_remediation_attempts(session_id)
        checkpoint = self._store.load_checkpoint(session_id)
        tool_name = str(checkpoint.get("tool_name", "web_search") if checkpoint else "web_search")
        params = checkpoint.get("params", {}) if checkpoint else {}

        steps: list[RemediationResult] = [
            self._retry.execute(session_id, attempt=attempt),
            self._rewrite.execute(session_id, "Complete the assigned task efficiently"),
            self._rollback.execute(session_id, checkpoint),
            self._fallback.execute(session_id, tool_name, params),
        ]

        rollback_ok = steps[2].success
        fallback_ok = steps[3].success
        recovered = rollback_ok and fallback_ok and attempt <= self.MAX_RECOVERY_CALLS

        if recovered:
            breaker = CircuitBreaker(self._store, session_id)
            breaker.reset()
            status = "recovered"
        elif attempt >= self.MAX_RECOVERY_CALLS:
            steps.append(self._escalate.execute(session_id, event.reason))
            status = "escalated"
        else:
            status = "in_progress"

        plan = RemediationPlanSchema(
            plan_id=str(uuid.uuid4()),
            session_id=session_id,
            status=status,
            attempt=attempt,
            recovered=recovered,
            steps=[self._step_dict(s) for s in steps],
            total_steps=len(steps),
        )
        self._store.save_remediation_plan(session_id, plan.model_dump(mode="json"))
        return plan

    @staticmethod
    def _step_dict(result: RemediationResult) -> dict:
        return {
            "action": result.action.value,
            "success": result.success,
            "message": result.message,
            "payload": result.payload,
        }
