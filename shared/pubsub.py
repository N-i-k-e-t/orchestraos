"""Shared Google Pub/Sub client for the OrchestraOS event fabric."""

from __future__ import annotations

import json
import logging
from typing import Any

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import pubsub_v1

from shared.config import get_settings

logger = logging.getLogger(__name__)


class EventFabric:
    """Publishes and subscribes across OrchestraOS Pub/Sub topics."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._publisher = pubsub_v1.PublisherClient()
        self._subscriber = pubsub_v1.SubscriberClient()
        self._raw_spans_path = self._publisher.topic_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_topic_raw_spans,
        )
        self._feature_vectors_path = self._publisher.topic_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_topic_feature_vectors,
        )
        self._risk_assessments_path = self._publisher.topic_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_topic_risk_assessments,
        )
        self._raw_spans_sub_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_raw_spans,
        )
        self._feature_vectors_sub_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_feature_vectors,
        )
        self._risk_assessments_sub_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_risk_assessments,
        )
        self._breaker_events_path = self._publisher.topic_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_topic_breaker_events,
        )
        self._remediation_plans_path = self._publisher.topic_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_topic_remediation_plans,
        )
        self._breaker_events_sub_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_breaker_events,
        )
        self._remediation_plans_sub_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_remediation_plans,
        )
        self._partners_breaker_sub_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_partners_breaker,
        )
        self._partners_remediation_sub_path = self._subscriber.subscription_path(
            self._settings.gcp_project_id,
            self._settings.pubsub_subscription_partners_remediation,
        )

    def ensure_infrastructure(self) -> None:
        """Create topics and subscriptions on the local emulator."""
        if not self._settings.is_local:
            return
        self._ensure_topic(self._raw_spans_path)
        self._ensure_topic(self._feature_vectors_path)
        self._ensure_topic(self._risk_assessments_path)
        self._ensure_topic(self._breaker_events_path)
        self._ensure_topic(self._remediation_plans_path)
        self._ensure_subscription(self._raw_spans_sub_path, self._raw_spans_path)
        self._ensure_subscription(self._feature_vectors_sub_path, self._feature_vectors_path)
        self._ensure_subscription(
            self._risk_assessments_sub_path, self._risk_assessments_path
        )
        self._ensure_subscription(
            self._breaker_events_sub_path, self._breaker_events_path
        )
        self._ensure_subscription(
            self._remediation_plans_sub_path, self._remediation_plans_path
        )
        self._ensure_subscription(
            self._partners_breaker_sub_path, self._breaker_events_path
        )
        self._ensure_subscription(
            self._partners_remediation_sub_path, self._remediation_plans_path
        )

    def ensure_topic(self) -> None:
        """Backward-compatible: ensure raw-spans topic (collector startup)."""
        if not self._settings.is_local:
            return
        self._ensure_topic(self._raw_spans_path)

    def _ensure_topic(self, path: str) -> None:
        try:
            self._publisher.get_topic(request={"topic": path})
        except NotFound:
            try:
                self._publisher.create_topic(request={"name": path})
                logger.info("Created topic %s", path)
            except AlreadyExists:
                pass

    def _ensure_subscription(self, sub_path: str, topic_path: str) -> None:
        try:
            self._subscriber.get_subscription(request={"subscription": sub_path})
        except NotFound:
            try:
                self._subscriber.create_subscription(
                    request={"name": sub_path, "topic": topic_path}
                )
                logger.info("Created subscription %s", sub_path)
            except AlreadyExists:
                pass

    def publish_raw_span(self, span: dict[str, Any]) -> str:
        payload = json.dumps(span, default=str).encode("utf-8")
        future = self._publisher.publish(
            self._raw_spans_path,
            payload,
            session_id=str(span.get("session_id", "")),
            tool_name=str(span.get("tool_name", "")),
        )
        return future.result()

    def publish_feature_vector(self, feature_vector: dict[str, Any]) -> str:
        payload = json.dumps(feature_vector, default=str).encode("utf-8")
        future = self._publisher.publish(
            self._feature_vectors_path,
            payload,
            session_id=str(feature_vector.get("session_id", "")),
            span_id=str(feature_vector.get("span_id", "")),
        )
        return future.result()

    def publish_risk_assessment(self, assessment: dict[str, Any]) -> str:
        payload = json.dumps(assessment, default=str).encode("utf-8")
        future = self._publisher.publish(
            self._risk_assessments_path,
            payload,
            session_id=str(assessment.get("session_id", "")),
            status=str(assessment.get("status", "")),
        )
        return future.result()

    def publish_breaker_event(self, event: dict[str, Any]) -> str:
        payload = json.dumps(event, default=str).encode("utf-8")
        future = self._publisher.publish(
            self._breaker_events_path,
            payload,
            session_id=str(event.get("session_id", "")),
            state=str(event.get("state", "")),
        )
        return future.result()

    def publish_remediation_plan(self, plan: dict[str, Any]) -> str:
        payload = json.dumps(plan, default=str).encode("utf-8")
        future = self._publisher.publish(
            self._remediation_plans_path,
            payload,
            session_id=str(plan.get("session_id", "")),
            status=str(plan.get("status", "")),
        )
        return future.result()


_fabric: EventFabric | None = None


def get_event_fabric() -> EventFabric:
    global _fabric
    if _fabric is None:
        _fabric = EventFabric()
    return _fabric


def get_pubsub_client() -> EventFabric:
    """Backward-compatible alias used by the collector."""
    return get_event_fabric()
