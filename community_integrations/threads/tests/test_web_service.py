"""Verify the web publishing flow without contacting Threads."""

from __future__ import annotations

import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from examples.threads_python.threads_client import ThreadsApiError, ThreadsClient, build_profile_request, build_status_request
from serve import ACCOUNT, account_status
from web_service import prepare_web_plan, prepare_web_request, publish_web_request


class FakeClient:
    """Return a deterministic sequence of provider responses."""

    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []

    def execute(self, request):
        """Record one request and return the next fixture."""
        self.requests.append(request)
        return next(self.responses)


class WebRequestTests(unittest.TestCase):
    """Cover browser payload validation and publication state handling."""

    def test_text_preview_contains_no_token(self) -> None:
        request = prepare_web_request("user-1", {"kind": "TEXT", "text": "hello"})
        self.assertEqual(request.params["text"], "hello")
        self.assertNotIn("access_token", request.params)

    def test_image_requires_https(self) -> None:
        with self.assertRaisesRegex(ValueError, "https"):
            prepare_web_request("user-1", {"kind": "IMAGE", "url": "http://example.com/a.jpg"})

    def test_unsupported_kind_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "지원하지 않는"):
            prepare_web_request("user-1", {"kind": "AUDIO", "url": "https://example.test/a.mp3"})

    def test_finished_container_is_published(self) -> None:
        client = FakeClient([{"id": "container-1"}, {"status": "FINISHED"}, {"id": "post-1"}])
        result = publish_web_request(client, "user-1", {"kind": "TEXT", "text": "hello"}, wait=lambda _: None)
        self.assertEqual(result["post_id"], "post-1")
        self.assertEqual(len(client.requests), 3)

    def test_processing_error_stops_without_publish(self) -> None:
        client = FakeClient([{"id": "container-1"}, {"status": "ERROR", "error_message": "bad media"}])
        with self.assertRaisesRegex(RuntimeError, "bad media"):
            publish_web_request(client, "user-1", {"kind": "TEXT", "text": "hello"}, wait=lambda _: None)
        self.assertEqual(len(client.requests), 2)

    def test_provider_error_does_not_retain_token_url(self) -> None:
        body = BytesIO(b'{"error":{"message":"expired","code":190,"fbtrace_id":"trace-1"}}')
        provider_error = HTTPError("https://graph.threads.net/id?access_token=secret-token", 401, "bad", {}, body)
        with patch("examples.threads_python.threads_client.urlopen", side_effect=provider_error):
            with self.assertRaises(ThreadsApiError) as caught:
                ThreadsClient("secret-token").execute(build_status_request("container-1"))
        self.assertNotIn("secret-token", str(caught.exception))
        self.assertEqual(caught.exception.trace_id, "trace-1")

    def test_profile_request_uses_me_without_token(self) -> None:
        request = build_profile_request()
        self.assertTrue(request.url.endswith("/me"))
        self.assertNotIn("access_token", request.params)

    def test_account_status_exposes_flags_not_secrets(self) -> None:
        ACCOUNT.clear()

    def test_multiple_media_builds_carousel_children(self) -> None:
        plan = prepare_web_plan("user-1", {"text": "mixed", "attachments": [
            {"kind": "IMAGE", "url": "https://example.test/a.jpg"},
            {"kind": "VIDEO", "url": "https://example.test/b.mp4"},
        ]})
        self.assertEqual(len(plan), 2)
        self.assertEqual([item.params["media_type"] for item in plan], ["IMAGE", "VIDEO"])
        self.assertTrue(all(item.params["is_carousel_item"] == "true" for item in plan))
        ACCOUNT.update(id="user-1", username="tester")
        status = account_status({"THREADS_APP_SECRET": "PRIVATE_VALUE_123", "THREADS_ACCESS_TOKEN": "TOKEN_VALUE_456"})
        self.assertTrue(status["connected"])
        self.assertEqual(status["configuration"]["app_secret"], True)
        self.assertNotIn("PRIVATE_VALUE_123", str(status))
        self.assertNotIn("TOKEN_VALUE_456", str(status))
        ACCOUNT.clear()


if __name__ == "__main__":
    unittest.main()
