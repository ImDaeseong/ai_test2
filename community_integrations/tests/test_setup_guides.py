"""Verify generated setup guides are complete, linked, and secret-free."""

from __future__ import annotations

from html.parser import HTMLParser
import unittest
from pathlib import Path

from doctor import REQUIREMENTS
from generate_setup_guides import PLATFORMS


ROOT = Path(__file__).parents[1] / "docs" / "community-setup"


class LinkParser(HTMLParser):
    """Collect links while proving the document parses."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a" and (href := dict(attrs).get("href")):
            self.links.append(href)


class SetupGuideTests(unittest.TestCase):
    """Protect platform coverage and environment setup contracts."""

    def test_every_platform_has_one_guide(self) -> None:
        self.assertEqual(set(REQUIREMENTS), {item[0] for item in PLATFORMS})
        self.assertEqual(set(REQUIREMENTS), {p.stem for p in ROOT.glob("*.html")} - {"index"})

    def test_guides_separate_site_environment_and_tests(self) -> None:
        for item in PLATFORMS:
            text = (ROOT / f"{item[0]}.html").read_text(encoding="utf-8")
            self.assertIn("커뮤니티 사이트에서 설정할 부분", text)
            self.assertIn("사이트에서 가져올 값과 환경 설정", text)
            self.assertIn(f"doctor.py --platform {item[0]}", text)
            for key in REQUIREMENTS[item[0]]:
                self.assertIn(key, text)

    def test_local_links_resolve_and_no_sample_secret_is_embedded(self) -> None:
        for path in ROOT.glob("*.html"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("secret-value", text)
            parser = LinkParser()
            parser.feed(text)
            for link in parser.links:
                if "://" not in link:
                    self.assertTrue((ROOT / link).exists(), f"{path.name}: {link}")


if __name__ == "__main__":
    unittest.main()
