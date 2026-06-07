"""Cloud Run helpers — PORT binding and background health server for workers."""

from __future__ import annotations

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


def get_listen_port(default: int = 8080) -> int:
    """Resolve listen port: Cloud Run PORT env, then service-specific override."""
    if port := os.getenv("PORT"):
        return int(port)
    if collector_port := os.getenv("COLLECTOR_PORT"):
        return int(collector_port)
    return default


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *_args) -> None:
        return


def start_health_server(port: int | None = None) -> None:
    """Start a daemon HTTP server so Cloud Run sees a listening container."""
    listen = port if port is not None else get_listen_port()
    server = HTTPServer(("0.0.0.0", listen), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
