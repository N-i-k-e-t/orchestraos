"""Unit tests for RedisStore."""

import json
from unittest.mock import MagicMock, patch

from checkpoint.redis_store import RedisStore


class TestRedisStore:
    def setup_method(self) -> None:
        self.mock_client = MagicMock()
        with patch("checkpoint.redis_store.redis.from_url", return_value=self.mock_client):
            self.store = RedisStore(redis_url="redis://localhost:6379/0")

    def test_save_and_load_checkpoint(self) -> None:
        data = {"step": 5, "tokens": 250}
        self.mock_client.get.return_value = json.dumps(data)

        self.store.save_checkpoint("sess-1", data)
        self.mock_client.setex.assert_called_once()

        result = self.store.load_checkpoint("sess-1")
        assert result == data

    def test_load_checkpoint_returns_none_when_missing(self) -> None:
        self.mock_client.get.return_value = None
        assert self.store.load_checkpoint("missing") is None

    def test_store_and_get_breaker_state(self) -> None:
        state = {"state": "open", "tripped_at": 12345.0}
        self.mock_client.get.return_value = json.dumps(state)

        self.store.store_breaker_state("sess-1", state)
        self.mock_client.setex.assert_called_once()

        result = self.store.get_breaker_state("sess-1")
        assert result == state

    def test_get_breaker_state_returns_none_when_missing(self) -> None:
        self.mock_client.get.return_value = None
        assert self.store.get_breaker_state("missing") is None

    def test_ping(self) -> None:
        self.mock_client.ping.return_value = True
        assert self.store.ping() is True
