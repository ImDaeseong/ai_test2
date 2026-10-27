"""Build and optionally execute the minimal official Threads publishing flow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen


API_BASE = "https://graph.threads.net"
TERMINAL_FAILURES = {"ERROR", "EXPIRED"}


class ThreadsApiError(RuntimeError):
    """Expose diagnosable provider fields without retaining a credential-bearing URL."""

    def __init__(self, status: int, payload: Mapping[str, Any]) -> None:
        error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        self.status = status
        self.code = error.get("code")
        self.subcode = error.get("error_subcode")
        self.trace_id = error.get("fbtrace_id")
        message = error.get("message") or "Threads API request failed"
        super().__init__(f"HTTP {status}: {message} (code={self.code}, subcode={self.subcode}, trace={self.trace_id})")


@dataclass(frozen=True)
class PreparedRequest:
    """Represent an HTTP request without exposing an access token."""

    method: str
    url: str
    params: Mapping[str, str]

    def safe_dict(self) -> dict[str, Any]:
        """Return a display-safe description of the prepared request."""
        return {"method": self.method, "url": self.url, "params": dict(self.params)}


def build_container_request(user_id: str, media_type: str, **fields: object) -> PreparedRequest:
    """Build a Threads media-container request for a supported content type."""
    normalized = media_type.upper()
    if normalized == "AUDIO":
        raise ValueError("Threads API has no verified standalone AUDIO publishing type")
    if normalized not in {"TEXT", "IMAGE", "VIDEO", "CAROUSEL"}:
        raise ValueError(f"unsupported media_type: {media_type}")
    _validate_container_fields(normalized, fields)
    params = {"media_type": normalized}
    params.update({key: _encode_value(value) for key, value in fields.items() if value is not None})
    return PreparedRequest("POST", f"{API_BASE}/{user_id}/threads", params)


def _validate_container_fields(media_type: str, fields: Mapping[str, object]) -> None:
    """Reject incomplete content before it reaches the provider API."""
    if media_type == "TEXT" and not (fields.get("text") or fields.get("link_attachment")):
        raise ValueError("TEXT requires text or link_attachment")
    required_url = {"IMAGE": "image_url", "VIDEO": "video_url"}.get(media_type)
    if required_url and not fields.get(required_url):
        raise ValueError(f"{media_type} requires {required_url}")
    if media_type == "CAROUSEL":
        children = fields.get("children")
        if not isinstance(children, (list, tuple)) or not 2 <= len(children) <= 20:
            raise ValueError("CAROUSEL requires 2 to 20 child container IDs")


def build_status_request(container_id: str) -> PreparedRequest:
    """Build a request that distinguishes container readiness from publication."""
    return PreparedRequest("GET", f"{API_BASE}/{container_id}", {"fields": "id,status,error_message"})


def build_profile_request() -> PreparedRequest:
    """Build the minimal account-verification request used by the local studio."""
    return PreparedRequest("GET", f"{API_BASE}/me", {"fields": "id,username,name,threads_profile_picture_url"})


def build_publish_request(user_id: str, container_id: str) -> PreparedRequest:
    """Build the final container-publication request."""
    return PreparedRequest("POST", f"{API_BASE}/{user_id}/threads_publish", {"creation_id": container_id})


def container_decision(status: str) -> str:
    """Map a provider container status to the caller's next safe action."""
    normalized = status.upper()
    if normalized == "FINISHED":
        return "PUBLISH"
    if normalized in {"IN_PROGRESS", "PUBLISHED"}:
        return "WAIT" if normalized == "IN_PROGRESS" else "DONE"
    if normalized in TERMINAL_FAILURES:
        return "STOP"
    return "HOLD"


class ThreadsClient:
    """Execute prepared Threads requests with a caller-supplied user token."""

    def __init__(self, access_token: str, timeout: float = 30.0) -> None:
        if not access_token:
            raise ValueError("access_token is required")
        self._access_token = access_token
        self._timeout = timeout

    def execute(self, prepared: PreparedRequest) -> dict[str, Any]:
        """Execute one prepared request and return its decoded JSON object."""
        params = dict(prepared.params)
        params["access_token"] = self._access_token
        body = urlencode(params).encode("utf-8") if prepared.method == "POST" else None
        url = prepared.url if body is not None else f"{prepared.url}?{urlencode(params)}"
        request = Request(url, data=body, method=prepared.method)
        request.add_header("Accept", "application/json")
        try:
            with urlopen(request, timeout=self._timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            try:
                error_payload = json.loads(exc.read().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                error_payload = {}
            raise ThreadsApiError(exc.code, error_payload) from None
        if not isinstance(payload, dict):
            raise ValueError("Threads API returned a non-object JSON response")
        return payload


def _encode_value(value: object) -> str:
    """Encode collection values using the comma-separated Graph API convention."""
    if isinstance(value, (list, tuple)):
        return ",".join(str(item) for item in value)
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)
