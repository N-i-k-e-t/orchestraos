"""Pub/Sub worker — consumes risk-assessments, updates Redis breaker state."""

from __future__ import annotations

import json
import logging
import signal
import sys

from google.cloud import pubsub_v1

from breaker.circuit_breaker_agent import CircuitBreakerAgent
from breaker.health_agent import HealthAgent
from checkpoint.redis_store import RedisStore
from shared.agent_runtime import AgentRuntime
from shared.config import get_redis_url, get_settings
from shared.live_state import LiveStateStore
from shared.pubsub import get_event_fabric
from shared.schemas import RiskSchema

logger = logging.getLogger(__name__)


class BreakerWorker:
    """Consumes risk assessments and publishes breaker events."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._fabric = get_event_fabric()
        self._store = RedisStore(redis_url=get_redis_url())
        self._agent = CircuitBreakerAgent(self._store)
        self._health = HealthAgent(self._store)
        self._runtime = AgentRuntime(LiveStateStore(self._store))
        self._subscriber = pubsub_v1.SubscriberClient()
        self._subscription_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_risk_assessments,
        )
        self._running = True

    def setup(self) -> None:
        self._fabric.ensure_infrastructure()
        health = self._health.check()
        if health["redis"] != "up":
            raise RuntimeError("Redis is unreachable")
        logger.info("Breaker worker ready — %s", health)

    def handle_assessment(self, raw: dict) -> None:
        assessment = RiskSchema.model_validate(raw)
        self._runtime.set_service("breaker")
        event = self._agent.process_assessment(assessment)
        self._runtime.record(
            assessment.session_id,
            "CircuitBreakerAgent",
            risk_score=assessment.risk_score,
            breaker_state=event.state,
        )
        self._runtime.record(assessment.session_id, "HealthAgent", breaker_state=event.state)
        if event.state == "open":
            self._runtime.record_incident(
                {
                    "incident_id": f"{assessment.session_id}-breaker",
                    "session_id": assessment.session_id,
                    "incident_type": "breaker_trip",
                    "severity": "critical",
                    "reason": assessment.reason,
                }
            )
        message_id = self._fabric.publish_breaker_event(event.model_dump(mode="json"))
        logger.info(
            "Breaker session=%s %s→%s allowed=%s risk=%.2f msg=%s",
            event.session_id,
            event.previous_state,
            event.state,
            event.allowed,
            event.risk_score,
            message_id,
        )

    def _callback(self, message: pubsub_v1.subscriber.message.Message) -> None:
        try:
            payload = json.loads(message.data.decode("utf-8"))
            self.handle_assessment(payload)
            message.ack()
        except Exception:
            logger.exception("Failed to process risk assessment %s", message.message_id)
            message.nack()

    def run(self) -> None:
        from shared.cloudrun import start_health_server

        start_health_server()
        self.setup()
        logger.info("Breaker worker listening on %s", self._subscription_path)
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
                logger.error("Breaker worker stopped: %s", exc)
                raise


def main() -> None:
    from shared.console import configure_stdout_utf8

    configure_stdout_utf8()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        BreakerWorker().run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
