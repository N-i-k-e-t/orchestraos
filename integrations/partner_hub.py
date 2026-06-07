"""Partner export hub — fans out events to all enabled integrations."""

from __future__ import annotations

import logging
from typing import Any

from integrations.arize_exporter import ArizeExporter
from integrations.dynatrace_exporter import DynatraceExporter
from integrations.elastic_exporter import ElasticExporter
from integrations.gitlab_fallback import GitLabFallback
from integrations.mongodb_store import MongoIncidentStore
from shared.schemas import BreakerEventSchema, RemediationPlanSchema, SpanSchema

logger = logging.getLogger(__name__)


class PartnerHub:
    """Coordinates exports to Arize, MongoDB, Elastic, Dynatrace, and GitLab."""

    def __init__(self) -> None:
        self.arize = ArizeExporter()
        self.mongodb = MongoIncidentStore()
        self.elastic = ElasticExporter()
        self.dynatrace = DynatraceExporter()
        self.gitlab = GitLabFallback()

    def export_span(self, span: SpanSchema | dict[str, Any]) -> dict[str, bool]:
        data = span.model_dump(mode="json") if isinstance(span, SpanSchema) else span
        return {"arize": self.arize.export_span(data)}

    def handle_breaker_event(self, event: BreakerEventSchema | dict[str, Any]) -> dict[str, bool]:
        ev = event if isinstance(event, BreakerEventSchema) else BreakerEventSchema.model_validate(event)
        if ev.state != "open":
            return {}

        payload = ev.model_dump(mode="json")
        results = {
            "mongodb": bool(
                self.mongodb.save_incident(
                    ev.session_id,
                    incident_type="breaker_trip",
                    severity="critical",
                    reason=ev.reason,
                    details=payload,
                )
            ),
            "elastic": self.elastic.index_event("breaker_trip", payload),
            "dynatrace": self.dynatrace.send_event("breaker_trip", payload),
        }
        logger.info("Partner export breaker session=%s results=%s", ev.session_id, results)
        return results

    def handle_remediation_plan(self, plan: RemediationPlanSchema | dict[str, Any]) -> dict[str, bool]:
        pl = plan if isinstance(plan, RemediationPlanSchema) else RemediationPlanSchema.model_validate(plan)
        payload = pl.model_dump(mode="json")
        results = {
            "mongodb": bool(
                self.mongodb.save_incident(
                    pl.session_id,
                    incident_type="remediation",
                    severity="info" if pl.recovered else "warning",
                    reason=f"Remediation {pl.status}",
                    details=payload,
                )
            ),
            "elastic": self.elastic.index_event("remediation", payload),
            "dynatrace": self.dynatrace.send_event("remediation", payload),
            "gitlab": False,
        }
        if pl.status == "escalated":
            results["gitlab"] = self.gitlab.create_escalation_issue(
                pl.session_id,
                reason=f"Remediation escalated after {pl.attempt} attempts",
                details=payload,
            )
        logger.info("Partner export remediation session=%s results=%s", pl.session_id, results)
        return results
