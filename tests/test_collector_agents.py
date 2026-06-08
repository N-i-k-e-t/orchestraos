"""Collector agent class tests."""

from tests.conftest import FakeRedisStore

from collector.agents import OtelParserAgent, SpanIngestAgent
from shared.schemas import SpanSchema


class TestCollectorAgents:
    def test_otel_parser_agent(self) -> None:
        agent = OtelParserAgent()
        spans = agent.parse(
            {
                "spans": [
                    {
                        "trace_id": "t1",
                        "span_id": "s1",
                        "session_id": "sess-1",
                        "tool_name": "read_file",
                        "params": {},
                    }
                ]
            }
        )
        assert len(spans) == 1
        assert spans[0].tool_name == "read_file"

    def test_span_ingest_agent(self) -> None:
        store = FakeRedisStore()
        msgs: list[str] = []

        class Pub:
            def publish(self, span: dict) -> str:
                msgs.append(span["span_id"])
                return "mid-99"

        agent = SpanIngestAgent(store, Pub())
        span = SpanSchema(
            trace_id="t1",
            span_id="s1",
            session_id="sess-1",
            tool_name="web_search",
            params={"q": "x"},
        )
        assert agent.ingest(span) == "mid-99"
        assert store.load_checkpoint("sess-1")["tool_name"] == "web_search"
