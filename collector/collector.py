"""Backward-compatible entry — use collector.main for Phase 1."""

from collector.main import app, main

__all__ = ["app", "main"]

if __name__ == "__main__":
    main()
