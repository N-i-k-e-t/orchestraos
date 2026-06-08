"""Collector agents — OTLP parse and span ingest."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from collector.otel_parser import parse_payload
from shared.schemas import SpanSchema

logger = logging.getLogger(__name__)


class SpanPublisher(Protocol):
    def publish(self, span: dict[str, Any]) -> str: ...


class CheckpointStore(Protocol):
    def save_checkpoint(self, session_id: str, data: dict[str, Any]) -> None: ...


class PartnerExporter(Protocol):
    def export_span(self, span: SpanSchema) -> dict[str, bool]: ...


class OtelParserAgent:
    """Parses OTLP JSON or OrchestraOS span payloads into validated spans."""

    def parse(self, payload: dict[str, Any]) -> list[SpanSchema]:
        return parse_payload(payload)


class SpanIngestAgent:
    """Ingests a validated span: checkpoint, Pub/Sub publish, optional partner export."""

    def __init__(
        self,
        store: CheckpointStore,
        publisher: SpanPublisher,
        partner: PartnerExporter | None = None,
    ) -> None:
        self._store = store
        self._publisher = publisher
        self._partner = partner

    def ingest(self, span: SpanSchema) -> str:
        self._store.save_checkpoint(
            span.session_id,
            {
                "trace_id": span.trace_id,
                "span_id": span.span_id,
                "tool_name": span.tool_name,
                "params": span.params,
                "token_count": span.token_count,
                "latency_ms": span.latency_ms,
                "state_hash": span.state_hash,
                "timestamp": span.timestamp.isoformat(),
            },
        )
        message_id = self._publisher.publish(span.model_dump(mode="json"))
        if self._partner:
            try:
                self._partner.export_span(span)
            except Exception:
                logger.debug("Partner export skipped", exc_info=True)
        return message_id
