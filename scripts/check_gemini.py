#!/usr/bin/env python3
"""Live Gemini verification — one API call + AutoGPT loop e2e through RiskAgent."""

from __future__ import annotations

import sys

from detectors.swarm import DetectorSwarm
from monitor_model.gemini_client import GeminiClient
from monitor_model.risk_agent import RiskAgent
from shared.config import get_settings
from shared.schemas import SpanSchema


def _loop_features() -> dict[str, float]:
    return {
        "loop_score": 1.0,
        "progress_score": 0.1,
        "latency_score": 0.04,
        "token_score": 0.015,
        "context_score": 0.67,
        "error_score": 0.0,
    }


def main() -> int:
    settings = get_settings()
    client = GeminiClient()
    print(f"configured_model: {settings.gemini_model}")
    print(f"active_model:   {client._model_name}")
    print(f"backend: {client.backend}")
    print(f"available: {client.available}")

    if not client.available:
        print("FAIL: no Gemini backend (set GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT + Vertex)")
        return 1

    # --- Step 1: single real Gemini classify call ---
    result = client.classify(_loop_features(), loop_detected=True, repeat_count=3)
    if result is None:
        print("FAIL: Gemini classify() returned None")
        return 1

    print(
        f"Gemini classify OK — status={result['status'].value} "
        f"risk_score={result['risk_score']:.4f}"
    )

    # --- Step 2: e2e — 3rd AutoGPT loop span → DetectorSwarm → RiskAgent ---
    swarm = DetectorSwarm()
    params = {"query": "server status"}
    vector = None
    for i in range(3):
        vector = swarm.process(
            SpanSchema(
                trace_id="gemini-e2e",
                span_id=f"s{i}",
                session_id="autogpt-demo",
                tool_name="web_search",
                params=params,
                token_count=105,
                latency_ms=200,
                state_hash="abc123",
            )
        )

    assert vector is not None
    assert vector.loop_detected, "expected loop on 3rd identical web_search span"

    agent = RiskAgent(gemini=client)
    risk = agent.assess_vector(vector)

    print()
    print("=== E2E loop test (DetectorSwarm -> RiskAgent) ===")
    print(f"loop_detected: {vector.loop_detected}")
    print(f"repeat_count:  {vector.repeat_count}")
    print(f"last_source:   {agent.last_source}")
    print(f"status:        {risk.status.value}")
    print(f"risk_score:    {risk.risk_score}")
    print(f"reason:        {risk.reason}")

    if not agent.last_source.startswith("gemini:"):
        print(f"FAIL: expected Gemini path, got {agent.last_source}")
        return 1

    if risk.risk_score <= 0.8:
        print(f"FAIL: risk_score {risk.risk_score} not > 0.8")
        return 1

    print()
    print(f"PASS: Gemini ({client.backend}) drove risk assessment — score > 0.8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
