"""MongoDB Atlas incident persistence."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from shared.config import get_mongodb_uri, is_partner_enabled

logger = logging.getLogger(__name__)


class MongoIncidentStore:
    """Stores incidents and remediation plans in MongoDB Atlas."""

    DB_NAME = "orchestraos"
    INCIDENTS_COLLECTION = "incidents"

    def __init__(self, uri: str | None = None) -> None:
        self._uri = uri or get_mongodb_uri()
        self._enabled = is_partner_enabled("mongodb") and bool(self._uri)
        self._client = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _collection(self):
        if self._client is None:
            from pymongo import MongoClient

            self._client = MongoClient(self._uri, serverSelectionTimeoutMS=3000)
        return self._client[self.DB_NAME][self.INCIDENTS_COLLECTION]

    def save_incident(
        self,
        session_id: str,
        incident_type: str,
        severity: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> str | None:
        if not self._enabled:
            return None

        doc = {
            "incident_id": str(uuid.uuid4()),
            "session_id": session_id,
            "incident_type": incident_type,
            "severity": severity,
            "reason": reason,
            "details": details or {},
            "created_at": datetime.now(timezone.utc),
        }
        try:
            self._collection().insert_one(doc)
            logger.info("MongoDB incident saved session=%s type=%s", session_id, incident_type)
            return doc["incident_id"]
        except Exception as exc:
            logger.warning("MongoDB save failed: %s", exc)
            return None

    def list_incidents(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._enabled:
            return []
        try:
            cursor = self._collection().find().sort("created_at", -1).limit(limit)
            return [{**doc, "_id": str(doc["_id"])} for doc in cursor]
        except Exception as exc:
            logger.warning("MongoDB list failed: %s", exc)
            return []
