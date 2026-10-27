"""Serve the local Threads composer and keep provider credentials server-side."""

from __future__ import annotations

import json
import logging
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError

from examples.threads_python.threads_client import ThreadsClient, build_profile_request
from web_service import prepare_web_plan, publish_web_request


ROOT = Path(__file__).resolve().parent
MAX_REQUEST_BYTES = 32_768
LOGGER = logging.getLogger("threads_studio")
ACCOUNT: dict[str, str] = {}


def account_status(environ: dict[str, str]) -> dict[str, object]:
    """Return public connection metadata without exposing credential values."""
    return {
        "connected": bool(ACCOUNT.get("id")),
        "account": dict(ACCOUNT) if ACCOUNT.get("id") else None,
        "configuration": {
            "app_id": bool(environ.get("THREADS_APP_ID")),
            "app_secret": bool(environ.get("THREADS_APP_SECRET")),
            "redirect_uri": bool(environ.get("THREADS_REDIRECT_URI")),
            "access_token": bool(environ.get("THREADS_ACCESS_TOKEN")),
        },
    }


class ThreadsStudioHandler(SimpleHTTPRequestHandler):
    """Serve static studio assets and the local publishing API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        """Return connection readiness or a static project file."""
        if self.path == "/api/status":
            self.send_json(200, account_status(dict(os.environ)))
            return
        if self.path == "/":
            self.path = "/publisher.html"
        super().do_GET()

    def do_POST(self) -> None:
        """Preview or publish a validated Threads composer request."""
        if self.path not in {"/api/preview", "/api/publish", "/api/account/verify", "/api/account/disconnect"}:
            self.send_error(404)
            return
        try:
            payload = self.read_json()
            if self.path == "/api/account/disconnect":
                ACCOUNT.clear()
                self.send_json(200, account_status(dict(os.environ)))
                return
            if self.path == "/api/account/verify":
                token = os.getenv("THREADS_ACCESS_TOKEN", "")
                if not token:
                    self.send_json(503, {"error": "THREADS_ACCESS_TOKEN 환경변수가 필요합니다"})
                    return
                profile = ThreadsClient(token).execute(build_profile_request())
                account_id = str(profile.get("id", ""))
                if not account_id:
                    raise RuntimeError("Threads가 계정 ID를 반환하지 않았습니다")
                ACCOUNT.clear()
                ACCOUNT.update(id=account_id, username=str(profile.get("username", "")), name=str(profile.get("name", "")))
                self.send_json(200, account_status(dict(os.environ)))
                return
            user_id = ACCOUNT.get("id", "{threads-user-id}")
            if self.path == "/api/preview":
                requests = prepare_web_plan(user_id, payload)
                self.send_json(200, {"carousel": len(requests) > 1, "requests": [request.safe_dict() for request in requests]})
                return
            token = os.getenv("THREADS_ACCESS_TOKEN", "")
            if user_id == "{threads-user-id}" or not token:
                self.send_json(503, {"error": "웹페이지에서 Threads 계정 연결을 먼저 확인하세요"})
                return
            result = publish_web_request(ThreadsClient(token), user_id, payload)
            self.send_json(200, result)
        except ValueError as exc:
            self.send_json(400, {"error": str(exc)})
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            LOGGER.exception("Threads publish call failed at %s", self.path)
            self.send_json(502, {"error": "Threads 게시에 실패했습니다. 서버 로그에서 원인을 확인하세요."})

    def read_json(self) -> dict[str, object]:
        """Read one bounded JSON object from the request body."""
        if self.headers.get_content_type() != "application/json":
            raise ValueError("Content-Type은 application/json이어야 합니다")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_REQUEST_BYTES:
            raise ValueError("요청 크기가 허용 범위를 벗어났습니다")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("JSON 객체가 필요합니다")
        return payload

    def send_json(self, status: int, payload: object) -> None:
        """Send a UTF-8 JSON response with local-only browser protections."""
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; img-src 'self' https:; media-src 'self' https:; style-src 'self'; script-src 'self'")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    """Run the composer on the loopback interface only."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    address = ("127.0.0.1", 8765)
    LOGGER.info("Threads Studio: http://%s:%s", *address)
    ThreadingHTTPServer(address, ThreadsStudioHandler).serve_forever()


if __name__ == "__main__":
    main()
