"""Protect the root project registry and each project's security boundary."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROJECTS = {
    "ai_anime",
    "ai_img_video_aiBoygirl",
    "ai_img_video_prompt_capcut",
    "youtube_research",
    "music_insight_studio",
    "CareerDiff",
}


class RepositoryContractTests(unittest.TestCase):
    """Keep the documented project count and API boundary synchronized."""

    @staticmethod
    def _discover_project_directories() -> set[str]:
        """Find runnable top-level projects without trusting the README registry."""
        discovered: set[str] = set()
        for directory in ROOT.iterdir():
            if not directory.is_dir() or not (directory / "README.md").is_file():
                continue
            markers = (
                directory / "main.py",
                directory / "run.py",
                directory / "pyproject.toml",
                directory / "package.json",
                directory / "SPEC.md",
                directory / "app" / "package.json",
            )
            if any(marker.is_file() for marker in markers):
                discovered.add(directory.name)
        return discovered

    def test_readme_registry_matches_discovered_project_directories(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        registered = set(re.findall(r"^\| \[`([^`]+)`\]", readme, re.MULTILINE))
        discovered = self._discover_project_directories()
        self.assertEqual(discovered, EXPECTED_PROJECTS)
        self.assertEqual(registered, discovered)
        self.assertIn("6개 독립 프로젝트", readme)
        self.assertIn("결정론적 로컬 분석기", readme)
        self.assertNotIn("내장 mock 결과", readme)

    def test_governance_docs_register_careerdiff(self) -> None:
        for name in (
            "SPEC.md",
            "ARCHITECTURE.md",
            "SECURITY_BOUNDARY.md",
            "HOLD_CONDITIONS.md",
            "CLAUDE.md",
            "VERIFICATION.md",
        ):
            with self.subTest(document=name):
                content = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn("CareerDiff", content)

    def test_security_boundary_distinguishes_local_and_external_paths(self) -> None:
        security = (ROOT / "SECURITY_BOUNDARY.md").read_text(encoding="utf-8")
        self.assertIn("음악·영상 도구 5개는 외부 API 키 없이 동작", security)
        self.assertIn("CareerDiff", security)
        self.assertIn("OPENAI_API_KEY", security)
        self.assertIn("ai_agent/keyinfo/keys.env", security)
        self.assertIn("사람 검토", security)


if __name__ == "__main__":
    unittest.main()
