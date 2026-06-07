"""Pub/Sub worker — consumes breaker-events and runs remediation orchestrator."""

from __future__ import annotations

import json
import logging
import signal
import sys

from google.cloud import pubsub_v1

from checkpoint.redis_store import RedisStore
from remediation.orchestrator import RemediationOrchestrator
from shared.config import get_redis_url, get_settings
from shared.pubsub import get_event_fabric
from shared.schemas import BreakerEventSchema

logger = logging.getLogger(__name__)


class RemediationWorker:
    """Consumes breaker events and publishes remediation plans."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._fabric = get_event_fabric()
        self._store = RedisStore(redis_url=get_redis_url())
        self._orchestrator = RemediationOrchestrator(self._store)
        self._subscriber = pubsub_v1.SubscriberClient()
        self._subscription_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_breaker_events,
        )
        self._running = True

    def setup(self) -> None:
        self._fabric.ensure_infrastructure()
        if not self._store.ping():
            raise RuntimeError("Redis is unreachable")
        logger.info("Remediation worker ready")

    def handle_event(self, raw: dict) -> None:
        event = BreakerEventSchema.model_validate(raw)
        plan = self._orchestrator.handle_breaker_event(event)
        if plan is None:
            return
        message_id = self._fabric.publish_remediation_plan(plan.model_dump(mode="json"))
        logger.info(
            "Remediation session=%s status=%s attempt=%d steps=%d msg=%s",
            plan.session_id,
            plan.status,
            plan.attempt,
            plan.total_steps,
            message_id,
        )

    def _callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        try:
            payload = json.loads(message.data.decode("utf-8"))
            self.handle_event(payload)
            message.ack()
        except Exception:
            logger.exception("Failed to process breaker event %s", message.message_id)
            message.nack()

    def run(self) -> None:
        from shared.cloudrun import start_health_server

        start_health_server()
        self.setup()
        logger.info("Remediation worker listening on %s", self._subscription_path)
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
                logger.error("Remediation worker stopped: %s", exc)
                raise


def main() -> None:
    from shared.console import configure_stdout_utf8

    configure_stdout_utf8()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        RemediationWorker().run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
