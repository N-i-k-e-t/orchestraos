"""Breaker service agent roster."""

from shared.agent_registry import AgentEntry

AGENTS: list[AgentEntry] = [
    AgentEntry("CircuitBreakerAgent", "Reliability", "breaker", "breaker/circuit_breaker_agent.py", tested=True),
    AgentEntry("HealthAgent", "Reliability", "breaker", "breaker/health_agent.py", tested=True),
    AgentEntry("session_breaker_state", "Reliability", "breaker", "breaker/circuit_breaker.py", kind="capability-of", parent="CircuitBreakerAgent", tested=True),
    AgentEntry("risk_threshold_trip", "Reliability", "breaker", "breaker/circuit_breaker_agent.py", kind="capability-of", parent="CircuitBreakerAgent", tested=True),
    AgentEntry("half_open_recovery", "Reliability", "breaker", "breaker/circuit_breaker.py", kind="capability-of", parent="CircuitBreakerAgent", tested=True),
    AgentEntry("redis_health_probe", "Reliability", "breaker", "breaker/health_agent.py", kind="capability-of", parent="HealthAgent", tested=True),
]
