"""Arize Phoenix MCP integration — trace/session tools for the Arize hackathon track."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from shared.config import get_phoenix_endpoint, is_partner_enabled

logger = logging.getLogger(__name__)


class PhoenixMcpClient:
    """
    JSON-RPC client for Arize Phoenix MCP tools.

    Complements OTLP span export (integrations/arize_exporter.py) by registering
    sessions and querying trace visibility for judges.

    Set PHOENIX_MCP_URL (e.g. http://localhost:6006/mcp) when Phoenix MCP server is running.
    Falls back to Phoenix HTTP API on the collector endpoint when MCP URL is unset.
    """

    def __init__(
        self,
        mcp_url: str | None = None,
        phoenix_base: str | None = None,
    ) -> None:
        self._mcp_url = (mcp_url or os.getenv("PHOENIX_MCP_URL", "")).rstrip("/")
        self._phoenix_base = (phoenix_base or get_phoenix_endpoint()).rstrip("/")
        self._enabled = is_partner_enabled("arize") and bool(self._mcp_url or self._phoenix_base)
        self._rpc_id = 0

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _next_id(self) -> int:
        self._rpc_id += 1
        return self._rpc_id

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
        """Invoke an MCP tool by name. Returns parsed result or None on failure."""
        if not self._enabled:
            return None
        if self._mcp_url:
            return self._json_rpc("tools/call", {"name": name, "arguments": arguments})
        return self._phoenix_rest_fallback(name, arguments)

    def _json_rpc(self, method: str, params: dict[str, Any]) -> dict[str, Any] | None:
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params,
        }
        try:
            resp = httpx.post(
                self._mcp_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=8.0,
            )
            resp.raise_for_status()
            body = resp.json()
            if "error" in body:
                logger.warning("Phoenix MCP error: %s", body["error"])
                return None
            return body.get("result")
        except Exception as exc:
            logger.warning("Phoenix MCP call failed: %s", exc)
            return None

    def _phoenix_rest_fallback(self, name: str, arguments: dict[str, Any]) -> dict[str, Any] | None:
        """When MCP server is not running, ping Phoenix health and log session metadata."""
        if name != "orchestraos_register_session":
            return None
        session_id = arguments.get("session_id", "")
        try:
            resp = httpx.get(f"{self._phoenix_base}/health", timeout=5.0)
            ok = resp.status_code == 200
            if ok:
                logger.info(
                    "Phoenix MCP fallback: session=%s registered (OTLP traces via collector)",
                    session_id,
                )
            return {"registered": ok, "session_id": session_id, "transport": "otlp_fallback"}
        except Exception as exc:
            logger.warning("Phoenix REST fallback failed: %s", exc)
            return None

    def register_session(self, session_id: str, *, tool_name: str, trace_id: str) -> bool:
        """
        Notify Phoenix MCP that an OrchestraOS-monitored session produced a span.
        Judges verify traces in Phoenix UI + MCP tool responses.
        """
        result = self.call_tool(
            "orchestraos_register_session",
            {
                "session_id": session_id,
                "trace_id": trace_id,
                "tool_name": tool_name,
                "source": "orchestraos-collector",
            },
        )
        return bool(result)

    def list_recent_sessions(self, limit: int = 10) -> list[dict[str, Any]]:
        """Query Phoenix MCP for recent agent sessions (demo / judge verification)."""
        result = self.call_tool("list_sessions", {"limit": limit})
        if not result:
            return []
        sessions = result.get("sessions") if isinstance(result, dict) else result
        return sessions if isinstance(sessions, list) else []
