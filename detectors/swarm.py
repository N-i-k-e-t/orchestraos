"""Parallel detector swarm — runs all 6 agents and fuses output."""

from __future__ import annotations

from detectors.context_agent import ContextAgent
from detectors.error_agent import ErrorAgent
from detectors.feature_fusion import FeatureFusion
from detectors.latency_agent import LatencyAgent
from detectors.loop_agent import LoopAgent
from detectors.progress_agent import ProgressAgent
from detectors.token_agent import TokenAgent
from shared.schemas import FeatureVectorSchema, SpanSchema


class DetectorSwarm:
    """
    Orchestrates the six detector agents in parallel (logical grouping)
    and produces a fused FeatureVector for downstream risk assessment.
    """

    def __init__(self) -> None:
        self.loop = LoopAgent()
        self.progress = ProgressAgent()
        self.token = TokenAgent()
        self.latency = LatencyAgent()
        self.context = ContextAgent()
        self.error = ErrorAgent()
        self.fusion = FeatureFusion()

    def process(self, span: SpanSchema) -> FeatureVectorSchema:
        loop_result = self.loop.observe(span.session_id, span.tool_name, span.params)
        progress_result = self.progress.observe(
            span.session_id, span.token_count, span.state_hash
        )
        token_result = self.token.observe(span.session_id, span.token_count)
        latency_result = self.latency.observe(span.session_id, span.latency_ms)
        context_result = self.context.observe(span.session_id, span.state_hash)
        error_result = self.error.observe(span.session_id, span.status)

        features = self.fusion.fuse(
            loop_score=loop_result.loop_score,
            progress_score=progress_result.progress_score,
            latency_score=latency_result.latency_score,
            token_score=token_result.token_score,
            context_score=context_result.context_score,
            error_score=error_result.error_score,
        )

        return FeatureVectorSchema(
            session_id=span.session_id,
            span_id=span.span_id,
            trace_id=span.trace_id,
            loop_detected=loop_result.loop_detected,
            repeat_count=loop_result.repeat_count,
            fingerprint=loop_result.fingerprint,
            features=features,
            timestamp=span.timestamp,
        )

    def reset(self, session_id: str | None = None) -> None:
        if session_id:
            self.progress.reset(session_id)
            self.token.reset(session_id)
            self.latency.reset(session_id)
            self.context.reset(session_id)
            self.error.reset(session_id)
        else:
            self.loop.reset()
            self.progress.reset()
            self.token.reset()
            self.latency.reset()
            self.context.reset()
            self.error.reset()
