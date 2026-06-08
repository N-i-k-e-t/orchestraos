"""Pub/Sub worker — consumes raw-spans, runs detector swarm, publishes feature-vectors."""

from __future__ import annotations

import json
import logging
import signal
import sys
from typing import Any

from google.cloud import pubsub_v1

from checkpoint.redis_store import RedisStore
from detectors.swarm import DetectorSwarm
from shared.agent_runtime import AgentRuntime
from shared.config import get_redis_url, get_settings
from shared.live_state import LiveStateStore
from shared.pipeline import DETECTOR_AGENTS
from shared.pubsub import get_event_fabric
from shared.schemas import SpanSchema

logger = logging.getLogger(__name__)


class DetectorWorker:
    """Pull-based consumer for the raw-spans → feature-vectors pipeline."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._fabric = get_event_fabric()
        self._swarm = DetectorSwarm()
        store = RedisStore(redis_url=get_redis_url())
        self._runtime = AgentRuntime(LiveStateStore(store))
        self._subscriber = pubsub_v1.SubscriberClient()
        self._subscription_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_raw_spans,
        )
        self._running = True

    def setup(self) -> None:
        self._fabric.ensure_infrastructure()

    def handle_span(self, raw: dict[str, Any]) -> None:
        span = SpanSchema.model_validate(raw)
        self._runtime.set_service("detectors")
        feature_vector = self._swarm.process(span)
        for name in DETECTOR_AGENTS:
            self._runtime.record(
                span.session_id,
                name,
                loop_score=feature_vector.features.get("loop_score", 0),
                progress_score=feature_vector.features.get("progress_score", 1),
            )
        message_id = self._fabric.publish_feature_vector(feature_vector.model_dump(mode="json"))
        logger.info(
            "Processed span %s session=%s loop_score=%.2f msg=%s",
            span.span_id,
            span.session_id,
            feature_vector.features.get("loop_score", 0),
            message_id,
        )

    def _callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        try:
            payload = json.loads(message.data.decode("utf-8"))
            self.handle_span(payload)
            message.ack()
        except Exception:
            logger.exception("Failed to process message %s", message.message_id)
            message.nack()

    def run(self) -> None:
        from shared.cloudrun import start_health_server

        start_health_server()
        self.setup()
        logger.info("Detector worker listening on %s", self._subscription_path)

        streaming = self._subscriber.subscribe(self._subscription_path, callback=self._callback)

        def _shutdown(_signum, _frame):
            self._running = False
            streaming.cancel()

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        try:
            streaming.result()
        except Exception as exc:
            if self._running:
                logger.error("Worker stopped: %s", exc)
                raise


def main() -> None:
    from shared.console import configure_stdout_utf8

    configure_stdout_utf8()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    worker = DetectorWorker()
    try:
        worker.run()
    except KeyboardInterrupt:
        sys.exit(0)
