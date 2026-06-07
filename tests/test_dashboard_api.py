"""Dashboard API tests."""

from fastapi.testclient import TestClient

from dashboard.server import app

client = TestClient(app)


class TestDashboardAPI:
    def test_health(self) -> None:
        r = client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_demo_compare(self) -> None:
        r = client.get("/api/demo/compare")
        assert r.status_code == 200
        data = r.json()
        assert data["unprotected"]["calls"] == 400
        assert data["protected"]["calls"] == 5
        assert data["cost_reduction_pct"] >= 99.0

    def test_demo_run_live(self) -> None:
        r = client.post("/api/demo/run")
        assert r.status_code == 200
        data = r.json()
        assert data["protected"]["calls"] <= 5
        assert data["protected"]["outcome"] == "RECOVERED"

    def test_incidents(self) -> None:
        r = client.get("/api/incidents")
        assert r.status_code == 200
        assert len(r.json()["incidents"]) >= 3

    def test_metrics(self) -> None:
        r = client.get("/api/metrics")
        assert r.status_code == 200
        assert r.json()["cost_saved_usd"] > 40
