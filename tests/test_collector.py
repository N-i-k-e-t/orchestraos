"""Phase 1 collector tests."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_redis():
    store = MagicMock()
    store.ping.return_value = True
    store.load_checkpoint.return_value = None
    return store


@pytest.fixture
def mock_pubsub():
    client = MagicMock()
    client.ensure_topic.return_value = None
    client.publish_raw_span.return_value = "msg-123"
    return client


@pytest.fixture
def client(mock_redis, mock_pubsub):
    with (
        patch("collector.main.redis_store", mock_redis),
        patch("collector.main.pubsub", mock_pubsub),
        patch("collector.main.redis_store.ping", return_value=True),
        patch("collector.main._ingest_agent", None),
    ):
        import collector.main as cm

        cm._ingest_agent = None
        from collector.main import app

        with TestClient(app) as test_client:
            yield test_client, mock_redis, mock_pubsub


class TestCollector:
    def test_health(self, client):
        test_client, _, _ = client
        resp = test_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_ingest_simplified_span(self, client):
        test_client, mock_redis, mock_pubsub = client
        payload = {
            "trace_id": "abc123",
            "span_id": "span001",
            "session_id": "sess-demo",
            "tool_name": "check_status",
            "params": {"target": "server-1"},
            "token_count": 50,
            "latency_ms": 120.0,
        }
        resp = test_client.post("/v1/traces", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["accepted"] == 1
        assert body["published"] == 1
        assert body["checkpointed"] == 1
        mock_pubsub.publish_raw_span.assert_called_once()
        mock_redis.save_checkpoint.assert_called_once()

    def test_ingest_otlp_json(self, client):
        test_client, mock_redis, mock_pubsub = client
        payload = {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "session.id", "value": {"stringValue": "autogpt-1"}}
                        ]
                    },
                    "scopeSpans": [
                        {
                            "spans": [
                                {
                                    "traceId": "0123456789abcdef0123456789abcdef",
                                    "spanId": "0123456789abcdef",
                                    "name": "web_search",
                                    "startTimeUnixNano": "1700000000000000000",
                                    "endTimeUnixNano": "1700000001500000000",
                                    "attributes": [
                                        {
                                            "key": "tool.name",
                                            "value": {"stringValue": "web_search"},
                                        },
                                        {
                                            "key": "tool.params",
                                            "value": {"stringValue": '{"query": "status"}'},
                                        },
                                        {"key": "token.count", "value": {"intValue": "42"}},
                                    ],
                                }
                            ]
                        }
                    ],
                }
            ]
        }
        resp = test_client.post("/v1/traces", content=json.dumps(payload))
        assert resp.status_code == 200
        assert resp.json()["accepted"] == 1
        mock_pubsub.publish_raw_span.assert_called_once()
        mock_redis.save_checkpoint.assert_called_once()

    def test_get_checkpoint(self, client):
        test_client, mock_redis, _ = client
        mock_redis.load_checkpoint.return_value = {"tool_name": "check_status"}
        resp = test_client.get("/v1/checkpoints/sess-demo")
        assert resp.status_code == 200
        assert resp.json()["checkpoint"]["tool_name"] == "check_status"

    def test_get_checkpoint_not_found(self, client):
        test_client, mock_redis, _ = client
        mock_redis.load_checkpoint.return_value = None
        resp = test_client.get("/v1/checkpoints/missing")
        assert resp.status_code == 404

    def test_reject_empty_body(self, client):
        test_client, _, _ = client
        resp = test_client.post("/v1/traces", content=b"")
        assert resp.status_code == 400
