"""Monitor model service agent roster."""

from shared.agent_registry import AgentEntry

AGENTS: list[AgentEntry] = [
    AgentEntry("RiskAgent", "Reasoning", "monitor", "monitor_model/risk_agent.py", tested=True),
    AgentEntry("GroundingAgent", "Reasoning", "monitor", "monitor_model/grounding_agent.py", tested=True),
    AgentEntry("ConfidenceAgent", "Reasoning", "monitor", "monitor_model/confidence_agent.py", tested=True),
    AgentEntry("MonitorAgentBuilder", "Reasoning", "monitor", "monitor_model/agent_builder.py", tested=True),
    AgentEntry("GeminiClient", "Reasoning", "monitor", "monitor_model/gemini_client.py", tested=True),
    AgentEntry("gemini_vertex_primary", "Reasoning", "monitor", "monitor_model/gemini_client.py", kind="capability-of", parent="GeminiClient", tested=True),
    AgentEntry("gemini_api_key_fallback", "Reasoning", "monitor", "monitor_model/gemini_client.py", kind="capability-of", parent="GeminiClient", tested=True),
    AgentEntry("deterministic_guardrails", "Reasoning", "monitor", "monitor_model/risk_agent.py", kind="capability-of", parent="RiskAgent", tested=True),
    AgentEntry("loop_risk_floor", "Reasoning", "monitor", "monitor_model/risk_agent.py", kind="capability-of", parent="RiskAgent", tested=True),
    AgentEntry("feature_grounding_check", "Reasoning", "monitor", "monitor_model/grounding_agent.py", kind="capability-of", parent="GroundingAgent", tested=True),
    AgentEntry("confidence_calibration", "Reasoning", "monitor", "monitor_model/confidence_agent.py", kind="capability-of", parent="ConfidenceAgent", tested=True),
    AgentEntry("agent_builder_orchestration", "Reasoning", "monitor", "monitor_model/agent_builder.py", kind="capability-of", parent="MonitorAgentBuilder", tested=True),
]
