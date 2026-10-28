"""Protect the public integration contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from community_integrations.publisher import ADAPTERS
from doctor import REQUIREMENTS
from integration_contract import SCHEMA_VERSION, build_contract, contract_text
ROOT = Path(__file__).parents[1]


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

if __name__ == "__main__":
    unittest.main()
