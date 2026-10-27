"""Verify the local web composer without contacting community providers."""

from __future__ import annotations

import unittest
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen

from web_app import CommunityWebHandler, MAX_REQUEST_BYTES, PLATFORM_LABELS, build_content, preview_payload, public_catalog, publish_payload
from community_integrations.publisher import ADAPTERS, PublishError


class FakeTransport:
    """Record outbound requests and return a deterministic provider result."""

    def __init__(self) -> None:
        self.requests = []

    def send(self, request, *, timeout=30.0):
        """Capture one request instead of opening the network."""
        self.requests.append(request)
        return {"data": {"id": "post-123"}}


class WebComposerTests(unittest.TestCase):
    """Protect UI catalog, dry-run redaction, and live-confirmation boundaries."""

    def test_catalog_covers_all_adapters_without_secret_values(self) -> None:
        catalog = public_catalog({"X_USER_ACCESS_TOKEN": "secret-value"})
        self.assertEqual(set(ADAPTERS), {item["id"] for item in catalog["platforms"]})
        self.assertEqual(set(ADAPTERS), set(PLATFORM_LABELS))
        self.assertNotIn("secret-value", str(catalog))

    def test_preview_redacts_token_and_does_not_send(self) -> None:
        result = preview_payload({"platform": "x", "text": "hello", "media_type": "TEXT"}, {"X_USER_ACCESS_TOKEN": "secret-value"})
        self.assertEqual("DRY_RUN", result["mode"])
        self.assertNotIn("secret-value", str(result))
        self.assertIn("<redacted>", str(result))

    def test_local_file_is_explicitly_held(self) -> None:
        with self.assertRaisesRegex(PublishError, "로컬 파일"):
            build_content({"text": "hello", "local_file_name": "song.mp3"})

    def test_publish_requires_checkbox_and_platform_name(self) -> None:
        env = {"X_USER_ACCESS_TOKEN": "token"}
        with self.assertRaisesRegex(PublishError, "확인"):
            publish_payload({"platform": "x", "text": "hello", "confirmed": True, "confirmation_text": "threads"}, env, FakeTransport())

    def test_confirmed_publish_uses_injected_transport(self) -> None:
        transport = FakeTransport()
        result = publish_payload({"platform": "x", "text": "hello", "confirmed": True, "confirmation_text": "x"}, {"X_USER_ACCESS_TOKEN": "token"}, transport)
        self.assertEqual("post-123", result["result"]["post_id"])
        self.assertEqual(1, len(transport.requests))

    def test_request_limit_is_small_enough_for_text_only_api(self) -> None:
        self.assertEqual(64 * 1024, MAX_REQUEST_BYTES)

    def test_javascript_is_served_with_an_executable_content_type(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), CommunityWebHandler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/app.js") as response:
                self.assertEqual("text/javascript", response.headers.get_content_type())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    unittest.main()
