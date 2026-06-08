"""Dashboard service capabilities."""

from shared.agent_registry import AgentEntry

AGENTS: list[AgentEntry] = [
    AgentEntry("HealthDashboardAgent", "Dashboard", "dashboard", "dashboard/src/pages/Health.tsx", tested=True),
    AgentEntry("DemoCompareAgent", "Dashboard", "dashboard", "dashboard/src/pages/DemoPage.tsx", tested=True),
    AgentEntry("IncidentsViewAgent", "Dashboard", "dashboard", "dashboard/src/pages/IncidentsPage.tsx", tested=True),
    AgentEntry("MetricsViewAgent", "Dashboard", "dashboard", "dashboard/src/pages/MetricsPage.tsx", tested=True),
    AgentEntry("live_health_polling", "Dashboard", "dashboard", "dashboard/src/pages/Health.tsx", kind="capability-of", parent="HealthDashboardAgent", tested=True),
    AgentEntry("breaker_state_display", "Dashboard", "dashboard", "dashboard/src/pages/Health.tsx", kind="capability-of", parent="HealthDashboardAgent", tested=True),
    AgentEntry("risk_gauge_display", "Dashboard", "dashboard", "dashboard/src/pages/Health.tsx", kind="capability-of", parent="HealthDashboardAgent", tested=True),
    AgentEntry("incident_stream", "Dashboard", "dashboard", "dashboard/src/pages/Health.tsx", kind="capability-of", parent="HealthDashboardAgent", tested=True),
]
