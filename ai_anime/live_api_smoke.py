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
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from main import (
    OPENAI_IMAGE_MODEL,
    Song,
    _build_scene_image_blocks,
    build_visual_identity,
    load_profiles,
)


LOGGER = logging.getLogger(__name__)
ENDPOINT = "https://api.openai.com/v1/images/generations"
EXPECTED_SIZE = (1024, 1024)


@dataclass(frozen=True)
class ImageValidation:
    """Describe the validated in-memory image without retaining its bytes."""

    byte_count: int
    image_format: str
    width: int
    height: int


def build_generated_prompt() -> str:
    """Build the first GPT scene prompt through the production generator."""
    song = Song(
        title="Live API Contract Smoke",
        genre="anime pop",
        bpm="120 BPM",
        mood="hopeful",
    )
    identity = build_visual_identity(song, load_profiles())
    blocks = _build_scene_image_blocks(song, identity)
    marker = f"### GPT Image ({OPENAI_IMAGE_MODEL} / OpenAI)\n"
    if marker not in blocks:
        raise ValueError("generated scene is missing the GPT Image section")
    prompt = blocks.split(marker, 1)[1].split("\n\n**Model:**", 1)[0].strip()
    if not prompt:
        raise ValueError("generated GPT Image prompt is empty")
    return prompt


def build_request(prompt: str | None = None) -> dict[str, object]:
    """Build the smallest representative image-generation request."""
    return {
        "model": OPENAI_IMAGE_MODEL,
        "prompt": prompt if prompt is not None else build_generated_prompt(),
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


def inspect_image(image: bytes) -> tuple[str, int, int]:
    """Read the format and dimensions from a PNG, JPEG, or WebP header."""
    if (
        image.startswith(b"\x89PNG\r\n\x1a\n")
        and len(image) >= 24
        and image[8:12] == b"\x00\x00\x00\r"
        and image[12:16] == b"IHDR"
    ):
        return "png", int.from_bytes(image[16:20], "big"), int.from_bytes(image[20:24], "big")
    if image.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 9 <= len(image):
            if image[offset] != 0xFF:
                offset += 1
                continue
            marker = image[offset + 1]
            if marker in {0xD8, 0xD9}:
                offset += 2
                continue
            segment_length = int.from_bytes(image[offset + 2:offset + 4], "big")
            if segment_length < 2 or offset + 2 + segment_length > len(image):
                break
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                height = int.from_bytes(image[offset + 5:offset + 7], "big")
                width = int.from_bytes(image[offset + 7:offset + 9], "big")
                return "jpeg", width, height
            offset += 2 + segment_length
    if image.startswith(b"RIFF") and image[8:12] == b"WEBP" and len(image) >= 30:
        chunk = image[12:16]
        if chunk == b"VP8X":
            width = int.from_bytes(image[24:27], "little") + 1
            height = int.from_bytes(image[27:30], "little") + 1
            return "webp", width, height
        if chunk == b"VP8 " and image[23:26] == b"\x9d\x01\x2a":
            width = int.from_bytes(image[26:28], "little") & 0x3FFF
            height = int.from_bytes(image[28:30], "little") & 0x3FFF
            return "webp", width, height
        if chunk == b"VP8L" and image[20] == 0x2F:
            bits = int.from_bytes(image[21:25], "little")
            return "webp", (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    raise ValueError("provider returned an unsupported or malformed image")


def validate_response(payload: dict[str, Any]) -> ImageValidation:
    """Validate one returned image's encoding, format, and exact dimensions."""
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise ValueError("provider response must contain exactly one image")
    encoded = data[0].get("b64_json")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError("provider response is missing data[0].b64_json")
    image = base64.b64decode(encoded, validate=True)
    if not image:
        raise ValueError("provider returned an empty image")
    image_format, width, height = inspect_image(image)
    if (width, height) != EXPECTED_SIZE:
        raise ValueError(
            f"provider returned {width}x{height}; expected {EXPECTED_SIZE[0]}x{EXPECTED_SIZE[1]}"
        )
    return ImageValidation(len(image), image_format, width, height)


def load_api_key(key_file: Path | None = None) -> str:
    """Load a key from the environment or one explicit small regular file."""
    if key_file is None:
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if not key:
            raise ValueError("OPENAI_API_KEY is required")
        return key
    if key_file.is_symlink():
        raise ValueError("--key-file must be one regular non-symlink file")
    path = key_file.resolve(strict=True)
    if not path.is_file():
        raise ValueError("--key-file must be one regular non-symlink file")
    if path.stat().st_size > 16_384:
        raise ValueError("--key-file exceeds 16 KiB")
    text = path.read_text(encoding="utf-8-sig")
    candidates = []
    for line in text.splitlines():
        if line.strip().startswith("OPENAI_API_KEY="):
            candidates.append(line.split("=", 1)[1].strip().strip("\"'"))
    if not candidates and len(text.splitlines()) == 1:
        candidates.append(text.strip().strip("\"'"))
    keys = list(dict.fromkeys(value for value in candidates if value))
    if len(keys) != 1:
        raise ValueError("--key-file must contain exactly one OpenAI API key")
    return keys[0]


def call_openai(api_key: str, prompt: str | None = None, timeout: float = 120.0) -> tuple[ImageValidation, str | None]:
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
    parser.add_argument("--key-file", type=Path)
    args = parser.parse_args(argv)
    if not args.confirm_paid_call:
        parser.error("--confirm-paid-call is required")
    try:
        api_key = load_api_key(args.key_file)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        image, request_id = call_openai(api_key)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "PASS", "model": OPENAI_IMAGE_MODEL, "calls": 1,
        "image_bytes": image.byte_count, "image_format": image.image_format,
        "width": image.width, "height": image.height,
        "prompt_source": "generated_first_scene",
        "request_id_present": bool(request_id), "image_saved": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
