"""Arize Phoenix OTel trace export."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from shared.config import get_phoenix_endpoint, is_partner_enabled

logger = logging.getLogger(__name__)


class ArizeExporter:
    """Exports agent spans to Arize Phoenix via OTLP HTTP."""

    def __init__(self, endpoint: str | None = None) -> None:
        self._endpoint = endpoint or get_phoenix_endpoint()
        self._enabled = is_partner_enabled("arize") and bool(self._endpoint)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def export_span(self, span: dict[str, Any]) -> bool:
        """Send a span to Phoenix OTLP /v1/traces endpoint."""
        if not self._enabled:
            return False

        otlp_payload = self._to_otlp(span)
        url = f"{self._endpoint.rstrip('/')}/v1/traces"
        try:
            resp = httpx.post(
                url,
                content=json.dumps(otlp_payload),
                headers={"Content-Type": "application/json"},
                timeout=5.0,
            )
            resp.raise_for_status()
            logger.info("Arize Phoenix export session=%s", span.get("session_id"))
            return True
        except Exception as exc:
            logger.warning("Arize export failed: %s", exc)
            return False

    @staticmethod
    def _to_otlp(span: dict[str, Any]) -> dict[str, Any]:
        trace_id = span.get("trace_id", "0" * 32)
        span_id = span.get("span_id", "0" * 16)
        return {
            "resourceSpans": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "orchestraos-agent"}},
                        {"key": "session.id", "value": {"stringValue": str(span.get("session_id", ""))}},
                    ]
                },
                "scopeSpans": [{
                    "spans": [{
                        "traceId": trace_id.replace("-", "")[:32].ljust(32, "0"),
                        "spanId": span_id.replace("-", "")[:16].ljust(16, "0"),
                        "name": str(span.get("tool_name", "tool_call")),
                        "attributes": [
                            {"key": "tool.name", "value": {"stringValue": str(span.get("tool_name", ""))}},
                            {"key": "openinference.span.kind", "value": {"stringValue": "TOOL"}},
                        ],
                    }]
                }],
            }]
        }
