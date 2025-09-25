"""
Minimal stdlib HTTP server to serve Kanban UI and cards.json feed.

Usage: python -m tools.kanban.server
Respects: ENABLE_KANBAN_UI, KANBAN_PORT
"""
from __future__ import annotations

import http.server
import json
import os
from pathlib import Path
from typing import Tuple

from .adapters import build_feed

ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = ROOT / "tools" / "kanban" / "static"


class KanbanHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (method name)
        try:
            if self.path.startswith("/kanban/cards.json"):
                self._serve_cards()
                return
            if self.path == "/kanban" or self.path == "/kanban/" or self.path == "/kanban/index.html":
                self._serve_index()
                return
            # Fallback to static files within STATIC_DIR
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def translate_path(self, path: str) -> str:  # Serve only STATIC_DIR for safety
        # Only serve static files from STATIC_DIR
        path = path.split("?", 1)[0].split("#", 1)[0]
        rel = path.lstrip("/")
        base = STATIC_DIR
        full = base / rel
        if full.is_dir():
            full = full / "index.html"
        return str(full)

    def _serve_index(self):
        index_path = STATIC_DIR / "index.html"
        if not index_path.exists():
            self.send_response(404)
            self.end_headers()
            return
        with index_path.open("rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _serve_cards(self):
        # Build feed from adapters
        window = os.getenv("KANBAN_WINDOW", "4h")
        feed = build_feed(window=window)
        data = json.dumps(feed).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def run_server(server_class=http.server.ThreadingHTTPServer, handler_class=KanbanHandler) -> Tuple[str, int]:
    host = os.getenv("KANBAN_HOST", "127.0.0.1")
    port = int(os.getenv("KANBAN_PORT", "8765"))
    httpd = server_class((host, port), handler_class)
    print(f"Kanban UI at http://{host}:{port}/kanban")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    return host, port


if __name__ == "__main__":
    if os.getenv("ENABLE_KANBAN_UI", "false").lower() != "true":
        print("ENABLE_KANBAN_UI=false; nothing to serve.")
    else:
        run_server()
