#!/usr/bin/env python3
"""Verify OrchestraOS secrets resolve (names + bool only — never values)."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable

from shared.config import (
    get_arize_api_key,
    get_gemini_api_key,
    get_mongodb_uri,
    get_phoenix_endpoint,
    get_redis_url,
    get_settings,
)

# secret_id, env_var, getter, required for exit code
SECRET_SPECS: list[tuple[str, str, Callable[[], str], bool]] = [
    ("gemini-api-key", "GEMINI_API_KEY", get_gemini_api_key, True),
    ("mongodb-uri", "MONGODB_URI", get_mongodb_uri, False),
    ("arize-api-key", "ARIZE_API_KEY", get_arize_api_key, False),
    ("redis-url", "REDIS_URL", get_redis_url, True),
    ("phoenix-endpoint", "PHOENIX_COLLECTOR_ENDPOINT", get_phoenix_endpoint, False),
]


def _gemini_satisfied() -> bool:
    """API key or Vertex AI backend counts as gemini-api-key satisfied."""
    if bool(get_gemini_api_key()):
        return True
    if not os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PUBSUB_EMULATOR_HOST"):
        return False
    try:
        from monitor_model.gemini_client import GeminiClient

        client = GeminiClient()
        return client.available and client.backend == "vertex"
    except Exception:
        return False


def main() -> int:
    settings = get_settings()
    print(f"settings.gcp_project_id = {settings.gcp_project_id}")
    print(f"settings.gemini_model   = {settings.gemini_model}")
    print(f"settings.is_local       = {settings.is_local}")
    print()

    missing_required: list[str] = []

    for secret_id, env_var, getter, required in SECRET_SPECS:
        if secret_id == "gemini-api-key":
            loaded = _gemini_satisfied()
            note = " (API key or Vertex AI)"
        else:
            loaded = bool(getter())
            note = ""

        flag = "OK" if loaded else "MISSING"
        req = "required" if required else "optional"
        print(f"  {secret_id:20} env={env_var:30} loaded={str(loaded):5} [{req}]{note}")

        if required and not loaded:
            missing_required.append(secret_id)

    print()
    if missing_required:
        print(f"FAIL: required secrets missing: {', '.join(missing_required)}")
        return 1

    print("PASS: all required secrets resolved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
