"""Ops Center API — topology, tasks, agent dynamics, secrets map."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from dashboard.health_api import agents_payload, live_payload

_REPO = "https://github.com/N-i-k-e-t/orchestraos"
_GCP_PROJECT = "orchestraos-498316"
_REGION = "us-central1"


def _load_gcp_config() -> dict[str, Any]:
    path = Path(__file__).resolve().parent.parent / "configs" / "gcp.yaml"
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def _dashboard_url(cfg: dict[str, Any]) -> str:
    return (
        cfg.get("live_dashboard_url")
        or os.getenv("LIVE_DASHBOARD_URL")
        or "https://orchestraos-dashboard-ew3uwemnxq-uc.a.run.app"
    )


def topology_payload() -> dict[str, Any]:
    cfg = _load_gcp_config()
    dashboard_url = _dashboard_url(cfg)
    collector_url = dashboard_url.replace("dashboard", "collector")
    live = live_payload()
    service_status = {s["service"]: s["status"] for s in live.get("services", [])}

    nodes = [
        {
            "id": "cursor",
            "label": "Cursor IDE",
            "layer": "dev",
            "status": "ok",
            "detail": "Local dev, agents, pytest, Cloud Build triggers",
            "links": [],
        },
        {
            "id": "antigravity",
            "label": "Antigravity",
            "layer": "dev",
            "status": "ok",
            "detail": "Team AI prompts (Ayush GCP, Rutuja monitor)",
            "links": [{"label": "docs", "url": f"{_REPO}/tree/main/docs/setup"}],
        },
        {
            "id": "github",
            "label": "GitHub",
            "layer": "source",
            "status": "ok",
            "detail": "orchestraos — main, dev, teammate branches",
            "links": [{"label": "repo", "url": _REPO}],
        },
        {
            "id": "gcp",
            "label": f"GCP {_GCP_PROJECT}",
            "layer": "cloud",
            "status": "ok" if live.get("redis") == "up" else "degraded",
            "detail": f"{_REGION} · Cloud Run · Pub/Sub · Memorystore",
            "links": [
                {"label": "console", "url": f"https://console.cloud.google.com/home/dashboard?project={_GCP_PROJECT}"}
            ],
        },
        {
            "id": "secret-manager",
            "label": "Secret Manager",
            "layer": "cloud",
            "status": "ok" if live.get("redis") == "up" else "standby",
            "detail": "gemini-api-key, redis-url, phoenix-endpoint, …",
            "links": [],
        },
        {
            "id": "vertex",
            "label": "Vertex AI / Gemini",
            "layer": "cloud",
            "status": service_status.get("monitor", "standby"),
            "detail": "RiskAgent primary path on monitor worker",
            "links": [],
        },
        {
            "id": "external-agent",
            "label": "External AI Agent",
            "layer": "edge",
            "status": "ok",
            "detail": "AutoGPT, LangGraph, CrewAI → OTLP spans",
            "links": [],
        },
    ]

    run_services = cfg.get("services") or {}
    pipeline = [
        ("collector", "raw-spans", collector_url),
        ("detectors", "feature-vectors", None),
        ("monitor", "risk-assessments", None),
        ("breaker", "breaker-events", None),
        ("remediation", "remediation-plans", None),
        ("partners", "exports", None),
        ("dashboard", "UI + health", dashboard_url),
    ]
    for svc_key, topic, url in pipeline:
        nodes.append(
            {
                "id": svc_key,
                "label": run_services.get(svc_key, f"orchestraos-{svc_key}"),
                "layer": "pipeline",
                "status": service_status.get(svc_key, "standby"),
                "detail": topic,
                "links": [{"label": "url", "url": url}] if url else [],
            }
        )

    edges = [
        {"from": "cursor", "to": "github", "label": "git push"},
        {"from": "antigravity", "to": "cursor", "label": "prompts / setup"},
        {"from": "github", "to": "gcp", "label": "Cloud Build"},
        {"from": "gcp", "to": "secret-manager", "label": "IAM + secrets"},
        {"from": "secret-manager", "to": "collector", "label": "redis-url, keys"},
        {"from": "vertex", "to": "monitor", "label": "Gemini risk"},
        {"from": "external-agent", "to": "collector", "label": "POST /v1/traces"},
        {"from": "collector", "to": "detectors", "label": "Pub/Sub"},
        {"from": "detectors", "to": "monitor", "label": "Pub/Sub"},
        {"from": "monitor", "to": "breaker", "label": "Pub/Sub"},
        {"from": "breaker", "to": "remediation", "label": "Pub/Sub"},
        {"from": "breaker", "to": "partners", "label": "Pub/Sub"},
        {"from": "remediation", "to": "partners", "label": "Pub/Sub"},
        {"from": "dashboard", "to": "gcp", "label": "reads Redis live state"},
    ]

    branches = [
        {"name": "main", "owner": "release", "role": "Devpost / protected"},
        {"name": "dev", "owner": "team", "role": "integration branch"},
        {"name": "niket/backbone", "owner": "Niket", "role": "pipeline + agents"},
        {"name": "ayush/dashboard", "owner": "Ayush", "role": "GCP deploy + UI"},
        {"name": "rutuja/monitor", "owner": "Rutuja", "role": "Gemini / monitor worker"},
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "branches": branches,
        "project_id": _GCP_PROJECT,
        "region": _REGION,
        "dashboard_url": dashboard_url,
        "collector_url": collector_url,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def secrets_map_payload() -> dict[str, Any]:
    cfg = _load_gcp_config()
    live = live_payload()
    redis_ok = live.get("redis") == "up"

    entries = [
        {
            "id": "redis-url",
            "source": "Memorystore orchestraos-redis",
            "consumers": ["collector", "detectors", "monitor", "breaker", "remediation", "dashboard"],
            "status": "configured" if redis_ok else "missing",
            "env_var": "REDIS_URL",
        },
        {
            "id": "gemini-api-key",
            "source": "Google AI / fallback",
            "consumers": ["monitor", "detectors", "breaker", "remediation"],
            "status": "check",
            "env_var": "GEMINI_API_KEY",
            "note": "Vertex AI primary on GCP; API key is fallback",
        },
        {
            "id": "phoenix-endpoint",
            "source": "Arize Phoenix",
            "consumers": ["collector", "partners"],
            "status": "check",
            "env_var": "PHOENIX_COLLECTOR_ENDPOINT",
        },
        {
            "id": "mongodb-uri",
            "source": "MongoDB Atlas",
            "consumers": ["partners", "remediation", "learning"],
            "status": "optional",
            "env_var": "MONGODB_URI",
        },
        {
            "id": "arize-api-key",
            "source": "Arize",
            "consumers": ["partners"],
            "status": "optional",
            "env_var": "ARIZE_API_KEY",
        },
    ]
    for extra in cfg.get("secrets", []):
        if extra in {e["id"] for e in entries}:
            continue
        entries.append(
            {
                "id": extra,
                "source": "Secret Manager",
                "consumers": ["partners"],
                "status": "optional",
                "env_var": extra.upper().replace("-", "_"),
            }
        )

    return {
        "secrets": entries,
        "service_accounts": {
            "deploy": f"orchestraos-sa@{_GCP_PROJECT}.iam.gserviceaccount.com",
            "runtime": f"orchestra-runtime@{_GCP_PROJECT}.iam.gserviceaccount.com",
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def tasks_payload() -> dict[str, Any]:
    live = live_payload()
    all_ok = all(s.get("status") in ("ok", "standby") for s in live.get("services", []))
    redis_ok = live.get("redis") == "up"

    tasks = [
        {"id": "t1", "title": "Agent pipeline wired + 104 tests", "owner": "Niket", "status": "done", "priority": "P0"},
        {"id": "t2", "title": "Push code to GitHub (all branches)", "owner": "Niket", "status": "done", "priority": "P0"},
        {"id": "t3", "title": "Memorystore Redis + VPC connector", "owner": "Ayush", "status": "done" if redis_ok else "pending", "priority": "P0"},
        {"id": "t4", "title": "Deploy 7 Cloud Run services", "owner": "Ayush", "status": "done" if all_ok else "in_progress", "priority": "P0"},
        {"id": "t5", "title": "Live /health/agents returns 200", "owner": "Ayush", "status": "done", "priority": "P0"},
        {"id": "t6", "title": "Set real gemini-api-key + phoenix-endpoint", "owner": "Niket", "status": "pending", "priority": "P0"},
        {"id": "t7", "title": "Record 3-min hackathon video", "owner": "All", "status": "pending", "priority": "P0"},
        {"id": "t8", "title": "Fill Devpost submission", "owner": "Niket", "status": "pending", "priority": "P0"},
        {"id": "t9", "title": "Phoenix / Arize screenshots", "owner": "Rutuja", "status": "pending", "priority": "P0"},
        {"id": "t10", "title": "Grant teammate Secret Manager access", "owner": "Niket", "status": "pending", "priority": "P1"},
        {"id": "t11", "title": "Live Vertex test on monitor worker", "owner": "Rutuja", "status": "pending", "priority": "P1"},
        {"id": "t12", "title": "MongoDB Atlas for learning agents", "owner": "Niket", "status": "pending", "priority": "P2"},
    ]
    done = sum(1 for t in tasks if t["status"] == "done")
    return {
        "tasks": tasks,
        "summary": {"total": len(tasks), "done": done, "pending": len(tasks) - done},
        "deadline": "2026-06-11",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def dynamics_payload() -> dict[str, Any]:
    live = live_payload()
    agents = agents_payload()
    firing = set(agents.get("agents_firing", []))

    pipeline_stages = [
        {"stage": "Ingest", "service": "collector", "agents": ["SpanIngestAgent", "OtelParserAgent"]},
        {"stage": "Detect", "service": "detectors", "agents": ["LoopAgent", "TokenAgent", "DetectorSwarm"]},
        {"stage": "Reason", "service": "monitor", "agents": ["RiskAgent", "GroundingAgent", "ConfidenceAgent"]},
        {"stage": "Break", "service": "breaker", "agents": ["CircuitBreakerAgent", "HealthAgent"]},
        {"stage": "Recover", "service": "remediation", "agents": ["RetryAgent", "FallbackToolAgent", "LearningCoordinator"]},
        {"stage": "Export", "service": "partners", "agents": ["PartnerHub", "ArizeExporter", "PhoenixMcpClient"]},
    ]

    svc_status = {s["service"]: s["status"] for s in live.get("services", [])}
    for stage in pipeline_stages:
        stage["status"] = svc_status.get(stage["service"], "unknown")
        stage["active_count"] = sum(1 for a in stage["agents"] if a in firing)

    domains: dict[str, int] = {}
    for entry in agents.get("roster", []):
        if entry.get("kind") != "agent":
            continue
        d = str(entry.get("domain", "Other"))
        domains[d] = domains.get(d, 0) + 1

    return {
        "pipeline": pipeline_stages,
        "agents_firing": agents.get("agents_firing", []),
        "active_agent_count": live.get("active_agent_count", 0),
        "sessions": live.get("sessions", []),
        "incidents": live.get("incidents", [])[:10],
        "aggregate": live.get("aggregate", {}),
        "domains": domains,
        "roster_total": agents.get("total", 0),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def ops_summary_payload() -> dict[str, Any]:
    live = live_payload()
    agents = agents_payload()
    tasks = tasks_payload()
    return {
        "health": {
            "redis": live.get("redis"),
            "services_ok": sum(1 for s in live.get("services", []) if s.get("status") == "ok"),
            "services_total": len(live.get("services", [])),
            "active_agents": live.get("active_agent_count", 0),
            "roster_total": agents.get("total", 0),
        },
        "tasks": tasks["summary"],
        "topology": {"project": _GCP_PROJECT, "region": _REGION},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
