"""Guard the five local AI/media projects against stale provider claims."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_PROJECTS = (
    "ai_anime",
    "ai_img_video_aiBoygirl",
    "ai_img_video_prompt_capcut",
    "youtube_research",
    "music_insight_studio",
)
EXTERNAL_AI_SDKS = {"openai", "anthropic", "google.generativeai"}
LIVE_API_ALLOWLIST = {Path("ai_anime/live_api_smoke.py")}


class AiApiContractTests(unittest.TestCase):
    """Keep model metadata, local-only boundaries, and reviewed versions aligned."""

    def test_local_projects_do_not_import_external_ai_sdks(self) -> None:
        found: list[str] = []
        for project in LOCAL_PROJECTS:
            for path in (ROOT / project).rglob("*.py"):
                if ".venv" in path.parts:
                    continue
                if path.relative_to(ROOT) in LIVE_API_ALLOWLIST:
                    continue
                tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        names = [node.module]
                    else:
                        continue
                    for name in names:
                        if any(name == sdk or name.startswith(f"{sdk}.") for sdk in EXTERNAL_AI_SDKS):
                            found.append(f"{path.relative_to(ROOT)}:{name}")
        self.assertEqual(found, [])

    def test_live_api_path_is_explicit_and_cost_guarded(self) -> None:
        source = (ROOT / "ai_anime" / "live_api_smoke.py").read_text(encoding="utf-8")
        self.assertIn("--confirm-paid-call", source)
        self.assertIn('os.getenv("OPENAI_API_KEY"', source)
        self.assertIn('"n": 1', source)
        self.assertIn('"quality": "low"', source)
        self.assertIn('"image_saved": False', source)

        live_paths = {
            path.relative_to(ROOT)
            for project in LOCAL_PROJECTS
            for path in (ROOT / project).rglob("*.py")
            if ".venv" not in path.parts
            and "api.openai.com" in path.read_text(encoding="utf-8-sig")
        }
        self.assertEqual(live_paths, LIVE_API_ALLOWLIST)

    def test_ai_anime_uses_reviewed_image_model_identifiers(self) -> None:
        source = (ROOT / "ai_anime" / "main.py").read_text(encoding="utf-8")
        self.assertIn('"gpt-image-2.5-sunburst"', source)
        self.assertIn('"gemini-3.1-flash-image"', source)
        self.assertNotIn("Imagen 3", source)
        stale = [
            str(path.relative_to(ROOT))
            for path in (ROOT / "ai_anime").rglob("*.md")
            if "Imagen 3" in path.read_text(encoding="utf-8-sig")
        ]
        self.assertEqual(stale, [])

    def test_ytdlp_and_audio_dependency_floors_are_reviewed(self) -> None:
        collector = (ROOT / "youtube_research" / "collect.py").read_text(encoding="utf-8")
        youtube_requirements = (ROOT / "youtube_research" / "requirements.txt").read_text(encoding="utf-8")
        audio_requirements = (ROOT / "music_insight_studio" / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("MIN_YTDLP_VERSION = (2026, 2, 21)", collector)
        self.assertIn("yt-dlp>=2026.8.19,<2027", youtube_requirements)
        self.assertIn("numpy>=2.5.3,<3", audio_requirements)
        self.assertIn("soundfile>=0.14.0,<0.15", audio_requirements)
        self.assertIn("pyloudnorm>=0.2.0,<0.3", audio_requirements)

    def test_prompt_and_editor_projects_keep_file_contract_boundary(self) -> None:
        boygirl = (ROOT / "ai_img_video_aiBoygirl" / "main.py").read_text(encoding="utf-8")
        capcut = (ROOT / "ai_img_video_prompt_capcut" / "main.py").read_text(encoding="utf-8")
        self.assertIn("Rights boundary: transformed concert-production attributes only", boygirl)
        self.assertIn('"schema_version": "1.2"', capcut)


if __name__ == "__main__":
    unittest.main()
