"""Agent harness roster — demo and replay agents."""

from shared.agent_registry import AgentEntry

AGENTS: list[AgentEntry] = [
    AgentEntry("ProtectedAgent", "Dashboard", "harness", "agent_harness/protected_agent.py", tested=True),
    AgentEntry("UnprotectedAgent", "Dashboard", "harness", "agent_harness/unprotected_agent.py", tested=True),
    AgentEntry("end_to_end_pipeline", "Dashboard", "harness", "agent_harness/protected_agent.py", kind="capability-of", parent="ProtectedAgent", tested=True),
    AgentEntry("autogpt_loop_simulation", "Detection", "harness", "agent_harness/unprotected_agent.py", kind="capability-of", parent="UnprotectedAgent", tested=True),
    AgentEntry("cost_metrics_estimation", "Cost", "harness", "agent_harness/metrics.py", kind="capability-of", parent="ProtectedAgent", tested=True),
]
