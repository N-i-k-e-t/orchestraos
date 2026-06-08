"""Shared types for programmatic agent/capability rosters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AgentKind = Literal["agent", "capability-of"]
AgentStatus = Literal["implemented", "planned"]


@dataclass(frozen=True)
class AgentEntry:
    """One agent class or named capability in the OrchestraOS roster."""

    name: str
    domain: str
    service: str
    module: str
    kind: AgentKind = "agent"
    parent: str | None = None
    status: AgentStatus = "implemented"
    tested: bool = False

    def to_dict(self) -> dict[str, str | bool | None]:
        return {
            "name": self.name,
            "domain": self.domain,
            "service": self.service,
            "module": self.module,
            "kind": self.kind,
            "parent": self.parent,
            "status": self.status,
            "tested": self.tested,
        }


def merge_registries(*registries: list[AgentEntry]) -> list[AgentEntry]:
    """Flatten multiple service registries preserving order."""
    merged: list[AgentEntry] = []
    seen: set[str] = set()
    for registry in registries:
        for entry in registry:
            key = f"{entry.service}:{entry.name}"
            if key in seen:
                continue
            seen.add(key)
            merged.append(entry)
    return merged
