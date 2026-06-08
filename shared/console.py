"""Console helpers for cross-platform CLI output."""

from __future__ import annotations

import sys


def configure_stdout_utf8() -> None:
    """Use UTF-8 on stdout/stderr when supported (avoids cp1252 errors on Windows)."""
    import os

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass
