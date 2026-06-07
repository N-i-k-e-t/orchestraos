"""Phase 8 partner integration tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from integrations.arize_exporter import ArizeExporter
from integrations.dynatrace_exporter import DynatraceExporter
from integrations.elastic_exporter import ElasticExporter
from integrations.gitlab_fallback import GitLabFallback
from integrations.mongodb_store import MongoIncidentStore
from integrations.partner_hub import PartnerHub
from shared.schemas import BreakerEventSchema, RemediationPlanSchema


class TestArizeExporter:
    @patch("integrations.arize_exporter.is_partner_enabled", return_value=True)
    @patch("integrations.arize_exporter.httpx.post")
    def test_export_span_success(self, mock_post, _enabled) -> None:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        exporter = ArizeExporter(endpoint="http://phoenix:6006")
        assert exporter.enabled
        assert exporter.export_span({"session_id": "s1", "tool_name": "search", "trace_id": "abc"})
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0].endswith("/v1/traces")

    @patch("integrations.arize_exporter.is_partner_enabled", return_value=False)
    def test_export_span_disabled(self, _enabled) -> None:
        exporter = ArizeExporter(endpoint="http://phoenix:6006")
        assert not exporter.export_span({"session_id": "s1"})


class TestMongoIncidentStore:
    @patch("integrations.mongodb_store.is_partner_enabled", return_value=True)
    def test_save_incident(self, _enabled) -> None:
        mock_collection = MagicMock()
        store = MongoIncidentStore(uri="mongodb://localhost:27017")
        store._collection = MagicMock(return_value=mock_collection)  # noqa: SLF001

        incident_id = store.save_incident(
            "sess-1",
            incident_type="breaker_trip",
            severity="critical",
            reason="loop detected",
            details={"risk_score": 0.9},
        )
        assert incident_id is not None
        mock_collection.insert_one.assert_called_once()

    @patch("integrations.mongodb_store.is_partner_enabled", return_value=False)
    def test_save_incident_disabled(self, _enabled) -> None:
        store = MongoIncidentStore(uri="mongodb://localhost:27017")
        assert store.save_incident("s1", "breaker_trip", "critical", "reason") is None


class TestElasticExporter:
    @patch("integrations.elastic_exporter.is_partner_enabled", return_value=True)
    @patch("integrations.elastic_exporter.httpx.post")
    def test_index_event(self, mock_post, _enabled) -> None:
        mock_post.return_value = MagicMock(status_code=201)
        mock_post.return_value.raise_for_status = MagicMock()
        exporter = ElasticExporter(base_url="http://elastic:9200", api_key="key")
        assert exporter.index_event("breaker_trip", {"session_id": "s1"})
        mock_post.assert_called_once()


class TestDynatraceExporter:
    @patch("integrations.dynatrace_exporter.is_partner_enabled", return_value=True)
    @patch("integrations.dynatrace_exporter.httpx.post")
    def test_send_event(self, mock_post, _enabled) -> None:
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.raise_for_status = MagicMock()
        exporter = DynatraceExporter(base_url="https://dt.example.com", token="tok")
        assert exporter.send_event("remediation", {"session_id": "s1", "status": "recovered"})
        mock_post.assert_called_once()


class TestGitLabFallback:
    @patch("integrations.gitlab_fallback.is_partner_enabled", return_value=True)
    @patch("integrations.gitlab_fallback.httpx.post")
    def test_create_escalation_issue(self, mock_post, _enabled) -> None:
        mock_post.return_value = MagicMock(status_code=201)
        mock_post.return_value.raise_for_status = MagicMock()
        gitlab = GitLabFallback(
            base_url="https://gitlab.com",
            token="glpat-test",
            project_id="123",
        )
        assert gitlab.create_escalation_issue("sess-1", "max retries", {"attempt": 5})
        mock_post.assert_called_once()


class TestPartnerHub:
    def _hub_with_mocks(self) -> PartnerHub:
        hub = PartnerHub()
        hub.arize = MagicMock(enabled=True, export_span=MagicMock(return_value=True))
        hub.phoenix_mcp = MagicMock(enabled=True, register_session=MagicMock(return_value=True))
        hub.mongodb = MagicMock(enabled=True, save_incident=MagicMock(return_value="inc-1"))
        hub.elastic = MagicMock(enabled=True, index_event=MagicMock(return_value=True))
        hub.dynatrace = MagicMock(enabled=True, send_event=MagicMock(return_value=True))
        hub.gitlab = MagicMock(enabled=True, create_escalation_issue=MagicMock(return_value=True))
        return hub

    def test_export_span_delegates_to_arize(self) -> None:
        hub = self._hub_with_mocks()
        hub.phoenix_mcp = MagicMock(enabled=True, register_session=MagicMock(return_value=True))
        results = hub.export_span({"session_id": "s1", "tool_name": "search", "trace_id": "t1"})
        assert results["arize_otlp"] is True
        assert results["arize_mcp"] is True
        hub.arize.export_span.assert_called_once()
        hub.phoenix_mcp.register_session.assert_called_once()

    def test_handle_breaker_event_open_exports(self) -> None:
        hub = self._hub_with_mocks()
        event = BreakerEventSchema(
            session_id="loop-demo",
            state="open",
            risk_score=0.92,
            allowed=False,
            reason="tool loop",
        )
        results = hub.handle_breaker_event(event)
        assert results["mongodb"] is True
        assert results["elastic"] is True
        assert results["dynatrace"] is True
        hub.mongodb.save_incident.assert_called_once()

    def test_handle_breaker_event_closed_noop(self) -> None:
        hub = self._hub_with_mocks()
        event = BreakerEventSchema(
            session_id="ok",
            state="closed",
            risk_score=0.1,
            allowed=True,
        )
        assert hub.handle_breaker_event(event) == {}

    def test_handle_remediation_escalation_creates_gitlab_issue(self) -> None:
        hub = self._hub_with_mocks()
        plan = RemediationPlanSchema(
            plan_id="p1",
            session_id="sess-1",
            status="escalated",
            attempt=5,
            recovered=False,
        )
        results = hub.handle_remediation_plan(plan)
        assert results["gitlab"] is True
        hub.gitlab.create_escalation_issue.assert_called_once()

    def test_handle_remediation_recovered_no_gitlab(self) -> None:
        hub = self._hub_with_mocks()
        plan = RemediationPlanSchema(
            plan_id="p2",
            session_id="sess-2",
            status="recovered",
            attempt=3,
            recovered=True,
        )
        results = hub.handle_remediation_plan(plan)
        assert results["gitlab"] is False
        hub.gitlab.create_escalation_issue.assert_not_called()
