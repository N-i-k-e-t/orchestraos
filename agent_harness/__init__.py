"""Agent harness for demonstrating OrchestraOS protection."""

from agent_harness.metrics import cost_reduction, estimate_protected, estimate_unprotected
from agent_harness.protected_agent import ProtectedAgent, run_protected_demo
from agent_harness.scenario_autogpt import run_autogpt_scenario
from agent_harness.unprotected_agent import AgentRunResult, UnprotectedAgent, run_unprotected_demo

__all__ = [
    "UnprotectedAgent",
    "ProtectedAgent",
    "AgentRunResult",
    "run_unprotected_demo",
    "run_protected_demo",
    "run_autogpt_scenario",
    "cost_reduction",
    "estimate_unprotected",
    "estimate_protected",
]
