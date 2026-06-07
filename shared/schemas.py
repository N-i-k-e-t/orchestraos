"""Canonical Pydantic schemas — single source of truth for OrchestraOS."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SpanSchema(BaseModel):
    """Validated representation of an agent tool-call span."""

    trace_id: str = Field(..., description="Unique trace identifier")
    span_id: str = Field(..., description="Unique span identifier within the trace")
    session_id: str = Field(..., description="Agent session identifier")
    tool_name: str = Field(..., description="Name of the tool invoked")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool call parameters")
    token_count: int = Field(default=0, ge=0, description="Tokens consumed by this span")
    latency_ms: float = Field(default=0.0, ge=0, description="Span latency in milliseconds")
    state_hash: str | None = Field(default=None, description="Hash of agent state after call")
    status: str = Field(default="ok", description="Span status: ok | error")
    error_message: str | None = Field(default=None, description="Error detail when status=error")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class IncidentType(str, Enum):
    LOOP = "loop"
    STALL = "stall"
    BREAKER_TRIP = "breaker_trip"
    ESCALATION = "escalation"


class IncidentSchema(BaseModel):
    """Record of a detected incident requiring attention or remediation."""

    incident_id: str
    session_id: str
    incident_type: IncidentType
    severity: str
    fingerprint: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RiskLevel(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


class RiskSchema(BaseModel):
    """Output of the risk assessment pipeline."""

    session_id: str
    span_id: str | None = None
    status: RiskLevel = Field(..., description="Alias: healthy | warning | critical")
    risk_level: RiskLevel
    risk_score: float = Field(..., ge=0.0, le=1.0)
    feature_vector: dict[str, float] = Field(default_factory=dict)
    reason: str = ""

    @classmethod
    def from_assessment(
        cls,
        session_id: str,
        status: RiskLevel,
        risk_score: float,
        reason: str,
        feature_vector: dict[str, float],
        span_id: str | None = None,
    ) -> "RiskSchema":
        return cls(
            session_id=session_id,
            span_id=span_id,
            status=status,
            risk_level=status,
            risk_score=risk_score,
            feature_vector=feature_vector,
            reason=reason,
        )


class MetricsSchema(BaseModel):
    """Aggregated metrics for a single agent session."""

    session_id: str
    total_spans: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    avg_latency_ms: float = Field(default=0.0, ge=0)
    loop_count: int = Field(default=0, ge=0)
    progress_score: float = Field(default=1.0, ge=0.0, le=1.0)
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TraceIngestResponse(BaseModel):
    """Collector acknowledgement for ingested spans."""

    accepted: int
    rejected: int
    published: int
    checkpointed: int
    spans: list[dict[str, str]]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeatureVectorSchema(BaseModel):
    """Fused detector output published to the event fabric."""

    session_id: str
    span_id: str
    trace_id: str
    loop_detected: bool = False
    repeat_count: int = 0
    fingerprint: str | None = None
    features: dict[str, float] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BreakerEventSchema(BaseModel):
    """Circuit breaker state change published after risk assessment."""

    session_id: str
    state: str = Field(..., description="closed | half_open | open")
    previous_state: str = "closed"
    risk_score: float = Field(..., ge=0.0, le=1.0)
    allowed: bool = Field(..., description="Whether the session may proceed")
    reason: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RemediationPlanSchema(BaseModel):
    """Published after orchestrator runs the recovery chain."""

    plan_id: str
    session_id: str
    status: str = Field(..., description="recovered | in_progress | escalated")
    attempt: int = Field(..., ge=1)
    recovered: bool = False
    steps: list[dict[str, Any]] = Field(default_factory=list)
    total_steps: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
