"""Gemini Flash client for risk classification."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from shared.config import get_gemini_api_key, get_settings
from shared.schemas import RiskLevel

logger = logging.getLogger(__name__)

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
    """Wraps Gemini Flash for structured risk classification."""

    def __init__(self, model_name: str | None = None) -> None:
        self._settings = get_settings()
        self._model_name = model_name or self._settings.gemini_model
        self._model = None
        self._available = False
        self._init_model()

    def _init_model(self) -> None:
        api_key = get_gemini_api_key()
        if not api_key:
            logger.info("GEMINI_API_KEY not set — RiskAgent uses deterministic fallback")
            return
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(self._model_name)
            self._available = True
        except Exception as exc:
            logger.warning("Gemini init failed: %s — using fallback", exc)

    @property
    def available(self) -> bool:
        return self._available

    def classify(
        self,
        features: dict[str, float],
        loop_detected: bool = False,
        repeat_count: int = 0,
    ) -> dict[str, Any] | None:
        """Call Gemini Flash. Returns None if unavailable or on error."""
        if not self._available or self._model is None:
            return None

        prompt = _CLASSIFY_PROMPT.format(
            features=json.dumps(features, indent=2),
            loop_detected=loop_detected,
            repeat_count=repeat_count,
        )
        try:
            response = self._model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"},
            )
            return self._parse_response(response.text)
        except Exception as exc:
            logger.warning("Gemini classify failed: %s", exc)
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
