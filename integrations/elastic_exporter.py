"""Elastic log shipping."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from shared.config import get_elastic_api_key, get_elastic_url, is_partner_enabled

logger = logging.getLogger(__name__)


class ElasticExporter:
    """Indexes OrchestraOS events into Elasticsearch."""

    INDEX = "orchestraos-events"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self._url = base_url or get_elastic_url()
        self._api_key = api_key or get_elastic_api_key()
        self._enabled = is_partner_enabled("elastic") and bool(self._url)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def index_event(self, event_type: str, payload: dict[str, Any]) -> bool:
        if not self._enabled:
            return False

        doc = {
            "@timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "service": "orchestraos",
            **payload,
        }
        url = f"{self._url.rstrip('/')}/{self.INDEX}/_doc"
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"ApiKey {self._api_key}"

        try:
            resp = httpx.post(url, json=doc, headers=headers, timeout=5.0)
            resp.raise_for_status()
            logger.info("Elastic indexed event=%s session=%s", event_type, payload.get("session_id"))
            return True
        except Exception as exc:
            logger.warning("Elastic export failed: %s", exc)
            return False
