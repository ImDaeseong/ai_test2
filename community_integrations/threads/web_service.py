"""Translate web composer payloads into the verified Threads publishing flow."""

from __future__ import annotations

import time
from typing import Any, Callable

from examples.threads_python.threads_client import (
    ThreadsClient,
    build_container_request,
    build_publish_request,
    build_status_request,
    container_decision,
)


def prepare_web_request(user_id: str, payload: dict[str, Any]):
    """Validate a browser payload and build a token-free provider request."""
    kind = str(payload.get("kind", "")).upper()
    text = str(payload.get("text", "")).strip()
    url = str(payload.get("url", "")).strip()
    alt_text = str(payload.get("alt_text", "")).strip()
    if len(text) > 500:
        raise ValueError("본문은 500자를 넘을 수 없습니다")
    if url and not url.startswith("https://"):
        raise ValueError("미디어와 링크 URL은 https://로 시작해야 합니다")
    if kind == "LINK":
        return build_container_request(user_id, "TEXT", text=text or None, link_attachment=url or None)
    if kind == "IMAGE":
        return build_container_request(user_id, "IMAGE", text=text or None, image_url=url or None, alt_text=alt_text or None)
    if kind == "VIDEO":
        return build_container_request(user_id, "VIDEO", text=text or None, video_url=url or None, alt_text=alt_text or None)
    if kind == "TEXT":
        return build_container_request(user_id, "TEXT", text=text or None)
    raise ValueError("지원하지 않는 게시 유형입니다")


def prepare_web_plan(user_id: str, payload: dict[str, Any]) -> list:
    """Build single-post or carousel-child requests from a unified composer payload."""
    attachments = payload.get("attachments")
    if not isinstance(attachments, list):
        return [prepare_web_request(user_id, payload)]
    text = str(payload.get("text", "")).strip()
    if not attachments:
        return [prepare_web_request(user_id, {"kind": "TEXT", "text": text})]
    if len(attachments) > 20:
        raise ValueError("첨부는 최대 20개까지 가능합니다")
    requests = []
    for item in attachments:
        if not isinstance(item, dict):
            raise ValueError("첨부 형식이 올바르지 않습니다")
        kind = str(item.get("kind", "")).upper()
        url = str(item.get("url", "")).strip()
        alt = str(item.get("alt_text", "")).strip()
        if not url.startswith("https://") or kind not in {"IMAGE", "VIDEO"}:
            raise ValueError("첨부는 HTTPS 이미지 또는 영상이어야 합니다")
        field = "image_url" if kind == "IMAGE" else "video_url"
        values = {field: url, "alt_text": alt or None}
        if len(attachments) > 1:
            values["is_carousel_item"] = True
        else:
            values["text"] = text or None
        requests.append(build_container_request(user_id, kind, **values))
    return requests


def publish_web_request(
    client: ThreadsClient,
    user_id: str,
    payload: dict[str, Any],
    *,
    max_checks: int = 12,
    wait: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Create, reconcile, and publish one Threads media container."""
    requests = prepare_web_plan(user_id, payload)
    if len(requests) > 1:
        child_ids = []
        for request in requests:
            child = client.execute(request)
            child_id = str(child.get("id", ""))
            if not child_id:
                raise RuntimeError("Threads가 캐러셀 자식 ID를 반환하지 않았습니다")
            _wait_until_finished(client, child_id, max_checks, wait)
            child_ids.append(child_id)
        parent = build_container_request(user_id, "CAROUSEL", text=str(payload.get("text", "")).strip() or None, children=child_ids)
        created = client.execute(parent)
    else:
        created = client.execute(requests[0])
    container_id = str(created.get("id", ""))
    if not container_id:
        raise RuntimeError("Threads가 컨테이너 ID를 반환하지 않았습니다")
    last_status = ""
    for check in range(max_checks):
        status_payload = client.execute(build_status_request(container_id))
        last_status = str(status_payload.get("status", ""))
        decision = container_decision(last_status)
        if decision == "PUBLISH":
            published = client.execute(build_publish_request(user_id, container_id))
            post_id = str(published.get("id", ""))
            if not post_id:
                raise RuntimeError("Threads가 게시물 ID를 반환하지 않았습니다")
            return {"container_id": container_id, "post_id": post_id, "status": "PUBLISHED"}
        if decision == "DONE":
            return {"container_id": container_id, "post_id": container_id, "status": "PUBLISHED"}
        if decision in {"STOP", "HOLD"}:
            message = status_payload.get("error_message") or f"예상하지 못한 컨테이너 상태: {last_status or '없음'}"
            raise RuntimeError(str(message))
        if check + 1 < max_checks:
            wait(1.0)
    raise TimeoutError(f"Threads 미디어 처리가 제한 시간 안에 끝나지 않았습니다: {last_status}")


def _wait_until_finished(client: ThreadsClient, container_id: str, max_checks: int, wait: Callable[[float], None]) -> None:
    """Wait until one carousel child is ready without publishing it directly."""
    for check in range(max_checks):
        status_payload = client.execute(build_status_request(container_id))
        decision = container_decision(str(status_payload.get("status", "")))
        if decision == "PUBLISH":
            return
        if decision in {"STOP", "HOLD"}:
            raise RuntimeError(str(status_payload.get("error_message") or "캐러셀 자식 처리 실패"))
        if check + 1 < max_checks:
            wait(1.0)
    raise TimeoutError("캐러셀 자식 처리가 제한 시간 안에 끝나지 않았습니다")
