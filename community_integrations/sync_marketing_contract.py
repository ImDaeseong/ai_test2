"""Synchronize the canonical community contract into Marketing Command Center."""

from __future__ import annotations

import argparse
from pathlib import Path

from integration_contract import contract_text


ROOT = Path(__file__).parent
CANONICAL = ROOT / "integration-contract.json"
DEFAULT_CONSUMER = ROOT.parent / "marketing_command_center" / "assets" / "community-integrations.json"


def sync(consumer: Path) -> None:
    """Write identical canonical and consumer copies of the public contract."""
    text = contract_text()
    CANONICAL.write_text(text, encoding="utf-8")
    consumer.parent.mkdir(parents=True, exist_ok=True)
    consumer.write_text(text, encoding="utf-8")


def verify(consumer: Path, canonical: Path = CANONICAL) -> None:
    """Reject stale canonical or consumer contracts with an attributable diagnostic."""
    expected = contract_text()
    if not canonical.is_file() or canonical.read_text(encoding="utf-8") != expected:
        raise ValueError("CANONICAL_CONTRACT_DRIFT")
    if not consumer.is_file() or consumer.read_text(encoding="utf-8") != expected:
        raise ValueError("CONSUMER_CONTRACT_DRIFT")


def main() -> None:
    """Synchronize the default sibling consumer or a test destination."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--consumer", type=Path, default=DEFAULT_CONSUMER)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    consumer = args.consumer.resolve()
    if args.check:
        verify(consumer)
        print("PASS: community integration contract synchronized")
    else:
        sync(consumer)


if __name__ == "__main__":
    main()
