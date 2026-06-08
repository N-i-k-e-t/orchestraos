"""Remediation service agent roster."""

from shared.agent_registry import AgentEntry

AGENTS: list[AgentEntry] = [
    AgentEntry("RetryAgent", "Remediation", "remediation", "remediation/agents.py", tested=True),
    AgentEntry("PromptRewriteAgent", "Remediation", "remediation", "remediation/agents.py", tested=True),
    AgentEntry("RollbackAgent", "Remediation", "remediation", "remediation/agents.py", tested=True),
    AgentEntry("HumanEscalationAgent", "Remediation", "remediation", "remediation/agents.py", tested=True),
    AgentEntry("FallbackToolAgent", "Remediation", "remediation", "remediation/agents.py", tested=True),
    AgentEntry("RemediationOrchestrator", "Remediation", "remediation", "remediation/orchestrator.py", tested=True),
    AgentEntry("exponential_backoff_retry", "Remediation", "remediation", "remediation/agents.py", kind="capability-of", parent="RetryAgent", tested=True),
    AgentEntry("prompt_de_looping", "Remediation", "remediation", "remediation/agents.py", kind="capability-of", parent="PromptRewriteAgent", tested=True),
    AgentEntry("checkpoint_rollback", "Remediation", "remediation", "remediation/agents.py", kind="capability-of", parent="RollbackAgent", tested=True),
    AgentEntry("human_escalation_path", "Remediation", "remediation", "remediation/agents.py", kind="capability-of", parent="HumanEscalationAgent", tested=True),
    AgentEntry("tool_fallback_switch", "Tool", "remediation", "remediation/agents.py", kind="capability-of", parent="FallbackToolAgent", tested=True),
    AgentEntry("recovery_chain", "Remediation", "remediation", "remediation/orchestrator.py", kind="capability-of", parent="RemediationOrchestrator", tested=True),
]
