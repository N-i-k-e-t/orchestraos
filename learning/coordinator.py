"""Learning coordinator — runs all learning agents after incidents are recorded."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from typing import Any, Protocol

from learning.incident_learning_agent import IncidentLearningAgent
from learning.pattern_mining_agent import PatternMiningAgent
from learning.policy_optimization_agent import PolicyOptimizationAgent

logger = logging.getLogger(__name__)


class LearningStore(Protocol):
    def set(self, key: str, value: str, ex: int | None = None) -> None: ...


def _serialize(obj: Any) -> Any:
    if is_dataclass(obj):
        return {k: _serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, tuple):
        return [_serialize(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


class LearningCoordinator:
    """Executes IncidentLearning, PatternMining, and PolicyOptimization agents."""

    CACHE_KEY = "orch:learning:latest"
    TTL = 3600

    def __init__(
        self,
        store: LearningStore | None = None,
        incident_agent: IncidentLearningAgent | None = None,
        pattern_agent: PatternMiningAgent | None = None,
        policy_agent: PolicyOptimizationAgent | None = None,
    ) -> None:
        self._store = store
        self._incident = incident_agent or IncidentLearningAgent()
        self._pattern = pattern_agent or PatternMiningAgent()
        self._policy = policy_agent or PolicyOptimizationAgent()

    def run(self) -> dict[str, Any]:
        """Run all learning agents and return combined output."""
        summary = self._incident.summarize()
        patterns = self._pattern.mine()
        policy = self._policy.recommend()

        result = {
            "agents_fired": [
                "IncidentLearningAgent",
                "PatternMiningAgent",
                "PolicyOptimizationAgent",
            ],
            "summary": _serialize(summary),
            "patterns": _serialize(patterns),
            "policy": _serialize(policy),
        }

        if self._store:
            self._store.set(self.CACHE_KEY, json.dumps(result), ex=self.TTL)

        logger.info(
            "Learning agents ran — incidents=%d dominant_pattern=%s breaker_threshold=%.2f",
            summary.total_incidents,
            patterns.dominant_pattern,
            policy.breaker_threshold,
        )
        return result
