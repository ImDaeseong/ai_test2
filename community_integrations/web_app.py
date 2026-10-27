"""Serve the local community composer and its dry-run-first publishing API."""

from __future__ import annotations

import argparse
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from capabilities import CAPABILITIES, PLATFORM_LABELS
from community_integrations.publisher import ADAPTERS, HttpTransport, PublishError, PublishRequest
from doctor import inspect_environment


LOGGER = logging.getLogger(__name__)
WEB_ROOT = Path(__file__).with_name("web")
MAX_REQUEST_BYTES = 64 * 1024
STATIC_CONTENT_TYPES = {
    ".css": "text/css",
    ".html": "text/html",
    ".js": "text/javascript",
}
def public_catalog(env: Mapping[str, str]) -> dict[str, Any]:
    """Return secret-free platform capabilities and local configuration readiness."""
    readiness = inspect_environment(env)
    return {
        "platforms": [
            {
                "id": key,
                "label": PLATFORM_LABELS[key],
                "capabilities": value,
                "configured": readiness[key]["local_config"] == "READY",
                "missing": readiness[key]["missing"],
            }
            for key, value in CAPABILITIES.items()
        ]
    }


def build_content(payload: Mapping[str, Any]) -> PublishRequest:
    """Validate browser input and convert it to the shared publishing model."""
    text = str(payload.get("text", "")).strip()
    title = str(payload.get("title", "")).strip() or None
    media_url = str(payload.get("media_url", "")).strip() or None
    media_type = str(payload.get("media_type", "TEXT")).strip().upper() or "TEXT"
    media_id = str(payload.get("media_id", "")).strip() or None
    alt_text = str(payload.get("alt_text", "")).strip() or None
    privacy = str(payload.get("privacy_level", "")).strip() or None
    if len(text) > 5000 or (title and len(title) > 300):
        raise PublishError("본문은 5,000자, 제목은 300자 이하여야 합니다")
    if media_url and not media_url.startswith("https://"):
        raise PublishError("미디어 URL은 https://로 시작해야 합니다")
    if payload.get("local_file_name"):
        raise PublishError("로컬 파일 바이너리 업로드는 아직 플랫폼별 업로더가 필요합니다. HTTPS URL 또는 기존 미디어 ID를 사용하세요")
    return PublishRequest(text, media_url, media_type, title, alt_text, privacy, media_id)


def preview_payload(payload: Mapping[str, Any], env: Mapping[str, str]) -> dict[str, Any]:
    """Build a redacted provider request preview without network activity."""
    platform = str(payload.get("platform", ""))
    if platform not in ADAPTERS:
        raise PublishError("지원하지 않는 플랫폼입니다")
    content = build_content(payload)
    requests = [request.safe_dict() for request in ADAPTERS[platform].preview(content, env)]
    return {"mode": "DRY_RUN", "platform": platform, "requests": requests}


def publish_payload(
    payload: Mapping[str, Any],
    env: Mapping[str, str],
    transport: HttpTransport | None = None,
) -> dict[str, Any]:
    """Publish only after two browser confirmations match the selected platform."""
    platform = str(payload.get("platform", ""))
    if payload.get("confirmed") is not True or str(payload.get("confirmation_text", "")).strip() != platform:
        raise PublishError("실제 게시에는 확인 체크와 플랫폼 ID 입력이 모두 필요합니다")
    if platform not in ADAPTERS:
        raise PublishError("지원하지 않는 플랫폼입니다")
    content = build_content(payload)
    result = ADAPTERS[platform].publish(content, env, transport or HttpTransport())
    return {"mode": "EXECUTED", "platform": platform, "result": result}


class CommunityWebHandler(BaseHTTPRequestHandler):
    """Expose static assets and bounded JSON endpoints on localhost."""

    server_version = "CommunityComposer/1.0"

    def do_GET(self) -> None:
        """Serve the composer shell or its public capability catalog."""
        path = urlparse(self.path).path
        if path == "/api/capabilities":
            self._send_json(200, public_catalog(os.environ))
            return
        asset = {"/": "index.html", "/app.js": "app.js", "/styles.css": "styles.css"}.get(path)
        if not asset:
            self._send_json(404, {"error": "not_found"})
            return
        self._send_file(WEB_ROOT / asset)

    def do_POST(self) -> None:
        """Handle dry-run previews and explicitly confirmed live publishing."""
        path = urlparse(self.path).path
        if path not in {"/api/preview", "/api/publish"}:
            self._send_json(404, {"error": "not_found"})
            return
        try:
            payload = self._read_json()
            result = preview_payload(payload, os.environ) if path == "/api/preview" else publish_payload(payload, os.environ)
            self._send_json(200, result)
        except PublishError as exc:
            self._send_json(400, {"error": "HOLD", "message": str(exc)})
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
            LOGGER.warning("invalid_request boundary=community_web", exc_info=exc)
            self._send_json(400, {"error": "INVALID_REQUEST", "message": "올바른 JSON 요청이 아닙니다"})
        except Exception as exc:  # provider and unexpected boundary
            LOGGER.exception("publish_failure boundary=community_web")
            self._send_json(502, {"error": "PUBLISH_FAILED", "message": "게시 요청이 실패했습니다. 서버 로그를 확인하세요"})

    def _read_json(self) -> dict[str, Any]:
        """Read one size-limited JSON object from the request body."""
        raw_length = self.headers.get("Content-Length", "0")
        length = int(raw_length)
        if length < 1 or length > MAX_REQUEST_BYTES:
            raise ValueError("request body size is invalid")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("request body must be an object")
        return payload

    def _send_json(self, status: int, payload: Mapping[str, Any]) -> None:
        """Return a UTF-8 JSON response with defensive browser headers."""
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path) -> None:
        """Return one allow-listed static file from the web asset directory."""
        if not path.is_file():
            self._send_json(404, {"error": "not_found"})
            return
        data = path.read_bytes()
        mime = STATIC_CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", f"{mime}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        """Route access messages through timestamped application logging."""
        LOGGER.info("web_access client=%s message=%s", self.client_address[0], format % args)


def build_parser() -> argparse.ArgumentParser:
    """Build the localhost web-server command parser."""
    parser = argparse.ArgumentParser(description="커뮤니티 게시 통합 웹 UI")
    parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "localhost"))
    parser.add_argument("--port", type=int, default=8766)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the T0 localhost-only community composer."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    server = ThreadingHTTPServer((args.host, args.port), CommunityWebHandler)
    print(f"Community Composer: http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
