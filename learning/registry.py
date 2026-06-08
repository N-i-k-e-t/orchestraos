"""Learning domain agent roster."""

from shared.agent_registry import AgentEntry

AGENTS: list[AgentEntry] = [
    AgentEntry("LearningCoordinator", "Learning", "learning", "learning/coordinator.py", tested=True),
    AgentEntry("IncidentLearningAgent", "Learning", "learning", "learning/incident_learning_agent.py", tested=True),
    AgentEntry("PatternMiningAgent", "Learning", "learning", "learning/pattern_mining_agent.py", tested=True),
    AgentEntry("PolicyOptimizationAgent", "Learning", "learning", "learning/policy_optimization_agent.py", tested=True),
    AgentEntry("incident_summarization", "Learning", "learning", "learning/incident_learning_agent.py", kind="capability-of", parent="IncidentLearningAgent", tested=True),
    AgentEntry("pattern_frequency_mining", "Learning", "learning", "learning/pattern_mining_agent.py", kind="capability-of", parent="PatternMiningAgent", tested=True),
    AgentEntry("threshold_recommendation", "Learning", "learning", "learning/policy_optimization_agent.py", kind="capability-of", parent="PolicyOptimizationAgent", tested=True),
]
