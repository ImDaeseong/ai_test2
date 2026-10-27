"""Prepare and execute official community publishing API requests with explicit consent."""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


LOGGER = logging.getLogger(__name__)


class PublishError(RuntimeError):
    """Report a sanitized provider failure at the outbound HTTP boundary."""


class UnsupportedAutomationError(PublishError):
    """Stop when no verified official API supports the requested publishing action."""


@dataclass(frozen=True)
class ApiRequest:
    """Describe one outbound request without storing authentication secrets in its URL."""

    method: str
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    body: Mapping[str, Any] | None = None
    form: Mapping[str, Any] | None = None

    def safe_dict(self) -> dict[str, Any]:
        """Return a credential-free request preview for logs and dry runs."""
        safe_headers = {key: "<redacted>" if key.lower() == "authorization" else value for key, value in self.headers.items()}
        return {"method": self.method, "url": self.url, "headers": safe_headers, "body": self.body, "form": self.form}


@dataclass(frozen=True)
class PublishRequest:
    """Represent platform-neutral content supplied by the operator."""

    text: str
    media_url: str | None = None
    media_type: str | None = None
    title: str | None = None
    alt_text: str | None = None
    privacy_level: str | None = None
    media_id: str | None = None


class HttpTransport:
    """Send JSON or form requests and convert network failures into sanitized diagnostics."""

    def send(self, request: ApiRequest, *, timeout: float = 30.0) -> dict[str, Any]:
        """Execute one request and return a decoded JSON object."""
        headers = dict(request.headers)
        data = None
        if request.body is not None:
            data = json.dumps(request.body).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        elif request.form is not None:
            data = urlencode(request.form).encode("utf-8")
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        outgoing = Request(request.url, data=data, headers=headers, method=request.method)
        try:
            with urlopen(outgoing, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
                payload = json.loads(raw) if raw else {}
                response_id = response.headers.get("x-restli-id")
                if response_id:
                    payload["_response_id"] = response_id
        except HTTPError as exc:
            safe_exc = PublishError(f"provider HTTP error: {exc.code}")
            LOGGER.error("provider_http_error boundary=community_publish status=%s", exc.code, exc_info=(type(safe_exc), safe_exc, exc.__traceback__))
            raise PublishError(f"provider HTTP error: {exc.code}") from exc
        except (URLError, TimeoutError) as exc:
            safe_exc = PublishError("provider network error")
            LOGGER.error("provider_network_error boundary=community_publish", exc_info=(type(safe_exc), safe_exc, exc.__traceback__))
            raise PublishError("provider network error") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            safe_exc = PublishError("provider returned invalid JSON")
            LOGGER.error("provider_response_error boundary=community_publish", exc_info=(type(safe_exc), safe_exc, exc.__traceback__))
            raise PublishError("provider returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise PublishError("provider returned a non-object JSON response")
        return payload


class BaseAdapter:
    """Define the shared preview and explicit-confirmation publishing contract."""

    name = "base"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build the first safe provider request without making a network call."""
        raise NotImplementedError

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Publish content after the CLI has obtained explicit operator confirmation."""
        requests = self.preview(content, env)
        if len(requests) != 1:
            raise PublishError("adapter requires a specialized publish workflow")
        return transport.send(requests[0])

    @staticmethod
    def required(env: Mapping[str, str], key: str) -> str:
        """Return one required environment value or fail before any network call."""
        value = env.get(key, "").strip()
        if not value:
            raise PublishError(f"missing environment variable: {key}")
        return value

    @staticmethod
    def bearer(token: str) -> dict[str, str]:
        """Build a bearer header that safe previews redact."""
        return {"Authorization": f"Bearer {token}"}


class ThreadsAdapter(BaseAdapter):
    """Publish text, image, or video posts through the official Threads API."""

    name = "threads"
    base_url = "https://graph.threads.net/v1.0"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build a Threads media-container request."""
        user_id = self.required(env, "THREADS_USER_ID")
        token = self.required(env, "THREADS_ACCESS_TOKEN")
        media_type = (content.media_type or ("TEXT" if not content.media_url else "IMAGE")).upper()
        if media_type not in {"TEXT", "IMAGE", "VIDEO"}:
            raise PublishError("Threads supports TEXT, IMAGE, or VIDEO in this beginner adapter")
        form: dict[str, Any] = {"media_type": media_type, "text": content.text}
        if media_type == "IMAGE":
            form["image_url"] = _https_url(content.media_url)
        elif media_type == "VIDEO":
            form["video_url"] = _https_url(content.media_url)
        return [ApiRequest("POST", f"{self.base_url}/{user_id}/threads", self.bearer(token), form=form)]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Create and then publish a Threads media container."""
        created = transport.send(self.preview(content, env)[0])
        creation_id = _response_id(created, "Threads media container")
        user_id = self.required(env, "THREADS_USER_ID")
        token = self.required(env, "THREADS_ACCESS_TOKEN")
        _wait_for_meta_container(
            ApiRequest("GET", f"{self.base_url}/{creation_id}?fields=id,status,error_message", self.bearer(token)),
            transport,
            status_field="status",
        )
        result = transport.send(ApiRequest("POST", f"{self.base_url}/{user_id}/threads_publish", self.bearer(token), form={"creation_id": creation_id}))
        return {"platform": self.name, "container_id": creation_id, "post_id": _response_id(result, "Threads post")}


class InstagramAdapter(BaseAdapter):
    """Publish media to an Instagram Professional account through the official API."""

    name = "instagram"
    base_url = "https://graph.instagram.com/v24.0"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build an Instagram media-container request."""
        user_id = self.required(env, "INSTAGRAM_USER_ID")
        token = self.required(env, "INSTAGRAM_ACCESS_TOKEN")
        media_type = (content.media_type or "IMAGE").upper()
        form: dict[str, Any] = {"caption": content.text}
        if media_type == "IMAGE":
            form["image_url"] = _https_url(content.media_url)
        elif media_type in {"VIDEO", "REELS", "STORIES"}:
            form.update({"media_type": media_type, "video_url": _https_url(content.media_url)})
        else:
            raise PublishError("Instagram adapter supports IMAGE, VIDEO, REELS, or STORIES")
        return [ApiRequest("POST", f"{self.base_url}/{user_id}/media", self.bearer(token), form=form)]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Create and publish an Instagram media container."""
        created = transport.send(self.preview(content, env)[0])
        creation_id = _response_id(created, "Instagram media container")
        user_id = self.required(env, "INSTAGRAM_USER_ID")
        token = self.required(env, "INSTAGRAM_ACCESS_TOKEN")
        _wait_for_meta_container(
            ApiRequest("GET", f"{self.base_url}/{creation_id}?fields=status_code", self.bearer(token)),
            transport,
            status_field="status_code",
        )
        result = transport.send(ApiRequest("POST", f"{self.base_url}/{user_id}/media_publish", self.bearer(token), form={"creation_id": creation_id}))
        return {"platform": self.name, "container_id": creation_id, "post_id": _response_id(result, "Instagram post")}


class TelegramAdapter(BaseAdapter):
    """Send text, photo, or video messages through the Telegram Bot API."""

    name = "telegram"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build a Telegram Bot API request while keeping the bot token out of previews."""
        self.required(env, "TELEGRAM_BOT_TOKEN")
        chat_id = self.required(env, "TELEGRAM_CHAT_ID")
        media_type = (content.media_type or "TEXT").upper()
        method = {"TEXT": "sendMessage", "IMAGE": "sendPhoto", "VIDEO": "sendVideo"}.get(media_type)
        if not method:
            raise PublishError("Telegram adapter supports TEXT, IMAGE, or VIDEO")
        body: dict[str, Any] = {"chat_id": chat_id}
        if media_type == "TEXT":
            body["text"] = _required_text(content.text)
        else:
            body["caption"] = content.text
            body["photo" if media_type == "IMAGE" else "video"] = _https_url(content.media_url)
        return [ApiRequest("POST", f"https://api.telegram.org/bot<redacted>/{method}", body=body)]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Send a Telegram message to the configured chat or channel."""
        preview = self.preview(content, env)[0]
        token = self.required(env, "TELEGRAM_BOT_TOKEN")
        actual = ApiRequest(preview.method, preview.url.replace("<redacted>", token), preview.headers, preview.body, preview.form)
        result = transport.send(actual)
        message_id = result.get("result", {}).get("message_id") if isinstance(result.get("result"), dict) else None
        if not result.get("ok") or message_id is None:
            raise PublishError("Telegram did not return a successful message ID")
        return {"platform": self.name, "post_id": str(message_id)}


class TikTokAdapter(BaseAdapter):
    """Initialize direct photo or video posts through TikTok's Content Posting API."""

    name = "tiktok"
    base_url = "https://open.tiktokapis.com/v2/post/publish"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build a verified-domain pull request for TikTok Direct Post."""
        token = self.required(env, "TIKTOK_ACCESS_TOKEN")
        creator_info = ApiRequest("POST", f"{self.base_url}/creator_info/query/", {**self.bearer(token), "Content-Type": "application/json; charset=UTF-8"}, body={})
        media_type = (content.media_type or "VIDEO").upper()
        privacy = content.privacy_level or "SELF_ONLY"
        if media_type == "VIDEO":
            url = f"{self.base_url}/video/init/"
            body = {"post_info": {"title": content.title or content.text, "privacy_level": privacy}, "source_info": {"source": "PULL_FROM_URL", "video_url": _https_url(content.media_url)}}
        elif media_type == "PHOTO":
            url = f"{self.base_url}/content/init/"
            body = {"post_info": {"title": content.title or "", "description": content.text, "privacy_level": privacy}, "source_info": {"source": "PULL_FROM_URL", "photo_images": [_https_url(content.media_url)], "photo_cover_index": 0}, "post_mode": "DIRECT_POST", "media_type": "PHOTO"}
        else:
            raise PublishError("TikTok adapter supports VIDEO or PHOTO")
        return [creator_info, ApiRequest("POST", url, {**self.bearer(token), "Content-Type": "application/json; charset=UTF-8"}, body=body)]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Initialize TikTok Direct Post and return its asynchronous publish ID."""
        requests = self.preview(content, env)
        creator = transport.send(requests[0])
        _validate_tiktok_response(creator, "creator info")
        creator_data = creator.get("data") if isinstance(creator.get("data"), dict) else {}
        allowed = creator_data.get("privacy_level_options")
        requested_privacy = requests[1].body["post_info"]["privacy_level"]
        if isinstance(allowed, list) and requested_privacy not in allowed:
            raise PublishError(f"TikTok creator does not allow privacy level: {requested_privacy}")
        result = transport.send(requests[1])
        _validate_tiktok_response(result, "publish initialization")
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        publish_id = data.get("publish_id")
        if not publish_id:
            raise PublishError("TikTok did not return a publish_id")
        final = wait_for_tiktok(str(publish_id), env, transport)
        post_ids = final.get("publicly_available_post_id", final.get("publicaly_available_post_id", []))
        return {"platform": self.name, "publish_id": str(publish_id), "status": str(final.get("status", "PUBLISH_COMPLETE")), "post_ids": post_ids}


class XAdapter(BaseAdapter):
    """Create text or URL-based posts through X API v2."""

    name = "x"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build an X create-post request."""
        token = self.required(env, "X_USER_ACCESS_TOKEN")
        if content.media_url:
            raise PublishError("X media upload workflow is not implemented; publish text/URL only")
        body: dict[str, Any] = {"text": _required_text(content.text)}
        return [ApiRequest("POST", "https://api.x.com/2/tweets", self.bearer(token), body=body)]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Create an X post and return its provider ID."""
        result = transport.send(self.preview(content, env)[0])
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        return {"platform": self.name, "post_id": _response_id(data, "X post")}


class KakaoAdapter(BaseAdapter):
    """Send a KakaoTalk memo to the authenticated user's own chat, not a public community."""

    name = "kakao"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build KakaoTalk's official send-to-self default-template request."""
        token = self.required(env, "KAKAO_ACCESS_TOKEN")
        template = {"object_type": "text", "text": _required_text(content.text), "link": {"web_url": content.media_url or "https://developers.kakao.com", "mobile_web_url": content.media_url or "https://developers.kakao.com"}}
        return [ApiRequest("POST", "https://kapi.kakao.com/v2/api/talk/memo/default/send", self.bearer(token), form={"template_object": json.dumps(template, ensure_ascii=False)})]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Send a KakaoTalk memo only when Kakao reports result_code zero."""
        result = transport.send(self.preview(content, env)[0])
        if result.get("result_code") != 0:
            raise PublishError(f"KakaoTalk send failed: result_code={result.get('result_code', 'missing')}")
        return {"platform": self.name, "result_code": 0}


class FacebookPageAdapter(BaseAdapter):
    """Publish text, links, remote images, or remote videos to a managed Facebook Page."""

    name = "facebook_page"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build a Facebook Page publishing request using a Page access token."""
        page_id = self.required(env, "FACEBOOK_PAGE_ID")
        token = self.required(env, "FACEBOOK_PAGE_ACCESS_TOKEN")
        version = env.get("META_GRAPH_VERSION", "v24.0").strip() or "v24.0"
        base = f"https://graph.facebook.com/{version}/{page_id}"
        media_type = (content.media_type or "TEXT").upper()
        if media_type == "TEXT":
            return [ApiRequest("POST", f"{base}/feed", self.bearer(token), form={"message": _required_text(content.text)})]
        if media_type == "LINK":
            return [ApiRequest("POST", f"{base}/feed", self.bearer(token), form={"message": content.text, "link": _https_url(content.media_url)})]
        if media_type == "IMAGE":
            return [ApiRequest("POST", f"{base}/photos", self.bearer(token), form={"caption": content.text, "url": _https_url(content.media_url)})]
        if media_type == "VIDEO":
            return [ApiRequest("POST", f"{base}/videos", self.bearer(token), form={"description": content.text, "file_url": _https_url(content.media_url)})]
        raise PublishError("Facebook Page adapter supports TEXT, LINK, IMAGE, or VIDEO")

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Publish one Facebook Page item and require a provider object ID."""
        result = transport.send(self.preview(content, env)[0])
        return {"platform": self.name, "post_id": _response_id(result, "Facebook Page post")}


class LinkedInAdapter(BaseAdapter):
    """Publish text or a previously uploaded media asset through LinkedIn's Posts API."""

    name = "linkedin"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build a LinkedIn organic post request without implementing binary asset upload."""
        token = self.required(env, "LINKEDIN_ACCESS_TOKEN")
        author = self.required(env, "LINKEDIN_AUTHOR_URN")
        version = env.get("LINKEDIN_VERSION", "202610").strip() or "202610"
        media_type = (content.media_type or "TEXT").upper()
        body: dict[str, Any] = {
            "author": author,
            "commentary": _required_text(content.text),
            "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }
        if media_type != "TEXT":
            if media_type not in {"IMAGE", "VIDEO", "DOCUMENT"}:
                raise PublishError("LinkedIn adapter supports TEXT or a pre-uploaded IMAGE, VIDEO, or DOCUMENT asset")
            if not content.media_id or not content.media_id.startswith("urn:li:"):
                raise PublishError("LinkedIn media posts require --media-id with an uploaded urn:li: asset")
            body["content"] = {"media": {"id": content.media_id, "title": content.title or media_type.title(), "altText": content.alt_text or ""}}
        headers = {**self.bearer(token), "LinkedIn-Version": version, "X-Restli-Protocol-Version": "2.0.0"}
        return [ApiRequest("POST", "https://api.linkedin.com/rest/posts", headers, body=body)]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Publish a LinkedIn post and read its ID from the response header."""
        result = transport.send(self.preview(content, env)[0])
        return {"platform": self.name, "post_id": _response_id(result, "LinkedIn post", key="_response_id")}


class DiscordAdapter(BaseAdapter):
    """Post text or remote-media references through a Discord incoming webhook."""

    name = "discord"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build a Discord webhook request while redacting its credential-bearing URL."""
        self.required(env, "DISCORD_WEBHOOK_URL")
        media_type = (content.media_type or "TEXT").upper()
        body: dict[str, Any] = {"allowed_mentions": {"parse": []}}
        if media_type == "TEXT":
            body["content"] = _required_text(content.text)
        elif media_type == "IMAGE":
            body["content"] = content.text
            body["embeds"] = [{"image": {"url": _https_url(content.media_url)}}]
        elif media_type in {"VIDEO", "AUDIO", "DOCUMENT", "LINK"}:
            body["content"] = "\n".join(part for part in (content.text, _https_url(content.media_url)) if part)
        else:
            raise PublishError("Discord adapter supports TEXT, LINK, IMAGE, VIDEO, AUDIO, or DOCUMENT")
        return [ApiRequest("POST", "https://discord.com/api/webhooks/<redacted>?wait=true", body=body)]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Execute a Discord webhook and return the created message ID."""
        preview = self.preview(content, env)[0]
        webhook = self.required(env, "DISCORD_WEBHOOK_URL")
        separator = "&" if "?" in webhook else "?"
        actual_url = webhook if "wait=" in webhook else f"{webhook}{separator}wait=true"
        result = transport.send(ApiRequest(preview.method, actual_url, preview.headers, preview.body, preview.form))
        return {"platform": self.name, "post_id": _response_id(result, "Discord message")}


class RedditAdapter(BaseAdapter):
    """Submit text or link posts to a configured subreddit through OAuth."""

    name = "reddit"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build a Reddit text or link submission request."""
        token = self.required(env, "REDDIT_ACCESS_TOKEN")
        subreddit = self.required(env, "REDDIT_SUBREDDIT")
        media_type = (content.media_type or "TEXT").upper()
        form: dict[str, Any] = {"api_type": "json", "sr": subreddit, "title": content.title or _required_text(content.text)[:300], "resubmit": "true"}
        if media_type == "TEXT":
            form.update({"kind": "self", "text": content.text})
        elif media_type == "LINK":
            form.update({"kind": "link", "url": _https_url(content.media_url)})
        else:
            raise PublishError("Reddit image/video upload requires a separate media workflow; use TEXT or LINK")
        return [ApiRequest("POST", "https://oauth.reddit.com/api/submit", self.bearer(token), form=form)]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Submit a Reddit post and reject the API's nested validation errors."""
        result = transport.send(self.preview(content, env)[0])
        json_result = result.get("json") if isinstance(result.get("json"), dict) else {}
        errors = json_result.get("errors")
        if errors:
            raise PublishError("Reddit rejected the post")
        data = json_result.get("data") if isinstance(json_result.get("data"), dict) else {}
        post_id = data.get("id") or data.get("name") or data.get("url")
        if not post_id:
            raise PublishError("Reddit response did not contain a post identifier")
        return {"platform": self.name, "post_id": str(post_id)}


class NaverCafeAdapter(BaseAdapter):
    """Publish text and links to a Naver Cafe board through the official OAuth API."""

    name = "naver_cafe"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Build a Naver Cafe text post; local multipart images remain a separate workflow."""
        token = self.required(env, "NAVER_ACCESS_TOKEN")
        cafe_id = self.required(env, "NAVER_CAFE_ID")
        menu_id = self.required(env, "NAVER_CAFE_MENU_ID")
        media_type = (content.media_type or "TEXT").upper()
        if media_type not in {"TEXT", "LINK"}:
            raise PublishError("Naver Cafe adapter currently supports TEXT or LINK; official image multipart upload is not implemented")
        body_text = _required_text(content.text)
        if media_type == "LINK":
            body_text = f"{body_text}\n{_https_url(content.media_url)}"
        form = {"subject": content.title or body_text[:80], "content": body_text}
        return [ApiRequest("POST", f"https://openapi.naver.com/v1/cafe/{cafe_id}/menu/{menu_id}/articles", self.bearer(token), form=form)]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Publish a Naver Cafe post and extract the nested article identifier."""
        result = transport.send(self.preview(content, env)[0])
        message = result.get("message") if isinstance(result.get("message"), dict) else {}
        nested = message.get("result") if isinstance(message.get("result"), dict) else {}
        post_id = nested.get("articleId")
        if post_id is None:
            raise PublishError("Naver Cafe response did not contain articleId")
        return {"platform": self.name, "post_id": str(post_id), "url": nested.get("articleUrl")}


class YouTubeAdapter(BaseAdapter):
    """Expose YouTube's video-only boundary until resumable binary upload is implemented."""

    name = "youtube"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Stop unsupported community-post automation and incomplete video uploads."""
        self.required(env, "YOUTUBE_ACCESS_TOKEN")
        media_type = (content.media_type or "TEXT").upper()
        if media_type != "VIDEO":
            raise UnsupportedAutomationError("YouTube Data API has no verified Community text/image post creation endpoint")
        raise UnsupportedAutomationError("YouTube video upload requires a local/resumable binary uploader, which is not implemented")


class NaverAdapter(BaseAdapter):
    """Provide Naver's user-mediated share page separately from the Cafe write API."""

    name = "naver"

    def preview(self, content: PublishRequest, env: Mapping[str, str]) -> list[ApiRequest]:
        """Prepare Naver's user-mediated share page without claiming automatic publishing."""
        target_url = _https_url(content.media_url)
        query = urlencode({"url": target_url, "title": content.title or content.text})
        return [ApiRequest("GET", f"https://share.naver.com/web/shareView?{query}")]

    def publish(self, content: PublishRequest, env: Mapping[str, str], transport: HttpTransport) -> dict[str, Any]:
        """Block unattended Naver publishing because the official route requires user interaction."""
        raise UnsupportedAutomationError("NAVER SHARE HOLD: this route is user-mediated; use naver_cafe for official Cafe text/link posting")


ADAPTERS: dict[str, BaseAdapter] = {
    adapter.name: adapter
    for adapter in (
        ThreadsAdapter(), InstagramAdapter(), TelegramAdapter(), TikTokAdapter(), XAdapter(), KakaoAdapter(),
        FacebookPageAdapter(), LinkedInAdapter(), DiscordAdapter(), RedditAdapter(), NaverCafeAdapter(), YouTubeAdapter(), NaverAdapter(),
    )
}


def _https_url(value: str | None) -> str:
    """Require a provider-fetchable HTTPS URL for remote media."""
    if not value or not value.startswith("https://"):
        raise PublishError("media_url must start with https://")
    return value


def _required_text(value: str) -> str:
    """Require visible text for adapters whose current mode cannot publish media alone."""
    if not value.strip():
        raise PublishError("text must not be empty")
    return value


def _response_id(payload: Mapping[str, Any], label: str, *, key: str = "id") -> str:
    """Extract a required provider object ID."""
    value = payload.get(key)
    if value is None or str(value).strip() == "":
        raise PublishError(f"{label} response did not contain id")
    return str(value)


def _wait_for_meta_container(
    request: ApiRequest,
    transport: HttpTransport,
    *,
    status_field: str,
    max_checks: int = 12,
) -> None:
    """Wait for a Meta media container using a bounded polling window."""
    for attempt in range(max_checks):
        payload = transport.send(request)
        status = str(payload.get(status_field, "")).upper()
        if status in {"FINISHED", "PUBLISHED"}:
            return
        if status in {"ERROR", "EXPIRED"}:
            raise PublishError(str(payload.get("error_message") or f"Meta container failed: {status}"))
        if status not in {"IN_PROGRESS"}:
            raise PublishError(f"unexpected Meta container status: {status or 'missing'}")
        if attempt + 1 < max_checks:
            time.sleep(2)
    raise PublishError("Meta container processing did not finish within the bounded polling window")


def wait_for_tiktok(publish_id: str, env: Mapping[str, str], transport: HttpTransport, *, max_checks: int = 12) -> dict[str, Any]:
    """Poll TikTok status with a bounded retry count and return the final provider data."""
    token = BaseAdapter.required(env, "TIKTOK_ACCESS_TOKEN")
    for attempt in range(max_checks):
        payload = transport.send(ApiRequest("POST", f"{TikTokAdapter.base_url}/status/fetch/", BaseAdapter.bearer(token), body={"publish_id": publish_id}))
        _validate_tiktok_response(payload, "status fetch")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        status = str(data.get("status", "")).upper()
        if status in {"PUBLISH_COMPLETE", "SEND_TO_USER"}:
            return data
        if status in {"FAILED", "PUBLISH_FAILED"}:
            raise PublishError(f"TikTok publishing failed: {data.get('fail_reason', 'unknown')}")
        if attempt + 1 < max_checks:
            time.sleep(2)
    raise PublishError("TikTok publishing did not finish within the bounded polling window")


def _validate_tiktok_response(payload: Mapping[str, Any], operation: str) -> None:
    """Reject TikTok's HTTP-200 error envelope before reading response data."""
    error = payload.get("error")
    if not isinstance(error, Mapping):
        raise PublishError(f"TikTok {operation} response did not contain an error envelope")
    code = error.get("code")
    if code != "ok":
        raise PublishError(f"TikTok {operation} failed: {code or 'missing error code'}")


def load_environment() -> Mapping[str, str]:
    """Return process environment values without reading or persisting a secret file."""
    return os.environ
