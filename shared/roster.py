"""Aggregate all service agent registries."""

from __future__ import annotations

import logging

from shared.agent_registry import AgentEntry, merge_registries

logger = logging.getLogger(__name__)

# Package names must match real top-level folders under /app (e.g. monitor_model, not monitor).
_SERVICE_PACKAGES: tuple[tuple[str, str], ...] = (
    ("collector", "collector"),
    ("detectors", "detectors"),
    ("monitor_model", "monitor"),
    ("breaker", "breaker"),
    ("remediation", "remediation"),
    ("integrations", "partners"),
    ("learning", "learning"),
    ("agent_harness", "harness"),
    ("dashboard", "dashboard"),
)


def _load_registry(package: str, label: str) -> list[AgentEntry]:
    try:
        mod = __import__(f"{package}.registry", fromlist=["AGENTS"])
        return list(getattr(mod, "AGENTS", []))
    except ModuleNotFoundError as exc:
        logger.warning("[roster] skipping %s (%s): %s", label, package, exc)
        return []


def load_all_registries() -> list[AgentEntry]:
    chunks: list[list[AgentEntry]] = [
        _load_registry(package, label) for package, label in _SERVICE_PACKAGES
    ]
    return merge_registries(*chunks)
