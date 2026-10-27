"""Protect the aggregate verifier's scope and failure propagation."""

from __future__ import annotations

import subprocess
import unittest

import verify_offline


class OfflineVerifierTests(unittest.TestCase):
    """Ensure every declared gate runs explicitly and failures cannot be hidden."""

    def test_manifest_covers_runtime_security_and_browser_boundaries(self) -> None:
        names = [name for name, _, _ in verify_offline.verification_commands()]
        self.assertEqual(13, len(names))
        self.assertIn("contract", names)
        self.assertIn("marketing browser E2E", names)
        self.assertIn("marketing Windows launcher", names)
        self.assertIn("security hotspots", names)

    def test_first_failure_stops_and_propagates_its_exit_code(self) -> None:
        calls = []

        def fake_run(command, **kwargs):
            calls.append((command, kwargs))
            code = 7 if len(calls) == 2 else 0
            return subprocess.CompletedProcess(command, code)

        self.assertEqual(7, verify_offline.run_all(fake_run))
        self.assertEqual(2, len(calls))
        self.assertFalse(calls[0][1]["check"])


if __name__ == "__main__":
    unittest.main()
