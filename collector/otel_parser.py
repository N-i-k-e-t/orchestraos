"""Parse OTLP HTTP JSON and OrchestraOS span payloads into SpanSchema."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from shared.schemas import SpanSchema


def _attr_value(raw: dict[str, Any]) -> Any:
    if "stringValue" in raw:
        return raw["stringValue"]
    if "intValue" in raw:
        return int(raw["intValue"])
    if "doubleValue" in raw:
        return float(raw["doubleValue"])
    if "boolValue" in raw:
        return raw["boolValue"]
    return str(raw)


def _attrs_to_dict(attributes: list[dict[str, Any]] | None) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in attributes or []:
        key = item.get("key", "")
        value = item.get("value", {})
        result[key] = _attr_value(value)
    return result


def _hex_id(value: str | bytes | None) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, bytes):
        return value.hex()
    return value


def parse_otlp_json(payload: dict[str, Any]) -> list[SpanSchema]:
    """Convert OTLP ExportTraceServiceRequest JSON to SpanSchema list."""
    spans: list[SpanSchema] = []

    for resource_span in payload.get("resourceSpans", []):
        resource_attrs = _attrs_to_dict(resource_span.get("resource", {}).get("attributes"))
        session_id = str(resource_attrs.get("session.id", resource_attrs.get("session_id", "unknown")))

        for scope_span in resource_span.get("scopeSpans", []):
            for otel_span in scope_span.get("spans", []):
                attrs = _attrs_to_dict(otel_span.get("attributes"))
                start_ns = int(otel_span.get("startTimeUnixNano", 0))
                end_ns = int(otel_span.get("endTimeUnixNano", 0))
                latency_ms = max(0.0, (end_ns - start_ns) / 1_000_000)

                params_raw = attrs.get("tool.params", attrs.get("params", "{}"))
                if isinstance(params_raw, str):
                    try:
                        params = json.loads(params_raw)
                    except json.JSONDecodeError:
                        params = {"raw": params_raw}
                elif isinstance(params_raw, dict):
                    params = params_raw
                else:
                    params = {}

                spans.append(
                    SpanSchema(
                        trace_id=_hex_id(otel_span.get("traceId")),
                        span_id=_hex_id(otel_span.get("spanId")),
                        session_id=str(attrs.get("session.id", session_id)),
                        tool_name=str(attrs.get("tool.name", otel_span.get("name", "unknown"))),
                        params=params,
                        token_count=int(attrs.get("token.count", attrs.get("token_count", 0))),
                        latency_ms=float(attrs.get("latency.ms", latency_ms)),
                        state_hash=attrs.get("state.hash"),
                        timestamp=datetime.fromtimestamp(start_ns / 1e9, tz=timezone.utc)
                        if start_ns
                        else datetime.now(timezone.utc),
                    )
                )
    return spans


def parse_payload(payload: dict[str, Any]) -> list[SpanSchema]:
    """Accept OTLP JSON or simplified OrchestraOS span dict(s)."""
    if "resourceSpans" in payload:
        return parse_otlp_json(payload)

    raw_spans = payload.get("spans", [payload])
    return [SpanSchema.model_validate(item) for item in raw_spans]
