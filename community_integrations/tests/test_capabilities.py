"""Keep the media matrix synchronized with the executable adapter registry."""

from __future__ import annotations

import unittest
from pathlib import Path

from capabilities import CAPABILITIES, render_markdown
from community_integrations.publisher import ADAPTERS


ROOT = Path(__file__).resolve().parents[1]


class CapabilityMatrixTests(unittest.TestCase):
    """Verify platform coverage and explicit media boundaries."""

    def test_every_capability_platform_has_an_adapter_boundary(self) -> None:
        self.assertEqual(set(CAPABILITIES), set(ADAPTERS))

    def test_every_platform_classifies_each_media_family(self) -> None:
        required = {"text", "image", "video", "audio", "file", "local"}
        for platform, row in CAPABILITIES.items():
            self.assertEqual(required, set(row), platform)
            self.assertTrue(all(row.values()), platform)

    def test_markdown_contains_every_platform(self) -> None:
        rendered = render_markdown()
        for platform in CAPABILITIES:
            self.assertIn(f"| {platform} |", rendered)

    def test_naver_research_summary_matches_supported_cafe_boundary(self) -> None:
        """Prevent the superseded share-only conclusion from returning to the report."""
        report = (ROOT / "reports" / "커뮤니티 자동 게시 통합.md").read_text(encoding="utf-8")

        self.assertIn("Naver Cafe는 OAuth 기반 공식 글쓰기 API", report)
        self.assertIn("Cafe 텍스트·링크 게시", report)
        self.assertNotIn("Blog/Cafe/Band 무인 글쓰기 엔드포인트를 확인하지 못했", report)


if __name__ == "__main__":
    unittest.main()
