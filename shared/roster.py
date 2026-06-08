"""Aggregate all service agent registries."""

from __future__ import annotations

from shared.agent_registry import AgentEntry, merge_registries


def load_all_registries() -> list[AgentEntry]:
    from agent_harness.registry import AGENTS as harness
    from breaker.registry import AGENTS as breaker
    from collector.registry import AGENTS as collector
    from dashboard.registry import AGENTS as dashboard
    from detectors.registry import AGENTS as detectors
    from integrations.registry import AGENTS as partners
    from learning.registry import AGENTS as learning
    from monitor_model.registry import AGENTS as monitor
    from remediation.registry import AGENTS as remediation

    return merge_registries(
        collector,
        detectors,
        monitor,
        breaker,
        remediation,
        partners,
        learning,
        harness,
        dashboard,
    )
