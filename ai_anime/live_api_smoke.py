"""Run one explicit paid OpenAI image-generation smoke request."""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from typing import Any

from main import OPENAI_IMAGE_MODEL


LOGGER = logging.getLogger(__name__)
ENDPOINT = "https://api.openai.com/v1/images/generations"
SMOKE_PROMPT = (
    "A small blue screen-face robot standing in a quiet recording studio, "
    "clean 2D anime illustration, no text, no logo, no watermark."
)


def build_request(prompt: str = SMOKE_PROMPT) -> dict[str, object]:
    """Build the smallest representative image-generation request."""
    return {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": prompt,
        "n": 1,
        "quality": "low",
        "size": "1024x1024",
    }


def classify_provider_error(exc: BaseException) -> str:
    """Map provider failures to a stable operator-facing category."""
    if isinstance(exc, urllib.error.HTTPError):
        if exc.code in {401, 403}:
            return "auth"
        if exc.code == 429:
            return "rate_limit"
        if 500 <= exc.code < 600:
            return "provider_outage"
        return "request_rejected"
    if isinstance(exc, (TimeoutError, urllib.error.URLError)):
        return "network_or_timeout"
    return "unexpected"


def provider_error_metadata(exc: BaseException) -> dict[str, object]:
    """Extract non-secret provider diagnostics from an HTTP error response."""
    metadata: dict[str, object] = {
        "http_status": getattr(exc, "code", None),
        "provider_code": None,
        "provider_type": None,
        "request_id_present": False,
    }
    if not isinstance(exc, urllib.error.HTTPError):
        return metadata
    metadata["request_id_present"] = bool(exc.headers and exc.headers.get("x-request-id"))
    try:
        payload = json.loads(exc.read().decode("utf-8"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return metadata
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return metadata
    for source, target in (("code", "provider_code"), ("type", "provider_type")):
        value = error.get(source)
        if isinstance(value, str) and value:
            metadata[target] = value[:100]
    return metadata


def validate_response(payload: dict[str, Any]) -> int:
    """Validate one returned image and report its decoded byte count."""
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("provider response must contain exactly one image")
    encoded = data[0].get("b64_json")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError("provider response is missing data[0].b64_json")
    image = base64.b64decode(encoded, validate=True)
    if not image:
        raise ValueError("provider returned an empty image")
    return len(image)


def call_openai(api_key: str, prompt: str = SMOKE_PROMPT, timeout: float = 120.0) -> tuple[int, str | None]:
    """Call the live image endpoint once without persisting the generated image."""
    body = json.dumps(build_request(prompt)).encode("utf-8")
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            request_id = response.headers.get("x-request-id")
    except Exception as exc:
        kind = classify_provider_error(exc)
        metadata = provider_error_metadata(exc)
        LOGGER.exception(
            "provider_failure=%s call_site=call_openai http_status=%s "
            "provider_code=%s provider_type=%s request_id_present=%s",
            kind,
            metadata["http_status"],
            metadata["provider_code"],
            metadata["provider_type"],
            metadata["request_id_present"],
        )
        raise RuntimeError(
            "OpenAI live smoke failed "
            f"({kind}; status={metadata['http_status']}; "
            f"code={metadata['provider_code'] or 'unknown'}; "
            f"request_id_present={metadata['request_id_present']})"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("OpenAI live smoke returned a non-object response")
    return validate_response(payload), request_id


def main(argv: list[str] | None = None) -> int:
    """Require explicit cost confirmation and run one sanitized live request."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-paid-call", action="store_true")
    args = parser.parse_args(argv)
    if not args.confirm_paid_call:
        parser.error("--confirm-paid-call is required")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        parser.error("OPENAI_API_KEY is required")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        byte_count, request_id = call_openai(api_key)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS", "model": OPENAI_IMAGE_MODEL, "calls": 1,
        "image_bytes": byte_count, "request_id_present": bool(request_id), "image_saved": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
