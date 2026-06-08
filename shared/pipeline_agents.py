"""Agent name tuples for workers — no heavy imports (safe for slim Docker images)."""

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
