from __future__ import annotations

import re
from collections import Counter

from app.core import TextFeatures


class TextAnalyzer:
    SECTION_PATTERN = re.compile(r"\[(intro|verse|pre[- ]?chorus|chorus|hook|bridge|outro|final chorus)[^\]]*\]", re.I)
    AI_TOOLS = ("suno", "udio", "ai", "aiva", "boomy")

    def analyze(self, lyrics: str = "", prompt: str = "") -> TextFeatures:
        combined = "\n".join(part for part in (prompt, lyrics) if part)
        lines = [line.strip() for line in lyrics.splitlines() if line.strip()]
        normalized = [line.lower() for line in lines]
        repeated = sum(count - 1 for count in Counter(normalized).values() if count > 1)
        section_names = [match.group(1).title() for match in self.SECTION_PATTERN.finditer(combined)]
        warnings = []
        if re.search(r"\[(ad-lib|humming)\]", lyrics, re.I):
            warnings.append("Lyrics contain label-only ad-lib/humming tags.")
        return TextFeatures(
            has_lyrics=bool(lyrics.strip()),
            has_prompt=bool(prompt.strip()),
            section_names=section_names,
            lyric_line_count=len(lines),
            repeated_line_count=repeated,
            hook_candidates=self._hook_candidates(lines),
            ai_tool_mentions=[tool for tool in self.AI_TOOLS if re.search(rf"\b{re.escape(tool)}\b", combined, re.I)],
            warnings=warnings,
        )

    @staticmethod
    def _hook_candidates(lines: list[str]) -> list[str]:
        candidates = []
        for line in lines:
            clean = re.sub(r"\[[^\]]+\]", "", line).strip()
            if 3 <= len(clean) <= 40:
                candidates.append(clean)
            if len(candidates) == 3:
                break
        return candidates
