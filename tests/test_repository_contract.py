"""Protect the root project registry and each project's security boundary."""

from __future__ import annotations

import json
import re
import subprocess
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
    "marketing_command_center",
    "community_integrations",
}
PRIVATE_LOCAL_PROJECTS: set[str] = set()


class RepositoryContractTests(unittest.TestCase):
    """Keep the documented project count and API boundary synchronized."""

    @staticmethod
    def _discover_project_directories() -> set[str]:
        """Find runnable top-level projects without trusting the README registry."""
        discovered: set[str] = set()
        for directory in ROOT.iterdir():
            if not directory.is_dir() or directory.name in PRIVATE_LOCAL_PROJECTS or not (directory / "README.md").is_file():
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
        self.assertIn("8개 독립 프로젝트", readme)
        self.assertIn("결정론적 로컬 분석기", readme)
        self.assertNotIn("내장 mock 결과", readme)

    def test_readme_links_the_repository_mit_license(self) -> None:
        """Keep the public license notice and its target file synchronized."""
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn("[MIT License](LICENSE)", readme)
        self.assertTrue(license_text.startswith("MIT License\n"))
        self.assertIn("Copyright (c) 2026 ImDaeseong", license_text)

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
                self.assertIn("marketing_command_center", content)
                self.assertIn("community_integrations", content)

    def test_spec_lists_every_community_contract_platform(self) -> None:
        """Keep the root product scope aligned with the generated integration contract."""
        spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
        contract = json.loads(
            (ROOT / "community_integrations" / "integration-contract.json").read_text(encoding="utf-8")
        )

        for platform in contract["platforms"]:
            with self.subTest(platform=platform["id"]):
                self.assertIn(platform["label"], spec)

    def test_security_boundary_distinguishes_local_and_external_paths(self) -> None:
        security = (ROOT / "SECURITY_BOUNDARY.md").read_text(encoding="utf-8")
        self.assertIn("음악·영상 도구 5개는 외부 API 키 없이 동작", security)
        self.assertIn("CareerDiff", security)
        self.assertIn("OPENAI_API_KEY", security)
        self.assertIn("ai_agent/keyinfo/keys.env", security)
        self.assertIn("사람 검토", security)

    def test_private_projects_stay_untracked_and_undocumented(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        docs = ("README.md", "SPEC.md", "ARCHITECTURE.md", "DESIGN.md", "SECURITY_BOUNDARY.md", "HOLD_CONDITIONS.md", "CLAUDE.md", "VERIFICATION.md", "ELI5.html")
        for project in sorted(PRIVATE_LOCAL_PROJECTS):
            with self.subTest(project=project):
                self.assertIn(f"{project}/", gitignore.splitlines())
                for name in docs:
                    self.assertNotIn(project, (ROOT / name).read_text(encoding="utf-8"), name)
                if (ROOT / ".git").is_dir():
                    tracked = subprocess.run(["git", "ls-files", project], cwd=ROOT, capture_output=True, text=True, check=False)
                    self.assertEqual(tracked.stdout.strip(), "", "private project files must not be tracked")

    def test_careerdiff_launcher_preserves_local_data_outside_build_trace(self) -> None:
        launcher = (ROOT / "CareerDiff" / "run-careerdiff.cmd").read_text(encoding="utf-8")
        store = (
            ROOT
            / "CareerDiff"
            / "app"
            / "src"
            / "core"
            / "validation"
            / "validationCaseFileStore.ts"
        ).read_text(encoding="utf-8")
        self.assertIn("CAREERDIFF_DATA_DIR=%~dp0data", launcher)
        self.assertIn('path.resolve(/* turbopackIgnore: true */ process.cwd(), "data")', store)
        self.assertNotIn('process.cwd(), "..", "data"', store)
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("CareerDiff/data/**/*.json", gitignore)
        self.assertIn("CareerDiff/app/data/**/*.json", gitignore)
        readme = (ROOT / "CareerDiff" / "README.md").read_text(encoding="utf-8")
        self.assertIn("CAREERDIFF_DATA_DIR", readme)
        self.assertIn("CareerDiff/app/data/", readme)


if __name__ == "__main__":
    unittest.main()
