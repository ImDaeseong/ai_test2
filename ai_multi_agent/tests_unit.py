"""
ai_multi_agent 단위 테스트
API 호출 없이 순수 함수만 검증한다.
실행: cd ai_multi_agent && python -m pytest tests_unit.py -v
"""
import os
import sys
from pathlib import Path

import pytest

# ai_multi_agent 디렉토리를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))


# ─────────────────────────────────────────
# agents/base.py — strip_code_fence, sanitize_text
# ─────────────────────────────────────────

from agents.base import strip_code_fence, sanitize_text


class TestStripCodeFence:
    def test_plain_text_unchanged(self):
        assert strip_code_fence('{"key": "value"}') == '{"key": "value"}'

    def test_removes_json_code_fence(self):
        text = '```json\n{"key": "value"}\n```'
        assert strip_code_fence(text) == '{"key": "value"}'

    def test_removes_generic_code_fence(self):
        text = '```\n{"key": "value"}\n```'
        assert strip_code_fence(text) == '{"key": "value"}'

    def test_strips_leading_trailing_whitespace(self):
        text = '  ```json\n{"a": 1}\n```  '
        assert strip_code_fence(text) == '{"a": 1}'

    def test_empty_string(self):
        assert strip_code_fence("") == ""

    def test_no_closing_fence_unchanged(self):
        text = "```json\n{no closing}"
        result = strip_code_fence(text)
        # 닫는 ``` 없으면 원본 반환
        assert "no closing" in result

    def test_multiline_json_preserved(self):
        text = '```json\n{\n  "title": "곡제목",\n  "genre": "발라드"\n}\n```'
        result = strip_code_fence(text)
        assert '"title"' in result
        assert '"genre"' in result


class TestSanitizeText:
    def test_normal_text_unchanged(self):
        assert sanitize_text("hello world") == "hello world"

    def test_korean_text_preserved(self):
        assert sanitize_text("안녕하세요") == "안녕하세요"

    def test_surrogate_chars_replaced(self):
        text = "hello\uD800world"  # 단독 서로게이트
        result = sanitize_text(text)
        assert "hello" in result
        assert "world" in result
        assert "\uD800" not in result

    def test_empty_string(self):
        assert sanitize_text("") == ""

    def test_mixed_korean_english(self):
        text = "Verse 1: 그리움이 밀려와"
        assert sanitize_text(text) == text


# ─────────────────────────────────────────
# main.py — song_slug, safe_read_json
# ─────────────────────────────────────────

from main import safe_read_json, song_slug


class TestSongSlug:
    def test_normal_title(self):
        assert song_slug("My Song") == "My Song"

    def test_removes_forbidden_chars(self):
        result = song_slug('title:with/forbidden<chars>')
        for ch in '<>:"/\\|?*':
            assert ch not in result

    def test_korean_title(self):
        assert song_slug("그리움의 노래") == "그리움의 노래"

    def test_strips_leading_trailing_dots(self):
        result = song_slug("...title...")
        assert not result.startswith(".")
        assert not result.endswith(".")

    def test_empty_slug_raises(self):
        with pytest.raises(ValueError):
            song_slug("...")  # 모두 점 → strip(".") 후 빈 슬러그

    def test_title_with_spaces(self):
        result = song_slug("Hello World 2024")
        assert result == "Hello World 2024"


class TestSafeReadJson:
    def test_missing_file_returns_empty_dict(self, tmp_path):
        result = safe_read_json(tmp_path / "nonexistent.json")
        assert result == {}

    def test_valid_json_parsed(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"key": "value", "num": 42}', encoding="utf-8")
        result = safe_read_json(f)
        assert result == {"key": "value", "num": 42}

    def test_invalid_json_returns_empty_dict(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not valid json {{", encoding="utf-8")
        result = safe_read_json(f)
        assert result == {}

    def test_empty_file_returns_empty_dict(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("", encoding="utf-8")
        result = safe_read_json(f)
        assert result == {}


# ─────────────────────────────────────────
# config.py — load_env_file
# ─────────────────────────────────────────

from config import load_env_file


class TestLoadEnvFile:
    def test_missing_file_no_error(self, tmp_path):
        load_env_file(tmp_path / "nonexistent.env")  # 예외 없어야 함

    def test_loads_key_value(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_LOAD_KEY=hello123\n", encoding="utf-8")
        monkeypatch.delenv("TEST_LOAD_KEY", raising=False)
        load_env_file(env_file)
        assert os.environ.get("TEST_LOAD_KEY") == "hello123"

    def test_skips_comments(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("# COMMENT=ignored\nREAL_KEY=real\n", encoding="utf-8")
        monkeypatch.delenv("REAL_KEY", raising=False)
        load_env_file(env_file)
        assert os.environ.get("REAL_KEY") == "real"
        assert os.environ.get("# COMMENT") is None

    def test_does_not_override_existing(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text("EXISTING_KEY=new_value\n", encoding="utf-8")
        monkeypatch.setenv("EXISTING_KEY", "original")
        load_env_file(env_file)
        assert os.environ.get("EXISTING_KEY") == "original"

    def test_strips_quotes(self, tmp_path, monkeypatch):
        env_file = tmp_path / ".env"
        env_file.write_text('QUOTED_KEY="quoted_value"\n', encoding="utf-8")
        monkeypatch.delenv("QUOTED_KEY", raising=False)
        load_env_file(env_file)
        assert os.environ.get("QUOTED_KEY") == "quoted_value"
