"""Partners / integrations service agent roster."""

from shared.agent_registry import AgentEntry

AGENTS: list[AgentEntry] = [
    AgentEntry("PartnerHub", "Observation", "partners", "integrations/partner_hub.py", tested=True),
    AgentEntry("ArizeExporter", "Observation", "partners", "integrations/arize_exporter.py", tested=True),
    AgentEntry("PhoenixMcpClient", "Observation", "partners", "integrations/phoenix_mcp.py", tested=True),
    AgentEntry("MongoIncidentStore", "Learning", "partners", "integrations/mongodb_store.py", tested=True),
    AgentEntry("ElasticExporter", "Observation", "partners", "integrations/elastic_exporter.py", tested=False),
    AgentEntry("DynatraceExporter", "Observation", "partners", "integrations/dynatrace_exporter.py", tested=False),
    AgentEntry("GitLabFallback", "Remediation", "partners", "integrations/gitlab_fallback.py", tested=False),
    AgentEntry("otlp_span_export", "Observation", "partners", "integrations/arize_exporter.py", kind="capability-of", parent="ArizeExporter", tested=True),
    AgentEntry("phoenix_mcp_session", "Observation", "partners", "integrations/phoenix_mcp.py", kind="capability-of", parent="PhoenixMcpClient", tested=True),
    AgentEntry("incident_persistence", "Learning", "partners", "integrations/mongodb_store.py", kind="capability-of", parent="MongoIncidentStore", tested=True),
    AgentEntry("breaker_event_fanout", "Observation", "partners", "integrations/partner_hub.py", kind="capability-of", parent="PartnerHub", tested=True),
]
