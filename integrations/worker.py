"""Partner export worker — consumes breaker + remediation events."""

from __future__ import annotations

import json
import logging
import signal
import sys
import threading

from google.cloud import pubsub_v1

from integrations.partner_hub import PartnerHub
from shared.config import get_settings
from shared.pubsub import get_event_fabric

logger = logging.getLogger(__name__)


class PartnerWorker:
    """Subscribes to breaker-events and remediation-plans, exports to partners."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._fabric = get_event_fabric()
        self._hub = PartnerHub()
        self._subscriber = pubsub_v1.SubscriberClient()
        self._running = True
        self._futures: list = []

    def setup(self) -> None:
        self._fabric.ensure_infrastructure()
        enabled = [
            name
            for name, ok in [
                ("arize", self._hub.arize.enabled),
                ("mongodb", self._hub.mongodb.enabled),
                ("elastic", self._hub.elastic.enabled),
                ("dynatrace", self._hub.dynatrace.enabled),
                ("gitlab", self._hub.gitlab.enabled),
            ]
            if ok
        ]
        logger.info("Partner worker ready — enabled: %s", enabled or ["none (no-op mode)"])

    def _on_breaker(self, message: pubsub_v1.subscriber.message.Message) -> None:
        try:
            payload = json.loads(message.data.decode("utf-8"))
            self._hub.handle_breaker_event(payload)
            message.ack()
        except Exception:
            logger.exception("Partner breaker export failed")
            message.nack()

    def _on_remediation(self, message: pubsub_v1.subscriber.message.Message) -> None:
        try:
            payload = json.loads(message.data.decode("utf-8"))
            self._hub.handle_remediation_plan(payload)
            message.ack()
        except Exception:
            logger.exception("Partner remediation export failed")
            message.nack()

    def run(self) -> None:
        from shared.cloudrun import start_health_server

        start_health_server()
        self.setup()
        # Separate subscription paths for partners (avoid stealing from remediation worker)
        partners_breaker = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_partners_breaker,
        )
        partners_remediation = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_partners_remediation,
        )

        f1 = self._subscriber.subscribe(partners_breaker, callback=self._on_breaker)
        f2 = self._subscriber.subscribe(partners_remediation, callback=self._on_remediation)
        self._futures = [f1, f2]

        def _shutdown(_signum, _frame):
            self._running = False
            for f in self._futures:
                f.cancel()

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        logger.info("Partner worker listening on partners-breaker + partners-remediation subs")
        for f in self._futures:
            t = threading.Thread(target=f.result, daemon=True)
            t.start()
        try:
            while self._running:
                threading.Event().wait(1)
        except KeyboardInterrupt:
            pass


def main() -> None:
    from shared.console import configure_stdout_utf8

    configure_stdout_utf8()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        PartnerWorker().run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
