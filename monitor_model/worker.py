"""Pub/Sub worker — consumes feature-vectors, publishes risk-assessments."""

from __future__ import annotations

import json
import logging
import signal
import sys

from google.cloud import pubsub_v1

from checkpoint.redis_store import RedisStore
from monitor_model.agent_builder import MonitorAgentBuilder
from shared.agent_runtime import AgentRuntime
from shared.config import get_redis_url, get_settings
from shared.live_state import LiveStateStore
from shared.pubsub import get_event_fabric
from shared.schemas import FeatureVectorSchema

logger = logging.getLogger(__name__)


class MonitorWorker:
    """Consumes fused feature vectors and publishes risk assessments."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._fabric = get_event_fabric()
        self._agent_builder = MonitorAgentBuilder()
        store = RedisStore(redis_url=get_redis_url())
        self._runtime = AgentRuntime(LiveStateStore(store))
        self._subscriber = pubsub_v1.SubscriberClient()
        self._subscription_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_feature_vectors,
        )
        self._running = True

    def setup(self) -> None:
        self._fabric.ensure_infrastructure()

    def handle_feature_vector(self, raw: dict) -> None:
        vector = FeatureVectorSchema.model_validate(raw)
        self._runtime.set_service("monitor")
        assessment = self._agent_builder.execute_vector(vector)
        for name in ("RiskAgent", "GroundingAgent", "ConfidenceAgent", "MonitorAgentBuilder"):
            self._runtime.record(
                vector.session_id,
                name,
                risk_score=assessment.risk_score,
                loop_score=vector.features.get("loop_score", 0),
                progress_score=vector.features.get("progress_score", 1),
            )
        if "gemini:" in assessment.reason:
            self._runtime.record(vector.session_id, "GeminiClient", risk_score=assessment.risk_score)
        payload = assessment.model_dump(mode="json")
        message_id = self._fabric.publish_risk_assessment(payload)
        logger.info(
            "Risk assessed session=%s status=%s score=%.2f msg=%s",
            assessment.session_id,
            assessment.status.value,
            assessment.risk_score,
            message_id,
        )

    def _callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        try:
            payload = json.loads(message.data.decode("utf-8"))
            self.handle_feature_vector(payload)
            message.ack()
        except Exception:
            logger.exception("Failed to process feature vector %s", message.message_id)
            message.nack()

    def run(self) -> None:
        from shared.cloudrun import start_health_server

        start_health_server()
        self.setup()
        logger.info("Monitor worker listening on %s", self._subscription_path)
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
                logger.error("Monitor worker stopped: %s", exc)
                raise


def main() -> None:
    from shared.console import configure_stdout_utf8

    configure_stdout_utf8()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        MonitorWorker().run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
