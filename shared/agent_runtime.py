"""Runtime hooks — record which agents fire and push live health state."""

from __future__ import annotations

from typing import Any

from shared.live_state import LiveStateStore


class AgentRuntime:
    """
    Tracks agents that execute during a session and mirrors state to Redis.

    Used by workers and the protected-agent harness so /health/live shows real activity.
    """

    def __init__(self, live: LiveStateStore | None = None) -> None:
        self._live = live
        self._session_agents: dict[str, set[str]] = {}
        self._service = "pipeline"

    def set_service(self, service: str) -> None:
        self._service = service
        if self._live:
            self._live.set_service_health(service, "ok", "processing")

    def record(
        self,
        session_id: str,
        agent_name: str,
        *,
        risk_score: float | None = None,
        loop_score: float | None = None,
        progress_score: float | None = None,
        breaker_state: str | None = None,
    ) -> None:
        agents = self._session_agents.setdefault(session_id, set())
        agents.add(agent_name)

        if not self._live:
            return

        kwargs: dict[str, Any] = {"active_agents": sorted(agents)}
        if risk_score is not None:
            kwargs["risk_score"] = risk_score
        if loop_score is not None:
            kwargs["loop_score"] = loop_score
        if progress_score is not None:
            kwargs["progress_score"] = progress_score
        if breaker_state is not None:
            kwargs["breaker_state"] = breaker_state

        self._live.update_session(session_id, **kwargs)

    def record_incident(self, incident: dict[str, Any]) -> None:
        if self._live:
            self._live.append_incident(incident)

    def fired_for(self, session_id: str) -> list[str]:
        return sorted(self._session_agents.get(session_id, set()))

    def all_fired(self) -> list[str]:
        merged: set[str] = set()
        for agents in self._session_agents.values():
            merged.update(agents)
        return sorted(merged)
