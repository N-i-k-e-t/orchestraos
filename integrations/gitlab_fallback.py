"""GitLab issue fallback for human escalation."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import httpx

from shared.config import get_gitlab_project_id, get_gitlab_token, get_gitlab_url, is_partner_enabled

logger = logging.getLogger(__name__)


class GitLabFallback:
    """Creates GitLab issues when remediation escalates to a human."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        project_id: str | None = None,
    ) -> None:
        self._url = base_url or get_gitlab_url()
        self._token = token or get_gitlab_token()
        self._project_id = project_id or get_gitlab_project_id()
        self._enabled = is_partner_enabled("gitlab") and bool(
            self._url and self._token and self._project_id
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def create_escalation_issue(self, session_id: str, reason: str, details: dict[str, Any]) -> bool:
        if not self._enabled:
            return False

        title = f"[OrchestraOS] Agent escalation — {session_id}"
        description = (
            f"## OrchestraOS Human Escalation\n\n"
            f"**Session:** `{session_id}`\n\n"
            f"**Reason:** {reason}\n\n"
            f"**Details:**\n```json\n{details}\n```\n"
        )
        project = quote(str(self._project_id), safe="")
        url = f"{self._url.rstrip('/')}/api/v4/projects/{project}/issues"
        headers = {"PRIVATE-TOKEN": self._token}
        payload = {
            "title": title,
            "description": description,
            "labels": "orchestraos,agent-escalation",
        }
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            resp.raise_for_status()
            logger.info("GitLab issue created for session=%s", session_id)
            return True
        except Exception as exc:
            logger.warning("GitLab fallback failed: %s", exc)
            return False
