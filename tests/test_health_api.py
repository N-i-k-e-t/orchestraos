"""Health dashboard API tests."""

from fastapi.testclient import TestClient

from dashboard.server import app

client = TestClient(app)


class TestHealthAPI:
    def test_health_agents(self) -> None:
        r = client.get("/health/agents")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 50
        assert data["agent_count"] >= 20
        assert "roster" in data

    def test_health_live(self) -> None:
        r = client.get("/health/live")
        assert r.status_code == 200
        data = r.json()
        assert data["redis"] in ("up", "down")
        assert len(data["services"]) >= 6
        assert "aggregate" in data
        assert "risk_score" in data["aggregate"]
