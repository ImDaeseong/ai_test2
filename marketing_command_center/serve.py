"""Serve the local post-writing app and its two paid OpenAI calls (draft, review)."""

from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import os
import re
import socket
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen


LOGGER = logging.getLogger("marketing_command_center")
CODE_VERSION = int(Path(__file__).stat().st_mtime)
PUBLIC_PATH = re.compile(r"/|/index\.html|/styles\.css|/src/[a-z]+\.js|/assets/[A-Za-z0-9._-]+")
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
OPENAI_MODEL = os.environ.get("MARKETING_OPENAI_MODEL", "gpt-6-luna")
MAX_FIELD_CHARS = {"service": 100, "description": 500, "channel": 50, "topic": 300, "audience": 300, "benefit": 300, "proof": 300, "cta": 300, "text": 3000}
MAX_REQUEST_BYTES = 20_000
DRAFT_TOKENS = 400
REVIEW_TOKENS = 700
DRAFT_INSTRUCTIONS = (
    "너는 광고 티를 줄이면서도 행동을 이끄는 한국어 커뮤니티 편집자다. 첫 줄은 지정된 독자의 상황 또는 얻을 가치로 시작한다. "
    "독자에게 맞는 이유, 구체적 가치, 믿을 근거와 한계, 마찰이 적은 행동 요청 순으로 쓴다. "
    "서비스 설명과 브리프에 없는 수치·성과·후기·자격·희소성을 만들지 않고, 과장·보장·공포 표현을 쓰지 않는다. "
    "채널 말투와 길이에 맞는 본문만 출력하고 행동 요청은 하나만 둔다."
)
REVIEW_INSTRUCTIONS = (
    "너는 까다로운 커뮤니티 회원이자 마케팅 편집자다. 주어진 글을 광고로 느껴지는지, 첫 줄이 읽을 이유를 주는지, "
    "서비스 설명으로 뒷받침되지 않는 주장이 있는지 엄격하게 평가한다. 아래 형식의 JSON 객체 하나만 출력한다: "
    '{"score": 1~10 정수, "hook": "첫 줄 평가 한두 문장", "persuasion": "설득력 평가 한두 문장", '
    '"risks": ["고쳐야 할 위험 최대 5개"], "rewrite": "더 나은 전체 글 한 편"}'
)


def _clean_fields(payload: object, required: tuple[str, ...], optional: tuple[str, ...]) -> dict[str, str] | None:
    """Return trimmed, length-checked fields, or None when input is missing or oversized."""
    if not isinstance(payload, dict):
        return None
    fields = {name: str(payload.get(name, "")).strip() for name in required + optional}
    if any(not fields[name] for name in required):
        return None
    if any(len(value) > MAX_FIELD_CHARS[name] for name, value in fields.items()):
        return None
    return fields


def _ask_openai(api_key: str, instructions: str, prompt: str, max_tokens: int, opener) -> dict[str, object]:
    """Make one private Responses API call and return text plus usage, or a tagged error."""
    request_payload = {
        "model": OPENAI_MODEL,
        "store": False,
        "max_output_tokens": max_tokens,
        "reasoning": {"effort": "none"},
        "instructions": instructions,
        "input": prompt,
    }
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))
        text = "".join(
            str(part.get("text", ""))
            for item in result.get("output", [])
            if isinstance(item, dict)
            for part in item.get("content", [])
            if isinstance(part, dict) and part.get("type") == "output_text"
        ).strip()
        usage = result.get("usage", {}) if isinstance(result.get("usage"), dict) else {}
        safe_usage = {name: int(usage.get(name, 0) or 0) for name in ("input_tokens", "output_tokens", "total_tokens")}
        model = str(result.get("model", OPENAI_MODEL))
        if not text:
            incomplete = result.get("incomplete_details") if isinstance(result.get("incomplete_details"), dict) else {}
            return {"status": "error", "kind": "empty_response", "model": model, "usage": safe_usage, "incomplete_reason": str(incomplete.get("reason", ""))}
        return {"status": "ok", "text": text, "model": model, "usage": safe_usage}
    except HTTPError as error:
        kind = "auth" if error.code in (401, 403) else "rate_limit" if error.code == 429 else "provider" if error.code >= 500 else "request"
        status = error.code
        error.close()
        LOGGER.warning("openai failure kind=%s status=%s", kind, status)
        return {"status": "error", "kind": kind, "http_status": status}
    except (URLError, TimeoutError) as error:
        kind = "timeout" if isinstance(error, TimeoutError) or isinstance(getattr(error, "reason", None), TimeoutError) else "network"
        LOGGER.exception("openai %s failure", kind, exc_info=error)
        return {"status": "error", "kind": kind}
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as error:
        LOGGER.exception("openai response failure", exc_info=error)
        return {"status": "error", "kind": "response"}


def _service_brief(fields: dict[str, str]) -> str:
    """Describe the service and channel for a prompt."""
    return f"서비스: {fields['service']}\n서비스 설명: {fields['description']}\n채널: {fields['channel'] or '미정'}"


