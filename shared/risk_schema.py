"""Backward-compatible re-exports — canonical definitions live in shared/schemas.py."""

from shared.schemas import RiskLevel, RiskSchema

__all__ = ["RiskSchema", "RiskLevel"]
