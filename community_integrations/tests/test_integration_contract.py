"""Protect the public integration contract and its synchronized consumer copy."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from community_integrations.publisher import ADAPTERS
from doctor import REQUIREMENTS
from integration_contract import SCHEMA_VERSION, build_contract, contract_text
from sync_marketing_contract import verify


ROOT = Path(__file__).parents[1]
CONSUMER = ROOT.parent / "marketing_command_center" / "assets" / "community-integrations.json"


class IntegrationContractTests(unittest.TestCase):
    """Keep the canonical contract complete, secret-free, and synchronized."""

    def test_contract_covers_every_adapter_and_required_environment_name(self) -> None:
        contract = build_contract()
        rows = {row["id"]: row for row in contract["platforms"]}
        self.assertEqual(SCHEMA_VERSION, contract["schema_version"])
        self.assertEqual(set(ADAPTERS), set(rows))
        for platform, names in REQUIREMENTS.items():
            self.assertEqual(list(names), rows[platform]["required_env"])
            self.assertTrue(rows[platform]["validation"]["reject_placeholders"])

    def test_contract_contains_names_but_no_environment_values(self) -> None:
        text = contract_text()
        self.assertNotIn("secret-value", text)
        self.assertNotIn("access_token\": \"", text.lower())
        json.loads(text)

    def test_marketing_copy_is_exactly_synchronized(self) -> None:
        self.assertTrue(CONSUMER.is_file(), "run: python sync_marketing_contract.py")
        self.assertEqual(contract_text(), CONSUMER.read_text(encoding="utf-8"))

    def test_drift_guard_rejects_each_copy_for_the_intended_reason(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            canonical = Path(directory) / "integration-contract.json"
            consumer = Path(directory) / "community-integrations.json"
            canonical.write_text(contract_text(), encoding="utf-8")
            consumer.write_text(contract_text(), encoding="utf-8")

            canonical.write_text(contract_text().replace('"schema_version": 2', '"schema_version": 99'), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "^CANONICAL_CONTRACT_DRIFT$"):
                verify(consumer, canonical)

            canonical.write_text(contract_text(), encoding="utf-8")
            consumer.write_text(contract_text().replace('"schema_version": 2', '"schema_version": 99'), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "^CONSUMER_CONTRACT_DRIFT$"):
                verify(consumer, canonical)


if __name__ == "__main__":
    unittest.main()