def generate_marketing_draft(payload: dict[str, object], api_key: str | None, opener=urlopen) -> dict[str, object]:
    """Write one channel-specific post draft for a service."""
    if not api_key:
        return {"status": "not_configured"}
    fields = _clean_fields(payload, ("service", "description"), ("channel", "topic", "audience", "benefit", "proof", "cta"))
    if fields is None:
        return {"status": "error", "kind": "invalid_input"}
    prompt = (
        f"{_service_brief(fields)}\n글의 주제: {fields['topic'] or '서비스를 처음 알리는 글'}\n"
        f"주요 독자: {fields['audience'] or '서비스 설명에서 가장 적합한 독자를 추론하되 새 사실은 만들지 말 것'}\n"
        f"독자가 얻는 가치: {fields['benefit'] or '서비스 설명에서 확인되는 가치만 사용할 것'}\n"
        f"신뢰 근거·안전 경계: {fields['proof'] or '서비스 설명에 있는 한계만 밝힐 것'}\n"
        f"행동 요청: {fields['cta'] or '부담이 적은 행동 한 가지'}"
    )
    answer = _ask_openai(api_key, DRAFT_INSTRUCTIONS, prompt, DRAFT_TOKENS, opener)
    if answer["status"] != "ok":
        return answer
    return {"status": "generated", "text": answer["text"], "model": answer["model"], "usage": answer["usage"]}


def _parse_review(text: str) -> dict[str, object] | None:
    """Extract and validate the review JSON object from a model reply."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    score, risks = data.get("score"), data.get("risks")
    strings = [data.get(name) for name in ("hook", "persuasion", "rewrite")]
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return None
    if not all(isinstance(value, str) for value in strings) or not isinstance(risks, list) or not all(isinstance(item, str) for item in risks):
        return None
    return {
        "score": max(1, min(10, round(score))),
        "hook": strings[0][:1000],
        "persuasion": strings[1][:1000],
        "risks": [item[:300] for item in risks[:5]],
        "rewrite": strings[2][:3000],
    }


def review_marketing_post(payload: dict[str, object], api_key: str | None, opener=urlopen) -> dict[str, object]:
    """Have the model judge hook, persuasion and risks of one post and suggest a rewrite."""
    if not api_key:
        return {"status": "not_configured"}
    fields = _clean_fields(payload, ("service", "description", "text"), ("channel",))
    if fields is None:
        return {"status": "error", "kind": "invalid_input"}
    prompt = f"{_service_brief(fields)}\n\n평가할 글:\n{fields['text']}"
    answer = _ask_openai(api_key, REVIEW_INSTRUCTIONS, prompt, REVIEW_TOKENS, opener)
    if answer["status"] != "ok":
        return answer
    review = _parse_review(str(answer["text"]))
    if review is None:
        LOGGER.warning("openai review reply was not valid review JSON")
        return {"status": "error", "kind": "response"}
    return {"status": "reviewed", "review": review, "model": answer["model"], "usage": answer["usage"]}


class MarketingHandler(SimpleHTTPRequestHandler):
    """Serve static assets, a health probe and the two AI endpoints."""

    def send_json(self, status: int, result: dict[str, object]) -> None:
        """Write a UTF-8 JSON response that browsers must not cache."""
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def is_public_asset(self) -> bool:
        """Allow only the app's own page, styles, scripts and icon, never source, logs or docs."""
        return PUBLIC_PATH.fullmatch(unquote(urlparse(self.path).path)) is not None

    def do_GET(self) -> None:
        """Return the health probe or an allow-listed static asset."""
        if self.path == "/api/health":
            self.send_json(200, {"status": "ok", "service": "marketing-command-center", "code_version": CODE_VERSION})
            return
        if not self.is_public_asset():
            self.send_error(404)
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        """Apply the same allow-list to HEAD requests."""
        if not self.is_public_asset():
            self.send_error(404)
            return
        super().do_HEAD()

    def end_headers(self) -> None:
        """Apply cache and browser hardening headers to every local response."""
        self.send_header("Cache-Control", "no-store" if self.path.startswith("/api/") else "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()

    def do_POST(self) -> None:
        """Run one paid AI call for the draft or review endpoint."""
        handlers = {"/api/ai/draft": generate_marketing_draft, "/api/ai/review": review_marketing_post}
        handler = handlers.get(self.path)
        if handler is None:
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self.send_error(413)
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"status": "error", "kind": "invalid_json"})
            return
        result = handler(payload, os.environ.get("OPENAI_API_KEY"))
        ok = result.get("status") in ("generated", "reviewed")
        self.send_json(200 if ok else 503 if result.get("status") == "not_configured" else 400 if result.get("kind") == "invalid_input" else 502, result)

    def log_message(self, format: str, *args: object) -> None:
        """Log requests without paths or bodies."""
        print(f"{self.log_date_time_string()} {self.command} response")


class LocalThreadingHTTPServer(ThreadingHTTPServer):
    """Keep one local server process responsible for the configured port."""

    allow_reuse_address = False

    def server_bind(self) -> None:
        """Request exclusive port ownership on Windows before binding."""
        if os.name == "nt" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main() -> None:
    """Start the local-only server."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4175)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    mimetypes.add_type("text/javascript", ".js")
    handler = lambda *handler_args, **kwargs: MarketingHandler(*handler_args, directory=str(Path(__file__).parent), **kwargs)
    server = LocalThreadingHTTPServer((args.host, args.port), handler)
    print(f"Marketing Command Center: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
