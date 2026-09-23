"""Serves the built frontend bundle on a loopback port for the browser driver."""

from __future__ import annotations

import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.core.exceptions import RenderError

# UIB_FRONTEND_DIST points the renderer at another bundle, so parallel builds never collide.
FRONTEND_DIST = Path(
    os.environ.get("UIB_FRONTEND_DIST") or Path(__file__).resolve().parents[2] / "frontend" / "dist"
).resolve()


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args: object) -> None:  # silence stderr access logs
        return

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


class StaticServer:
    """Context manager serving a directory; picks a free port."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or FRONTEND_DIST
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        if self._httpd is None:
            raise RenderError("server not started", stage="server")
        return f"http://127.0.0.1:{self._httpd.server_address[1]}/"

    def start(self) -> StaticServer:
        if not (self.directory / "index.html").exists():
            raise RenderError(
                f"frontend bundle missing at {self.directory}; "
                "run `npm --prefix frontend install && npm --prefix frontend run build`",
                stage="server",
                details={"directory": str(self.directory)},
            )
        handler = partial(_QuietHandler, directory=str(self.directory))
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    def __enter__(self) -> StaticServer:
        return self.start()

    def __exit__(self, *exc: object) -> None:
        self.stop()
