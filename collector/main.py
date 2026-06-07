"""Phase 1 — FastAPI OTLP collector: receive spans → Pub/Sub → Redis checkpoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import ValidationError

from checkpoint.redis_store import RedisStore
from collector.otel_parser import parse_payload
from shared.cloudrun import get_listen_port
from shared.config import get_redis_url, get_settings
from shared.pubsub import get_pubsub_client
from shared.schemas import SpanSchema, TraceIngestResponse

logger = logging.getLogger(__name__)
settings = get_settings()
redis_store = RedisStore(redis_url=get_redis_url())
pubsub = get_pubsub_client()
_partner_hub = None


def _get_partner_hub():
    """Lazy PartnerHub for optional Arize span export."""
    global _partner_hub
    if _partner_hub is None:
        from integrations.partner_hub import PartnerHub

        _partner_hub = PartnerHub()
    return _partner_hub


def _maybe_export_to_partners(span: SpanSchema) -> None:
    try:
        hub = _get_partner_hub()
        if hub.arize.enabled:
            hub.export_span(span)
    except Exception:
        logger.debug("Partner span export skipped", exc_info=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    pubsub.ensure_topic()
    if not redis_store.ping():
        raise RuntimeError("Redis is unreachable")
    logger.info("Collector ready — Redis OK, Pub/Sub topic ensured")
    yield


app = FastAPI(
    title="OrchestraOS Collector",
    description="OTLP HTTP receiver on :4318 → Pub/Sub raw-spans → Redis checkpoint",
    version="0.1.0",
    lifespan=lifespan,
)


def _checkpoint_span(span: SpanSchema) -> None:
    """Persist latest span snapshot for the session."""
    redis_store.save_checkpoint(
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.otel_service_name,
        "redis": "up" if redis_store.ping() else "down",
    }


@app.post("/v1/traces")
async def ingest_traces(request: Request) -> TraceIngestResponse:
    """
    OTLP HTTP trace ingestion endpoint (port 4318).

    Accepts application/json (OTLP or simplified OrchestraOS span format).
    """
    content_type = request.headers.get("content-type", "application/json")
    body = await request.body()

    if not body:
        raise HTTPException(status_code=400, detail="Empty request body")

    if "json" not in content_type:
        raise HTTPException(
            status_code=415,
            detail="Phase 1 supports application/json OTLP payloads",
        )

    import json

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

    accepted: list[dict[str, str]] = []
    rejected: list[str] = []
    published = 0
    checkpointed = 0

    try:
        spans = parse_payload(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    for span in spans:
        try:
            record = span.model_dump(mode="json")
            message_id = pubsub.publish_raw_span(record)
            _checkpoint_span(span)
            _maybe_export_to_partners(span)
            published += 1
            checkpointed += 1
            accepted.append(
                {
                    "span_id": span.span_id,
                    "session_id": span.session_id,
                    "status": "accepted",
                    "message_id": message_id,
                }
            )
        except Exception as exc:
            logger.exception("Failed to process span %s", span.span_id)
            rejected.append(str(exc))

    if not accepted and rejected:
        raise HTTPException(status_code=422, detail={"errors": rejected})

    return TraceIngestResponse(
        accepted=len(accepted),
        rejected=len(rejected),
        published=published,
        checkpointed=checkpointed,
        spans=accepted,
    )


@app.get("/v1/checkpoints/{session_id}")
async def get_checkpoint(session_id: str) -> dict[str, Any]:
    """Debug endpoint — read latest Redis checkpoint for a session."""
    data = redis_store.load_checkpoint(session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return {"session_id": session_id, "checkpoint": data}


@app.options("/v1/traces")
async def otlp_options() -> Response:
    """CORS preflight for OTLP HTTP exporters."""
    return Response(status_code=204)


def main() -> None:
    import uvicorn

    from shared.console import configure_stdout_utf8

    configure_stdout_utf8()
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(
        "collector.main:app",
        host=settings.collector_host,
        port=get_listen_port(default=settings.collector_port),
        reload=False,
    )


if __name__ == "__main__":
    main()
