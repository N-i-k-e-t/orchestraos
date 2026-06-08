"""Ops Center API tests."""

from dashboard.ops_api import (
    dynamics_payload,
    ops_summary_payload,
    secrets_map_payload,
    tasks_payload,
    topology_payload,
)


def test_topology_has_core_nodes() -> None:
    data = topology_payload()
    ids = {n["id"] for n in data["nodes"]}
    assert "github" in ids
    assert "gcp" in ids
    assert "cursor" in ids
    assert "collector" in ids
    assert data["project_id"] == "orchestraos-498316"


def test_secrets_map_no_values() -> None:
    data = secrets_map_payload()
    assert all("value" not in s for s in data["secrets"])
    assert "redis-url" in {s["id"] for s in data["secrets"]}


def test_tasks_payload() -> None:
    data = tasks_payload()
    assert data["summary"]["total"] >= 10
    assert any(t["status"] == "done" for t in data["tasks"])


def test_dynamics_pipeline_stages() -> None:
    data = dynamics_payload()
    assert len(data["pipeline"]) == 6
    assert data["roster_total"] >= 50


def test_ops_summary() -> None:
    data = ops_summary_payload()
    assert "health" in data
    assert data["health"]["roster_total"] >= 50
