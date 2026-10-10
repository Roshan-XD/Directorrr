"""Launcher-only local static UI and protected proxy; no Node needed after setup."""
import http.client
import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "http://127.0.0.1:5173"
LIMIT = 64 * 1024 * 1024


def trusted_session(headers):
    if headers.get("Host") != "127.0.0.1:5173":
        return False
    if headers.get("Origin"):
        return headers["Origin"] == ORIGIN
    return headers.get("Sec-Fetch-Site") == "same-origin" and urlsplit(headers.get("Referer", "")).netloc == "127.0.0.1:5173" and headers.get("Referer", "").startswith(ORIGIN + "/")


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass  # URLs, bodies and credentials never enter console logs.

    def error(self, code, message):
        data = json.dumps({"detail": message}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def dispatch(self):
        origin = self.headers.get("Origin")
        if self.headers.get("Host") != "127.0.0.1:5173" or origin and origin != ORIGIN:
            return self.error(403, "Untrusted local frontend origin")
        if not self.path.startswith("/api/"):
            if self.command not in {"GET", "HEAD"}:
                return self.error(405, "Method not allowed")
            path = unquote(urlsplit(self.path).path)
            target = (ROOT / "frontend/dist" / path.lstrip("/")).resolve()
            if not target.is_relative_to((ROOT / "frontend/dist").resolve()):
                return self.error(403, "Invalid asset path")
            for parent in (target, *target.parents):
                if parent.exists() and (parent.is_symlink() or getattr(parent.stat(), "st_file_attributes", 0) & 0x400):
                    return self.error(403, "Linked asset path")
            if self.command == "HEAD":
                return super().do_HEAD()
            return super().do_GET()
        key = self.server.session_key
        if self.path == "/api/launcher-session":
            if not trusted_session(self.headers):
                return self.error(403, "Untrusted session origin")
            data = b'{"automatic":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        marked = self.headers.get("X-Director-Session") == "launcher"
        if marked and not trusted_session(self.headers):
            return self.error(403, "Untrusted session origin")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.error(400, "Invalid request length")
        if self.headers.get("Transfer-Encoding") or not 0 <= length <= LIMIT:
            return self.error(413, "Request body exceeds local proxy limit")
        blocked = {"connection", "proxy-authorization", "transfer-encoding", "upgrade", "host", "x-director-session", "cookie"}
        headers = {k: v for k, v in self.headers.items() if k.lower() not in blocked}
        if origin:
            headers["Origin"] = "http://127.0.0.1:8000"
        if marked and not self.headers.get("X-Director-Key"):
            headers["X-Director-Key"] = key
        connection = http.client.HTTPConnection("127.0.0.1", 8000, timeout=60)
        started = False
        try:
            connection.request(self.command, self.path, body=self.rfile.read(length), headers=headers)
            response = connection.getresponse()
            self.send_response(response.status)
            started = True
            for name, value in response.getheaders():
                if name.lower() not in {"connection", "transfer-encoding", "set-cookie"}:
                    self.send_header(name, value)
            self.send_header("Connection", "close")
            self.end_headers()
            while chunk := response.read(64 * 1024):
                self.wfile.write(chunk)
        except (OSError, http.client.HTTPException):
            if not started:
                self.error(502, "Director backend is unavailable")
            else:
                self.close_connection = True
        finally:
            connection.close()

    do_GET = dispatch
    do_HEAD = dispatch
    do_POST = dispatch
    do_DELETE = dispatch
    do_PUT = dispatch
    do_PATCH = dispatch
    do_OPTIONS = dispatch


def main():
    key = os.environ.pop("DIRECTOR_LAUNCHER_TOKEN", "")
    if len(key) < 64 or os.environ.get("DIRECTOR_PACKAGED_SESSION") != "1":
        raise SystemExit("An explicit Director launcher session is required")
    if not (ROOT / "frontend/dist/index.html").is_file():
        raise SystemExit("Packaged frontend assets are missing")
    from functools import partial
    server = ThreadingHTTPServer(("127.0.0.1", 5173), partial(Handler, directory=str(ROOT / "frontend/dist")))
    server.session_key = key
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.session_key = ""
        server.server_close()


if __name__ == "__main__":
    main()
