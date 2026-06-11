"""Configuration loader — Secret Manager in prod, .env for local dev."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Runtime settings for OrchestraOS services."""

    redis_url: str
    gcp_project_id: str
    pubsub_topic_raw_spans: str
    pubsub_topic_feature_vectors: str
    pubsub_topic_risk_assessments: str
    pubsub_subscription_raw_spans: str
    pubsub_subscription_feature_vectors: str
    pubsub_subscription_risk_assessments: str
    pubsub_topic_breaker_events: str
    pubsub_topic_remediation_plans: str
    pubsub_subscription_breaker_events: str
    pubsub_subscription_remediation_plans: str
    pubsub_subscription_partners_breaker: str
    pubsub_subscription_partners_remediation: str
    pubsub_emulator_host: str | None
    collector_host: str
    collector_port: int
    otel_service_name: str
    gemini_model: str
    breaker_risk_threshold: float
    breaker_cooldown_sec: int

    @property
    def is_local(self) -> bool:
        return bool(self.pubsub_emulator_host)


def _is_valid_secret(value: str) -> bool:
    """Reject empty values and setup_gcp placeholder strings."""
    return bool(value) and value.strip().lower() != "placeholder"


def _read_secret(secret_id: str, env_fallback: str) -> str:
    """
    Read a secret from Secret Manager when running on GCP.
    Falls back to environment variable for local development.

    Resolution order:
      1. Env var (e.g. GEMINI_API_KEY) if set and non-placeholder
      2. Secret Manager ``projects/{GOOGLE_CLOUD_PROJECT}/secrets/{secret_id}/versions/latest``
      3. Empty string
    """
    local_value = os.getenv(env_fallback, "")
    if _is_valid_secret(local_value):
        return local_value.strip()

    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    if not project_id or os.getenv("PUBSUB_EMULATOR_HOST"):
        return ""

    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        remote = response.payload.data.decode("utf-8").strip()
        return remote if _is_valid_secret(remote) else ""
    except Exception:
        return ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once per process."""
    return Settings(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        gcp_project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "orchestraos-local"),
        pubsub_topic_raw_spans=os.getenv("PUBSUB_TOPIC_RAW_SPANS", "raw-spans"),
        pubsub_topic_feature_vectors=os.getenv("PUBSUB_TOPIC_FEATURE_VECTORS", "feature-vectors"),
        pubsub_topic_risk_assessments=os.getenv("PUBSUB_TOPIC_RISK_ASSESSMENTS", "risk-assessments"),
        pubsub_subscription_raw_spans=os.getenv("PUBSUB_SUBSCRIPTION_RAW_SPANS", "raw-spans-sub"),
        pubsub_subscription_feature_vectors=os.getenv(
            "PUBSUB_SUBSCRIPTION_FEATURE_VECTORS", "feature-vectors-sub"
        ),
        pubsub_subscription_risk_assessments=os.getenv(
            "PUBSUB_SUBSCRIPTION_RISK_ASSESSMENTS", "risk-assessments-sub"
        ),
        pubsub_topic_breaker_events=os.getenv("PUBSUB_TOPIC_BREAKER_EVENTS", "breaker-events"),
        pubsub_topic_remediation_plans=os.getenv(
            "PUBSUB_TOPIC_REMEDIATION_PLANS", "remediation-plans"
        ),
        pubsub_subscription_breaker_events=os.getenv(
            "PUBSUB_SUBSCRIPTION_BREAKER_EVENTS", "breaker-events-sub"
        ),
        pubsub_subscription_remediation_plans=os.getenv(
            "PUBSUB_SUBSCRIPTION_REMEDIATION_PLANS", "remediation-plans-sub"
        ),
        pubsub_subscription_partners_breaker=os.getenv(
            "PUBSUB_SUBSCRIPTION_PARTNERS_BREAKER", "partners-breaker-sub"
        ),
        pubsub_subscription_partners_remediation=os.getenv(
            "PUBSUB_SUBSCRIPTION_PARTNERS_REMEDIATION", "partners-remediation-sub"
        ),
        pubsub_emulator_host=os.getenv("PUBSUB_EMULATOR_HOST"),
        collector_host=os.getenv("COLLECTOR_HOST", "0.0.0.0"),
        collector_port=int(os.getenv("COLLECTOR_PORT", "4318")),
        otel_service_name=os.getenv("OTEL_SERVICE_NAME", "orchestraos-collector"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        breaker_risk_threshold=float(os.getenv("BREAKER_RISK_THRESHOLD", "0.8")),
        breaker_cooldown_sec=int(os.getenv("BREAKER_COOLDOWN_SEC", "30")),
    )


def get_redis_url() -> str:
    """Redis URL from env or Secret Manager."""
    return _read_secret("redis-url", "REDIS_URL") or get_settings().redis_url


def get_gemini_api_key() -> str:
    """Gemini API key from env or Secret Manager."""
    return _read_secret("gemini-api-key", "GEMINI_API_KEY")


def get_mongodb_uri() -> str:
    return _read_secret("mongodb-uri", "MONGODB_URI")


def get_phoenix_endpoint() -> str:
    return _read_secret("phoenix-endpoint", "PHOENIX_COLLECTOR_ENDPOINT")


def get_arize_api_key() -> str:
    """Arize API key from env or Secret Manager (optional; OTLP uses phoenix-endpoint)."""
    return _read_secret("arize-api-key", "ARIZE_API_KEY")


def get_elastic_url() -> str:
    return _read_secret("elastic-url", "ELASTIC_URL")


def get_elastic_api_key() -> str:
    return _read_secret("elastic-api-key", "ELASTIC_API_KEY")


def get_dynatrace_url() -> str:
    return _read_secret("dynatrace-url", "DYNATRACE_URL")


def get_dynatrace_token() -> str:
    return _read_secret("dynatrace-token", "DYNATRACE_API_TOKEN")


def get_gitlab_url() -> str:
    return os.getenv("GITLAB_URL", "https://gitlab.com")


def get_gitlab_token() -> str:
    return _read_secret("gitlab-token", "GITLAB_TOKEN")


def get_gitlab_project_id() -> str:
    return _read_secret("gitlab-project-id", "GITLAB_PROJECT_ID")


def is_partner_enabled(partner: str) -> bool:
    """Check if a partner integration is enabled via env."""
    key = f"PARTNER_{partner.upper()}_ENABLED"
    return os.getenv(key, "false").lower() in ("1", "true", "yes")
