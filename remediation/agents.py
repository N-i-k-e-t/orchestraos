"""Remediation agent implementations."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RemediationAction(str, Enum):
    RETRY = "retry"
    REWRITE_PROMPT = "rewrite_prompt"
    ROLLBACK = "rollback"
    FALLBACK_TOOL = "fallback_tool"
    ESCALATE = "escalate"


@dataclass
class RemediationResult:
    action: RemediationAction
    session_id: str
    success: bool
    message: str
    payload: dict[str, Any]


class RetryAgent:
    """Retries the last failed tool call with exponential backoff metadata."""

    def execute(self, session_id: str, attempt: int = 1) -> RemediationResult:
        delay = min(2**attempt, 60)
        return RemediationResult(
            action=RemediationAction.RETRY,
            session_id=session_id,
            success=True,
            message=f"Scheduled retry attempt {attempt} after {delay}s",
            payload={"attempt": attempt, "delay_sec": delay},
        )


class PromptRewriteAgent:
    """Rewrites the agent prompt to break out of a loop or stall."""

    def execute(self, session_id: str, original_prompt: str) -> RemediationResult:
        rewritten = (
            f"{original_prompt}\n\n"
            "[OrchestraOS] You appear stuck. Try a different approach. "
            "Avoid repeating the same tool call with identical parameters."
        )
        return RemediationResult(
            action=RemediationAction.REWRITE_PROMPT,
            session_id=session_id,
            success=True,
            message="Prompt rewritten to encourage alternative strategy",
            payload={"rewritten_prompt": rewritten},
        )


class RollbackAgent:
    """Restores agent state from the last checkpoint."""

    def execute(self, session_id: str, checkpoint: dict[str, Any] | None) -> RemediationResult:
        if checkpoint is None:
            return RemediationResult(
                action=RemediationAction.ROLLBACK,
                session_id=session_id,
                success=False,
                message="No checkpoint available for rollback",
                payload={},
            )
        return RemediationResult(
            action=RemediationAction.ROLLBACK,
            session_id=session_id,
            success=True,
            message="Restored state from checkpoint",
            payload={"checkpoint": checkpoint},
        )


class HumanEscalationAgent:
    """Escalates the session to a human operator."""

    def execute(self, session_id: str, reason: str) -> RemediationResult:
        return RemediationResult(
            action=RemediationAction.ESCALATE,
            session_id=session_id,
            success=True,
            message=f"Escalated to human operator: {reason}",
            payload={"reason": reason, "escalated": True},
        )


class FallbackToolAgent:
    """Switches to an alternate tool to break out of a loop."""

    DEFAULT_FALLBACKS: dict[str, str] = {
        "web_search": "read_file",
        "check_status": "list_processes",
        "browse": "fetch_url",
    }

    def execute(
        self,
        session_id: str,
        tool_name: str,
        params: dict[str, Any] | None = None,
    ) -> RemediationResult:
        fallback = self.DEFAULT_FALLBACKS.get(tool_name, "generic_query")
        return RemediationResult(
            action=RemediationAction.FALLBACK_TOOL,
            session_id=session_id,
            success=True,
            message=f"Switched from {tool_name} to fallback {fallback}",
            payload={
                "original_tool": tool_name,
                "fallback_tool": fallback,
                "original_params": params or {},
                "fallback_params": {"source": "orchestraos_remediation"},
            },
        )
