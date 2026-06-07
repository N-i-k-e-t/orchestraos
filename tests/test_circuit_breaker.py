"""Unit tests for CircuitBreaker."""

import time
from unittest.mock import patch

from breaker.circuit_breaker import BreakerState, CircuitBreaker
from tests.conftest import FakeRedisStore


class TestCircuitBreaker:
    def setup_method(self) -> None:
        self.store = FakeRedisStore()
        self.breaker = CircuitBreaker(self.store, "sess-1", threshold=0.8, cooldown_sec=1)

    def test_starts_closed(self) -> None:
        assert self.breaker.state == BreakerState.CLOSED
        assert self.breaker.allow_call() is True

    def test_trips_on_high_risk(self) -> None:
        state = self.breaker.record_risk(0.9)
        assert state == BreakerState.OPEN
        assert self.breaker.allow_call() is False

    def test_does_not_trip_below_threshold(self) -> None:
        state = self.breaker.record_risk(0.5)
        assert state == BreakerState.CLOSED
        assert self.breaker.allow_call() is True

    def test_half_open_after_cooldown(self) -> None:
        self.breaker.record_risk(0.95)
        assert self.breaker.allow_call() is False

        with patch("breaker.circuit_breaker.time") as mock_time:
            mock_time.time.return_value = time.time() + 60
            assert self.breaker.allow_call() is True
            assert self.breaker.state == BreakerState.HALF_OPEN

    def test_reset_returns_to_closed(self) -> None:
        self.breaker.record_risk(0.95)
        self.breaker.reset()
        assert self.breaker.state == BreakerState.CLOSED
