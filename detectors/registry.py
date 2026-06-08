"""Detector service agent roster."""

from shared.agent_registry import AgentEntry

AGENTS: list[AgentEntry] = [
    AgentEntry("LoopAgent", "Detection", "detectors", "detectors/loop_agent.py", tested=True),
    AgentEntry("ProgressAgent", "Context", "detectors", "detectors/progress_agent.py", tested=True),
    AgentEntry("TokenAgent", "Cost", "detectors", "detectors/token_agent.py", tested=True),
    AgentEntry("LatencyAgent", "Reliability", "detectors", "detectors/latency_agent.py", tested=True),
    AgentEntry("ContextAgent", "Context", "detectors", "detectors/context_agent.py", tested=True),
    AgentEntry("ErrorAgent", "Reliability", "detectors", "detectors/error_agent.py", tested=True),
    AgentEntry("DetectorSwarm", "Detection", "detectors", "detectors/swarm.py", tested=True),
    AgentEntry("loop_fingerprinting", "Detection", "detectors", "detectors/loop_agent.py", kind="capability-of", parent="LoopAgent", tested=True),
    AgentEntry("progress_stagnation", "Context", "detectors", "detectors/progress_agent.py", kind="capability-of", parent="ProgressAgent", tested=True),
    AgentEntry("token_budget_tracking", "Cost", "detectors", "detectors/token_agent.py", kind="capability-of", parent="TokenAgent", tested=True),
    AgentEntry("latency_anomaly", "Reliability", "detectors", "detectors/latency_agent.py", kind="capability-of", parent="LatencyAgent", tested=True),
    AgentEntry("context_stagnation", "Context", "detectors", "detectors/context_agent.py", kind="capability-of", parent="ContextAgent", tested=True),
    AgentEntry("error_rate_tracking", "Reliability", "detectors", "detectors/error_agent.py", kind="capability-of", parent="ErrorAgent", tested=True),
    AgentEntry("FeatureFusion", "Detection", "detectors", "detectors/feature_fusion.py", kind="capability-of", parent="DetectorSwarm", tested=True),
    AgentEntry("parallel_swarm_dispatch", "Detection", "detectors", "detectors/swarm.py", kind="capability-of", parent="DetectorSwarm", tested=True),
]
