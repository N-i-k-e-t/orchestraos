"""Gemini client — Vertex AI (primary on GCP) + API key + deterministic fallback."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Literal

from shared.config import get_gemini_api_key, get_settings
from shared.schemas import RiskLevel

logger = logging.getLogger(__name__)

GeminiBackend = Literal["vertex", "api_key", "none"]

# Vertex model fallbacks when the configured name is unavailable in a region/project.
_VERTEX_MODEL_FALLBACKS = (
    "gemini-2.0-flash",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash",
    "gemini-2.5-flash",
)

_CLASSIFY_PROMPT = """You are OrchestraOS RiskAgent. Classify agent session risk from detector features.

Features (0.0=good, 1.0=bad unless noted):
- loop_score: repeated identical tool calls
- progress_score: forward progress (LOW value = bad)
- latency_score: slow responses
- token_score: token budget usage
- context_score: stagnant agent state
- error_score: tool error rate

Also consider:
- loop_detected: {loop_detected}
- repeat_count: {repeat_count}

Respond ONLY with JSON:
{{"status":"healthy|warning|critical","risk_score":0.0-1.0,"reason":"one sentence"}}

Feature vector: {features}
"""


class GeminiClient:
    """Gemini via Vertex AI (Agent Builder path) or Google AI API key."""

    def __init__(self, model_name: str | None = None) -> None:
        self._settings = get_settings()
        self._model_name = model_name or self._settings.gemini_model
        self._model: Any = None
        self._available = False
        self._backend: GeminiBackend = "none"
        self._init_model()

    @property
    def available(self) -> bool:
        return self._available

    @property
    def backend(self) -> GeminiBackend:
        return self._backend

    def _init_model(self) -> None:
        if self._try_vertex():
            return
        if self._try_api_key():
            return
        logger.info("No Gemini backend — RiskAgent uses deterministic fallback only")

    def _vertex_model_candidates(self) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for name in (self._model_name, *_VERTEX_MODEL_FALLBACKS):
            if name not in seen:
                seen.add(name)
                ordered.append(name)
        return ordered

    def _try_vertex(self) -> bool:
        """Vertex AI Gemini — required path for GCP / Agent Builder submissions."""
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        if not project or os.getenv("PUBSUB_EMULATOR_HOST"):
            return False
        if os.getenv("USE_VERTEX_GEMINI", "true").lower() in ("0", "false", "no"):
            return False
        try:
            import vertexai
            from vertexai.generative_models import GenerationConfig, GenerativeModel

            location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
            vertexai.init(project=project, location=location)
            smoke = GenerationConfig(response_mime_type="application/json", max_output_tokens=16)
            for model_name in self._vertex_model_candidates():
                try:
                    model = GenerativeModel(model_name)
                    model.generate_content('{"status":"healthy"}', generation_config=smoke)
                    self._model = model
                    self._gen_config = GenerationConfig(response_mime_type="application/json")
                    self._model_name = model_name
                    self._backend = "vertex"
                    self._available = True
                    logger.info(
                        "Gemini via Vertex AI project=%s location=%s model=%s",
                        project,
                        location,
                        model_name,
                    )
                    return True
                except Exception as exc:
                    logger.warning("Vertex model %s unavailable: %s", model_name, exc)
            return False
        except Exception as exc:
            logger.warning("Vertex AI Gemini init failed: %s", exc)
            return False

    def _try_api_key(self) -> bool:
        api_key = get_gemini_api_key()
        if not api_key:
            return False
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(self._model_name)
            self._gen_config = {"response_mime_type": "application/json"}
            self._backend = "api_key"
            self._available = True
            logger.info("Gemini via API key model=%s", self._model_name)
            return True
        except Exception as exc:
            logger.warning("Gemini API key init failed: %s — using fallback", exc)
            return False

    def classify(
        self,
        features: dict[str, float],
        loop_detected: bool = False,
        repeat_count: int = 0,
    ) -> dict[str, Any] | None:
        """Call Gemini. Returns None if unavailable or on error."""
        if not self._available or self._model is None:
            return None

        prompt = _CLASSIFY_PROMPT.format(
            features=json.dumps(features, indent=2),
            loop_detected=loop_detected,
            repeat_count=repeat_count,
        )
        result = self._generate(prompt)
        if result is not None:
            return result

        # Vertex model may init but fail at runtime — try API key once if configured.
        if self._backend == "vertex" and get_gemini_api_key():
            prior = self._backend
            if self._try_api_key():
                result = self._generate(prompt)
                if result is not None:
                    return result
                self._backend = prior
        return None

    def _generate(self, prompt: str) -> dict[str, Any] | None:
        try:
            response = self._model.generate_content(prompt, generation_config=self._gen_config)
            text = response.text if hasattr(response, "text") else str(response)
            return self._parse_response(text)
        except Exception as exc:
            logger.warning("Gemini classify failed (%s): %s", self._backend, exc)
            return None

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group()
        data = json.loads(cleaned)
        status = RiskLevel(data["status"])
        score = float(data["risk_score"])
        return {
            "status": status,
            "risk_score": max(0.0, min(1.0, score)),
            "reason": str(data.get("reason", "")),
        }
