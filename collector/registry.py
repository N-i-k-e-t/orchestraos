"""Collector service agent roster."""

from shared.agent_registry import AgentEntry

AGENTS: list[AgentEntry] = [
    AgentEntry("SpanIngestAgent", "Observation", "collector", "collector/agents.py", tested=True),
    AgentEntry("OtelParserAgent", "Observation", "collector", "collector/otel_parser.py", tested=True),
    AgentEntry("otlp_http_ingest", "Observation", "collector", "collector/main.py", kind="capability-of", parent="SpanIngestAgent", tested=True),
    AgentEntry("span_validation", "Observation", "collector", "collector/main.py", kind="capability-of", parent="SpanIngestAgent", tested=True),
    AgentEntry("pubsub_span_publish", "Observation", "collector", "collector/main.py", kind="capability-of", parent="SpanIngestAgent", tested=True),
    AgentEntry("otel_json_parse", "Observation", "collector", "collector/otel_parser.py", kind="capability-of", parent="OtelParserAgent", tested=True),
]
