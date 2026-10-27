"""Verify provider request contracts without calling external APIs."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

import cli
from community_integrations.publisher import ADAPTERS, HttpTransport, PublishError, PublishRequest, UnsupportedAutomationError


ENV = {
    "THREADS_USER_ID": "threads-user",
    "THREADS_ACCESS_TOKEN": "threads-secret",
    "INSTAGRAM_USER_ID": "ig-user",
    "INSTAGRAM_ACCESS_TOKEN": "ig-secret",
    "TELEGRAM_BOT_TOKEN": "telegram-secret",
    "TELEGRAM_CHAT_ID": "@channel",
    "TIKTOK_ACCESS_TOKEN": "tiktok-secret",
    "X_USER_ACCESS_TOKEN": "x-secret",
    "KAKAO_ACCESS_TOKEN": "kakao-secret",
    "NAVER_ACCESS_TOKEN": "naver-secret",
    "NAVER_CAFE_ID": "1234",
    "NAVER_CAFE_MENU_ID": "5",
    "FACEBOOK_PAGE_ID": "page-1",
    "FACEBOOK_PAGE_ACCESS_TOKEN": "facebook-secret",
    "LINKEDIN_ACCESS_TOKEN": "linkedin-secret",
    "LINKEDIN_AUTHOR_URN": "urn:li:organization:123",
    "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/123/discord-secret",
    "REDDIT_ACCESS_TOKEN": "reddit-secret",
    "REDDIT_SUBREDDIT": "example",
    "YOUTUBE_ACCESS_TOKEN": "youtube-secret",
}


class FakeTransport(HttpTransport):
    """Return deterministic provider fixtures and record outbound requests."""

    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def send(self, request, *, timeout=30.0):
        """Record one request and return the next fixture."""
        self.requests.append(request)
        return next(self.responses)


class EmptyHeaderResponse:
    """Emulate a successful empty provider response carrying a post ID header."""

    headers = {"x-restli-id": "urn:li:share:123"}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return b""


class AdapterContractTests(unittest.TestCase):
    """Cover all supported and intentionally unsupported platform contracts."""

    def test_previews_redact_every_secret(self) -> None:
        cases = {
            "threads": PublishRequest("hello"),
            "instagram": PublishRequest("hello", "https://example.test/a.jpg", "IMAGE"),
            "telegram": PublishRequest("hello"),
            "tiktok": PublishRequest("hello", "https://example.test/a.mp4", "VIDEO"),
            "x": PublishRequest("hello"),
            "kakao": PublishRequest("hello"),
            "naver": PublishRequest("hello", "https://example.test/article", title="hello"),
            "naver_cafe": PublishRequest("hello", title="hello"),
            "facebook_page": PublishRequest("hello"),
            "linkedin": PublishRequest("hello"),
            "discord": PublishRequest("hello"),
            "reddit": PublishRequest("hello", title="hello"),
        }
        combined = str([request.safe_dict() for name, content in cases.items() for request in ADAPTERS[name].preview(content, ENV)])
        for secret in (value for key, value in ENV.items() if "TOKEN" in key):
            self.assertNotIn(secret, combined)

    def test_transport_accepts_empty_success_with_linkedin_id_header(self) -> None:
        with mock.patch("community_integrations.publisher.urlopen", return_value=EmptyHeaderResponse()):
            result = HttpTransport().send(ADAPTERS["linkedin"].preview(PublishRequest("hello"), ENV)[0])
        self.assertEqual(result["_response_id"], "urn:li:share:123")

    def test_threads_uses_create_then_publish(self) -> None:
        transport = FakeTransport([{"id": "container-1"}, {"status": "FINISHED"}, {"id": "post-1"}])
        result = ADAPTERS["threads"].publish(PublishRequest("hello"), ENV, transport)
        self.assertEqual(result["post_id"], "post-1")
        self.assertTrue(transport.requests[2].url.endswith("/threads_publish"))

    def test_instagram_uses_media_then_media_publish(self) -> None:
        transport = FakeTransport([{"id": "container-1"}, {"status_code": "FINISHED"}, {"id": "post-1"}])
        result = ADAPTERS["instagram"].publish(PublishRequest("caption", "https://example.test/a.jpg", "IMAGE"), ENV, transport)
        self.assertEqual(result["post_id"], "post-1")
        self.assertTrue(transport.requests[2].url.endswith("/media_publish"))

    def test_telegram_token_is_only_inserted_at_execution(self) -> None:
        preview = ADAPTERS["telegram"].preview(PublishRequest("hello"), ENV)[0]
        self.assertIn("<redacted>", preview.url)
        transport = FakeTransport([{"ok": True, "result": {"message_id": 7}}])
        result = ADAPTERS["telegram"].publish(PublishRequest("hello"), ENV, transport)
        self.assertEqual(result["post_id"], "7")
        self.assertIn("telegram-secret", transport.requests[0].url)

    def test_tiktok_defaults_to_private_direct_post(self) -> None:
        requests = ADAPTERS["tiktok"].preview(PublishRequest("caption", "https://example.test/a.mp4", "VIDEO"), ENV)
        self.assertTrue(requests[0].url.endswith("/creator_info/query/"))
        request = requests[1]
        self.assertEqual(request.body["post_info"]["privacy_level"], "SELF_ONLY")
        self.assertEqual(request.body["source_info"]["source"], "PULL_FROM_URL")

    def test_tiktok_queries_creator_then_waits_for_completion(self) -> None:
        transport = FakeTransport([
            {"data": {"privacy_level_options": ["SELF_ONLY"]}, "error": {"code": "ok"}},
            {"data": {"publish_id": "publish-1"}, "error": {"code": "ok"}},
            {"data": {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": ["post-1"]}, "error": {"code": "ok"}},
        ])
        result = ADAPTERS["tiktok"].publish(PublishRequest("caption", "https://example.test/a.mp4", "VIDEO"), ENV, transport)
        self.assertEqual(result["status"], "PUBLISH_COMPLETE")
        self.assertEqual(result["post_ids"], ["post-1"])

    def test_tiktok_rejects_creator_info_error_envelope(self) -> None:
        transport = FakeTransport([{"data": {}, "error": {"code": "scope_not_authorized"}}])
        with self.assertRaisesRegex(PublishError, "creator info failed: scope_not_authorized"):
            ADAPTERS["tiktok"].publish(PublishRequest("caption", "https://example.test/a.mp4", "VIDEO"), ENV, transport)

    def test_tiktok_rejects_status_error_envelope(self) -> None:
        transport = FakeTransport([
            {"data": {"privacy_level_options": ["SELF_ONLY"]}, "error": {"code": "ok"}},
            {"data": {"publish_id": "publish-1"}, "error": {"code": "ok"}},
            {"data": {}, "error": {"code": "access_token_invalid"}},
        ])
        with self.assertRaisesRegex(PublishError, "status fetch failed: access_token_invalid"):
            ADAPTERS["tiktok"].publish(PublishRequest("caption", "https://example.test/a.mp4", "VIDEO"), ENV, transport)

    def test_x_uses_current_v2_create_endpoint(self) -> None:
        request = ADAPTERS["x"].preview(PublishRequest("hello"), ENV)[0]
        self.assertEqual(request.url, "https://api.x.com/2/tweets")
        self.assertEqual(request.body, {"text": "hello"})

    def test_x_media_is_held_until_upload_workflow_is_implemented(self) -> None:
        with self.assertRaisesRegex(Exception, "media upload"):
            ADAPTERS["x"].preview(PublishRequest("hello", "https://example.test/a.jpg", "IMAGE"), ENV)

    def test_x_rejects_blank_text_before_network(self) -> None:
        with self.assertRaisesRegex(PublishError, "text must not be empty"):
            ADAPTERS["x"].preview(PublishRequest("   "), ENV)

    def test_kakao_is_send_to_self_not_public_posting(self) -> None:
        request = ADAPTERS["kakao"].preview(PublishRequest("hello"), ENV)[0]
        self.assertIn("/talk/memo/default/send", request.url)

    def test_kakao_requires_success_result_code(self) -> None:
        with self.assertRaisesRegex(PublishError, "result_code=missing"):
            ADAPTERS["kakao"].publish(PublishRequest("hello"), ENV, FakeTransport([{}]))
        result = ADAPTERS["kakao"].publish(PublishRequest("hello"), ENV, FakeTransport([{"result_code": 0}]))
        self.assertEqual(result["result_code"], 0)

    def test_naver_previews_manual_share_but_blocks_unattended_execution(self) -> None:
        content = PublishRequest("hello", "https://example.test/article", title="hello")
        preview = ADAPTERS["naver"].preview(content, ENV)[0]
        self.assertIn("share.naver.com/web/shareView", preview.url)
        with self.assertRaises(UnsupportedAutomationError):
            ADAPTERS["naver"].publish(content, ENV, FakeTransport([]))

    def test_naver_cafe_text_post_uses_official_write_endpoint(self) -> None:
        request = ADAPTERS["naver_cafe"].preview(PublishRequest("본문", title="제목"), ENV)[0]
        self.assertEqual(request.form, {"subject": "제목", "content": "본문"})
        self.assertIn("/v1/cafe/1234/menu/5/articles", request.url)
        response = {"message": {"result": {"articleId": 9, "articleUrl": "https://cafe.naver.com/example/9"}}}
        result = ADAPTERS["naver_cafe"].publish(PublishRequest("본문", title="제목"), ENV, FakeTransport([response]))
        self.assertEqual(result["post_id"], "9")

    def test_facebook_page_routes_media_to_official_edges(self) -> None:
        text = ADAPTERS["facebook_page"].preview(PublishRequest("hello"), ENV)[0]
        image = ADAPTERS["facebook_page"].preview(PublishRequest("caption", "https://example.test/a.jpg", "IMAGE"), ENV)[0]
        video = ADAPTERS["facebook_page"].preview(PublishRequest("caption", "https://example.test/a.mp4", "VIDEO"), ENV)[0]
        self.assertTrue(text.url.endswith("/feed"))
        self.assertTrue(image.url.endswith("/photos"))
        self.assertTrue(video.url.endswith("/videos"))

    def test_linkedin_supports_text_and_preuploaded_media_urn(self) -> None:
        text = ADAPTERS["linkedin"].preview(PublishRequest("hello"), ENV)[0]
        image = ADAPTERS["linkedin"].preview(PublishRequest("hello", media_type="IMAGE", media_id="urn:li:image:123"), ENV)[0]
        self.assertNotIn("content", text.body)
        self.assertEqual(image.body["content"]["media"]["id"], "urn:li:image:123")
        result = ADAPTERS["linkedin"].publish(PublishRequest("hello"), ENV, FakeTransport([{"_response_id": "urn:li:share:1"}]))
        self.assertEqual(result["post_id"], "urn:li:share:1")

    def test_discord_redacts_webhook_and_disables_mentions(self) -> None:
        preview = ADAPTERS["discord"].preview(PublishRequest("hello"), ENV)[0]
        self.assertIn("<redacted>", preview.url)
        self.assertNotIn("discord-secret", str(preview.safe_dict()))
        self.assertEqual(preview.body["allowed_mentions"], {"parse": []})
        transport = FakeTransport([{"id": "message-1"}])
        result = ADAPTERS["discord"].publish(PublishRequest("hello"), ENV, transport)
        self.assertEqual(result["post_id"], "message-1")

    def test_reddit_supports_text_and_link_but_holds_media_upload(self) -> None:
        text = ADAPTERS["reddit"].preview(PublishRequest("body", title="title"), ENV)[0]
        link = ADAPTERS["reddit"].preview(PublishRequest("body", "https://example.test", "LINK", "title"), ENV)[0]
        self.assertEqual(text.form["kind"], "self")
        self.assertEqual(link.form["kind"], "link")
        with self.assertRaisesRegex(PublishError, "media workflow"):
            ADAPTERS["reddit"].preview(PublishRequest("body", "https://example.test/a.jpg", "IMAGE", "title"), ENV)

    def test_youtube_blocks_unverified_community_post_and_incomplete_upload(self) -> None:
        with self.assertRaisesRegex(UnsupportedAutomationError, "Community"):
            ADAPTERS["youtube"].preview(PublishRequest("hello"), ENV)
        with self.assertRaisesRegex(UnsupportedAutomationError, "resumable"):
            ADAPTERS["youtube"].preview(PublishRequest("caption", media_type="VIDEO"), ENV)

    def test_cli_requires_confirm_for_execution(self) -> None:
        output = io.StringIO()
        with mock.patch.dict("os.environ", ENV, clear=True), redirect_stdout(output):
            code = cli.main(["x", "--text", "hello", "--execute"])
        self.assertEqual(code, 2)
        self.assertIn("--confirm", output.getvalue())


if __name__ == "__main__":
    unittest.main()
