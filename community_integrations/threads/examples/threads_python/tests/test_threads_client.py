"""Verify the offline Threads request contract without making network calls."""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from threads_client import (  # noqa: E402
    build_container_request,
    build_publish_request,
    build_status_request,
    container_decision,
)


class RequestContractTests(unittest.TestCase):
    """Cover each supported publishing request shape."""

    def test_text_container(self) -> None:
        request = build_container_request("user-1", "TEXT", text="hello")
        self.assertEqual(request.params, {"media_type": "TEXT", "text": "hello"})

    def test_image_container(self) -> None:
        request = build_container_request("user-1", "IMAGE", image_url="https://example.test/a.jpg")
        self.assertEqual(request.params["image_url"], "https://example.test/a.jpg")

    def test_video_container(self) -> None:
        request = build_container_request("user-1", "VIDEO", video_url="https://example.test/a.mp4")
        self.assertEqual(request.params["media_type"], "VIDEO")

    def test_carousel_children_are_encoded(self) -> None:
        request = build_container_request("user-1", "CAROUSEL", children=["one", "two"])
        self.assertEqual(request.params["children"], "one,two")

    def test_audio_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "no verified standalone AUDIO"):
            build_container_request("user-1", "AUDIO", audio_url="https://example.test/a.mp3")

    def test_required_fields_are_rejected_offline(self) -> None:
        invalid = (("TEXT", {}), ("IMAGE", {}), ("VIDEO", {}), ("CAROUSEL", {"children": ["one"]}))
        for media_type, fields in invalid:
            with self.subTest(media_type=media_type), self.assertRaises(ValueError):
                build_container_request("user-1", media_type, **fields)

    def test_carousel_rejects_more_than_twenty_children(self) -> None:
        with self.assertRaisesRegex(ValueError, "2 to 20"):
            build_container_request("user-1", "CAROUSEL", children=[str(i) for i in range(21)])

    def test_status_and_publish_paths(self) -> None:
        self.assertTrue(build_status_request("container-1").url.endswith("/container-1"))
        self.assertTrue(build_publish_request("user-1", "container-1").url.endswith("/user-1/threads_publish"))

    def test_container_decisions(self) -> None:
        expected = {
            "IN_PROGRESS": "WAIT",
            "FINISHED": "PUBLISH",
            "PUBLISHED": "DONE",
            "ERROR": "STOP",
            "EXPIRED": "STOP",
            "NEW_VALUE": "HOLD",
        }
        self.assertEqual({status: container_decision(status) for status in expected}, expected)


if __name__ == "__main__":
    unittest.main()
