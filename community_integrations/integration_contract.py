"""Build the secret-free integration contract consumed by sibling applications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from capabilities import CAPABILITIES, PLATFORM_LABELS
from community_integrations.publisher import ADAPTERS
from doctor import REQUIREMENTS, VALUE_PATTERNS


SCHEMA_VERSION = 2
EXECUTION_HOLDS = {"youtube"}
MANUAL_PLATFORMS = {"naver"}


def build_contract() -> dict[str, Any]:
    """Return one versioned contract without reading or exposing credential values."""
    platform_ids = set(ADAPTERS)
    if platform_ids != set(CAPABILITIES) or platform_ids != set(REQUIREMENTS) or platform_ids != set(PLATFORM_LABELS):
        raise ValueError("platform registries are out of sync")
    platforms = []
    for platform in ADAPTERS:
        mode = "manual" if platform in MANUAL_PLATFORMS else "hold" if platform in EXECUTION_HOLDS else "api"
        platforms.append({
            "id": platform,
            "label": PLATFORM_LABELS[platform],
            "mode": mode,
            "required_env": list(REQUIREMENTS[platform]),
            "validation": {
                "reject_placeholders": True,
                "patterns": {name: VALUE_PATTERNS[name] for name in REQUIREMENTS[platform] if name in VALUE_PATTERNS},
            },
            "capabilities": CAPABILITIES[platform],
            "setup_guide": f"docs/community-setup/{platform}.html",
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "community_integrations",
        "platforms": platforms,
        "unsupported": [{"id": "naver_blog", "label": "Naver Blog", "reason": "official_write_api_retired"}],
    }


def contract_text() -> str:
    """Serialize the contract deterministically for exact-copy drift checks."""
    return json.dumps(build_contract(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_contract(path: Path) -> None:
    """Write the generated contract as UTF-8 JSON."""
    path.write_text(contract_text(), encoding="utf-8")
