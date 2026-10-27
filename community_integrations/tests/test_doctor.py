"""Verify the configuration doctor reports presence without leaking values."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

import doctor


class DoctorTests(unittest.TestCase):
    """Cover ready, missing, and secret-redaction behavior."""

    def test_missing_platform_configuration_returns_hold(self) -> None:
        output = io.StringIO()
        with mock.patch.dict("os.environ", {}, clear=True), redirect_stdout(output):
            code = doctor.main(["--platform", "telegram"])
        self.assertEqual(code, 2)
        self.assertIn("TELEGRAM_BOT_TOKEN", output.getvalue())

    def test_ready_platform_never_prints_secret_value(self) -> None:
        output = io.StringIO()
        env = {"TELEGRAM_BOT_TOKEN": "123456:never_print_this_valid_token", "TELEGRAM_CHAT_ID": "@test_chat"}
        with mock.patch.dict("os.environ", env, clear=True), redirect_stdout(output):
            code = doctor.main(["--platform", "telegram"])
        self.assertEqual(code, 0)
        self.assertIn('"local_config": "READY"', output.getvalue())
        self.assertNotIn("never_print_this_valid_token", output.getvalue())

    def test_placeholder_and_malformed_values_are_named_but_never_printed(self) -> None:
        env = {"DISCORD_WEBHOOK_URL": "your_discord_webhook"}
        report = doctor.inspect_environment(env)["discord"]
        self.assertEqual("INVALID", report["local_config"])
        self.assertEqual(["DISCORD_WEBHOOK_URL"], report["invalid"])
        self.assertNotIn(env["DISCORD_WEBHOOK_URL"], str(report))

    def test_structured_values_accept_known_safe_shapes(self) -> None:
        env = {
            "LINKEDIN_ACCESS_TOKEN": "opaque-token",
            "LINKEDIN_AUTHOR_URN": "urn:li:organization:12345",
        }
        self.assertEqual("READY", doctor.inspect_environment(env)["linkedin"]["local_config"])

    def test_naver_is_locally_ready_but_live_unverified(self) -> None:
        report = doctor.inspect_environment({})["naver"]
        self.assertEqual(report["local_config"], "READY")
        self.assertFalse(report["live_verified"])
        self.assertIn("Blog 글쓰기 API 종료", str(report["limitation"]))


if __name__ == "__main__":
    unittest.main()
