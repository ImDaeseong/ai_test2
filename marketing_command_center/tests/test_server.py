import json
import socket
import unittest
from urllib.error import HTTPError, URLError

from serve import LocalThreadingHTTPServer, generate_marketing_draft, review_marketing_post


class FakeResponse:
    """Provide a context-managed byte response for network-bound unit tests."""

    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def openai_body(text: str) -> bytes:
    """Build a minimal Responses API body carrying one output text."""
    return json.dumps({
        "model": "gpt-6-luna",
        "output": [{"content": [{"type": "output_text", "text": text}]}],
        "usage": {"input_tokens": 12, "output_tokens": 4, "total_tokens": 16},
        "secret": "ignored",
    }).encode("utf-8")


DRAFT = {"service": "Hermes", "description": "광고 성과를 한 화면에 모으는 도구", "channel": "Threads", "topic": "엑셀 정리 시간 줄이기"}
REVIEW = {"service": "Hermes", "description": "광고 성과를 한 화면에 모으는 도구", "channel": "Threads", "text": "매주 엑셀로 성과를 옮기시나요? 직접 써 보고 의견 주세요."}
GOOD_REVIEW = {"score": 7, "hook": "질문으로 시작해 좋습니다.", "persuasion": "이득이 더 구체적이면 좋습니다.", "risks": ["수치 근거 없음"], "rewrite": "개선안 문장"}


class OpenAIDraftTests(unittest.TestCase):
    """Verify the paid-call boundary without placing credentials in responses."""

    def test_missing_key_skips_network(self):
        result = generate_marketing_draft(DRAFT, None, lambda *_args, **_kwargs: self.fail("network called"))
        self.assertEqual(result, {"status": "not_configured"})

    def test_response_is_allowlisted_and_request_is_private(self):
        captured = {}

        def opener(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return FakeResponse(openai_body("짧은 초안"))

        result = generate_marketing_draft(DRAFT, "local-secret", opener)
        self.assertEqual(result["status"], "generated")
        self.assertEqual(result["text"], "짧은 초안")
        self.assertNotIn("secret", result)
        self.assertFalse(captured["body"]["store"])
        self.assertEqual(captured["body"]["max_output_tokens"], 400)
        self.assertIn("Hermes", captured["body"]["input"])
        self.assertIn("광고 성과를 한 화면에", captured["body"]["input"])
        self.assertIn("주요 독자", captured["body"]["input"])
        self.assertEqual(captured["timeout"], 20)

    def test_invalid_input_never_reaches_the_network(self):
        for payload in ({}, {"service": ""}, {**DRAFT, "description": "가" * 501}):
            result = generate_marketing_draft(payload, "k", lambda *_a, **_k: self.fail("network called"))
            self.assertEqual(result, {"status": "error", "kind": "invalid_input"})

    def test_empty_response_preserves_only_cost_diagnostics(self):
        body = b'{"model":"gpt-6-luna","output":[],"usage":{"input_tokens":67,"output_tokens":400},"incomplete_details":{"reason":"max_output_tokens"},"private":"x"}'
        result = generate_marketing_draft(DRAFT, "k", lambda *_a, **_k: FakeResponse(body))
        self.assertEqual(result["kind"], "empty_response")
        self.assertEqual(result["incomplete_reason"], "max_output_tokens")
        self.assertNotIn("private", repr(result))

    def test_content_brief_reaches_the_model_prompt(self):
        captured = {}
        payload = {**DRAFT, "audience": "혼자 일하는 마케터", "benefit": "정리 시간 줄이기", "proof": "직접 입력한 데이터만 사용", "cta": "데모 요청"}

        def opener(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse(openai_body("초안"))

        self.assertEqual(generate_marketing_draft(payload, "k", opener)["status"], "generated")
        for value in ("혼자 일하는 마케터", "정리 시간 줄이기", "직접 입력한 데이터만 사용", "데모 요청"):
            self.assertIn(value, captured["body"]["input"])


class OpenAIReviewTests(unittest.TestCase):
    """Verify the review reply is parsed strictly and only the allowlisted fields survive."""

    def review(self, text: str):
        return review_marketing_post(REVIEW, "local-secret", lambda *_a, **_k: FakeResponse(openai_body(text)))

    def test_missing_key_or_empty_post_skips_network(self):
        fail = lambda *_a, **_k: self.fail("network called")
        self.assertEqual(review_marketing_post(REVIEW, None, fail), {"status": "not_configured"})
        self.assertEqual(review_marketing_post({**REVIEW, "text": "  "}, "k", fail), {"status": "error", "kind": "invalid_input"})

    def test_valid_json_is_normalised(self):
        result = self.review(json.dumps({**GOOD_REVIEW, "extra": "drop"}, ensure_ascii=False))
        self.assertEqual(result["status"], "reviewed")
        self.assertEqual(result["review"], GOOD_REVIEW)
        self.assertEqual(result["usage"]["total_tokens"], 16)

    def test_json_wrapped_in_prose_or_code_fence_is_still_read(self):
        wrapped = "결과입니다\n```json\n" + json.dumps(GOOD_REVIEW, ensure_ascii=False) + "\n```"
        self.assertEqual(self.review(wrapped)["review"]["score"], 7)

    def test_score_is_clamped_and_risks_are_capped(self):
        result = self.review(json.dumps({**GOOD_REVIEW, "score": 99, "risks": [f"r{i}" for i in range(9)]}))
        self.assertEqual(result["review"]["score"], 10)
        self.assertEqual(len(result["review"]["risks"]), 5)

    def test_unusable_replies_are_classified_not_trusted(self):
        for text in ("not json at all", json.dumps({"score": "high"}), json.dumps({**GOOD_REVIEW, "rewrite": 5}), "[1, 2]"):
            self.assertEqual(self.review(text), {"status": "error", "kind": "response"})


class OpenAIFailureKindTests(unittest.TestCase):
    """Verify each failure is tagged with a distinct, actionable kind for both paid calls."""

    def kinds(self, error):
        def fail(*_args, **_kwargs):
            raise error

        with self.assertLogs("marketing_command_center", level="WARNING"):
            draft = generate_marketing_draft(DRAFT, "sk-secret", fail)
        with self.assertLogs("marketing_command_center", level="WARNING"):
            review = review_marketing_post(REVIEW, "sk-secret", fail)
        self.assertNotIn("sk-secret", repr((draft, review)))
        return draft["kind"], review["kind"]

    def test_timeout_is_distinct_from_network_failure(self):
        self.assertEqual(self.kinds(TimeoutError()), ("timeout", "timeout"))
        self.assertEqual(self.kinds(URLError(socket.timeout())), ("timeout", "timeout"))
        self.assertEqual(self.kinds(URLError(ConnectionRefusedError())), ("network", "network"))

    def test_http_status_kinds(self):
        for code, kind in ((401, "auth"), (429, "rate_limit"), (503, "provider"), (400, "request")):
            self.assertEqual(self.kinds(HTTPError("url", code, "x", {}, None)), (kind, kind))


class LifecycleConfigurationTests(unittest.TestCase):
    """Verify one local process owns the port."""

    def test_server_disables_address_reuse(self):
        self.assertFalse(LocalThreadingHTTPServer.allow_reuse_address)


if __name__ == "__main__":
    unittest.main()
