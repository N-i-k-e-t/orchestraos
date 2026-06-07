"""Cloud Run compatibility tests."""

from __future__ import annotations

import os
import urllib.request

from shared.cloudrun import get_listen_port, start_health_server


class TestCloudRunHelpers:
    def test_get_listen_port_uses_port_env(self, monkeypatch) -> None:
        monkeypatch.setenv("PORT", "9999")
        monkeypatch.delenv("COLLECTOR_PORT", raising=False)
        assert get_listen_port(default=8080) == 9999

    def test_get_listen_port_falls_back_to_default(self, monkeypatch) -> None:
        monkeypatch.delenv("PORT", raising=False)
        monkeypatch.delenv("COLLECTOR_PORT", raising=False)
        assert get_listen_port(default=4318) == 4318

    def test_health_server_responds(self, monkeypatch) -> None:
        monkeypatch.setenv("PORT", "18080")
        start_health_server()
        with urllib.request.urlopen("http://127.0.0.1:18080/health", timeout=2) as resp:
            assert resp.status == 200
            assert resp.read() == b"ok"
