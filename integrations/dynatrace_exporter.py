"""Dynatrace APM event ingest."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from shared.config import get_dynatrace_token, get_dynatrace_url, is_partner_enabled

logger = logging.getLogger(__name__)


class DynatraceExporter:
    """Sends custom events and metrics to Dynatrace."""

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self._url = base_url or get_dynatrace_url()
        self._token = token or get_dynatrace_token()
        self._enabled = is_partner_enabled("dynatrace") and bool(self._url and self._token)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def send_event(self, event_type: str, payload: dict[str, Any]) -> bool:
        if not self._enabled:
            return False

        body = {
            "eventType": "ORCHESTRAOS_EVENT",
            "title": f"OrchestraOS {event_type}",
            "entityName": f"agent-session-{payload.get('session_id', 'unknown')}",
            "properties": {
                "event_type": event_type,
                **{k: str(v) for k, v in payload.items()},
            },
            "timestamp": int(time.time() * 1000),
        }
        url = f"{self._url.rstrip('/')}/api/v2/events/ingest"
        headers = {
            "Authorization": f"Api-Token {self._token}",
            "Content-Type": "application/json",
        }
        try:
            resp = httpx.post(url, json={"events": [body]}, headers=headers, timeout=5.0)
            resp.raise_for_status()
            logger.info("Dynatrace event=%s session=%s", event_type, payload.get("session_id"))
            return True
        except Exception as exc:
            logger.warning("Dynatrace export failed: %s", exc)
            return False
