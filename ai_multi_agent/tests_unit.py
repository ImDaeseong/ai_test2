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


# ─────────────────────────────────────────
# web_app_scaffold.py — create_prompt_runner_app
# Flask test client only, no real network/API calls.
# web_app_story.py / web_app_scenario.py are thin wrappers around this
# scaffold, so testing the scaffold in isolation (fake managed_summary /
# managed_output_file) covers both.
# ─────────────────────────────────────────

import web_app_scaffold
from web_app_scaffold import PromptRunnerConfig, create_prompt_runner_app


def _fake_runner(tmp_path, *, api_key="fake-key", **overrides):
    project = tmp_path / "demo_project"
    project.mkdir()

    def managed_summary(project_dir):
        return {"title": "Demo Title", "total": 2, "current": 1, "next_num": 2, "next_file": None}

    def managed_output_file(project_dir, num):
        return project_dir / f"unit{num:02d}_output.md"

    fields = dict(
        kind="teststory",
        port=9999,
        title="Test Prompt Runner",
        sub_label="test sub label",
        project_label="Test Projects",
        unit_dirname="units",
        unit_label_fmt="u{:02d}",
        unit_heading="All Test Prompts",
        accent_color="#123456",
        accent_dark_text="#000000",
        output_dir=tmp_path,
        managed_summary=managed_summary,
        managed_output_file=managed_output_file,
        openrouter_api_key=api_key,
    )
    fields.update(overrides)
    cfg = PromptRunnerConfig(**fields)
    return create_prompt_runner_app(cfg), project


class TestPromptRunnerScaffoldIndexAndProjects:
    def test_index_returns_html_with_title(self, tmp_path):
        app, _ = _fake_runner(tmp_path)
        resp = app.test_client().get("/")
        assert resp.status_code == 200
        assert resp.content_type.startswith("text/html")
        assert "Test Prompt Runner" in resp.get_data(as_text=True)

    def test_projects_lists_dirs_under_output_dir(self, tmp_path):
        app, project = _fake_runner(tmp_path)
        data = app.test_client().get("/api/projects").get_json()
        assert data["ok"] is True
        assert data["output_dir_exists"] is True
        assert "warning" not in data
        assert [p["name"] for p in data["projects"]] == [project.name]

    def test_projects_warns_when_output_dir_missing(self, tmp_path):
        missing_dir = tmp_path / "does_not_exist"
        app, _ = _fake_runner(tmp_path, output_dir=missing_dir)
        data = app.test_client().get("/api/projects").get_json()
        assert data["ok"] is True
        assert data["output_dir_exists"] is False
        assert data["projects"] == []
        assert str(missing_dir) in data["warning"]


class TestPromptRunnerScaffoldDetail:
    def test_missing_project_returns_404(self, tmp_path):
        app, _ = _fake_runner(tmp_path)
        resp = app.test_client().get("/api/detail/does-not-exist")
        assert resp.status_code == 404
        assert resp.get_json()["ok"] is False

    def test_existing_project_returns_detail_with_formatted_label(self, tmp_path):
        app, project = _fake_runner(tmp_path)
        data = app.test_client().get(f"/api/detail/{project.name}").get_json()
        assert data["ok"] is True
        assert data["title"] == "Demo Title"
        assert data["next_label"] == "u02"  # unit_label_fmt applied to next_num
        assert len(data["prompts"]) == 2


class TestPromptRunnerScaffoldRun:
    def test_missing_api_key_returns_400_without_calling_run_prompt_once(self, tmp_path, monkeypatch):
        app, project = _fake_runner(tmp_path, api_key=None)
        monkeypatch.setattr(
            web_app_scaffold, "run_prompt_once",
            lambda *a, **kw: (_ for _ in ()).throw(AssertionError("should not be called")),
        )
        resp = app.test_client().post("/api/run", json={"name": project.name})
        assert resp.status_code == 400
        assert "OPENROUTER_API_KEY" in resp.get_json()["error"]

    def test_missing_project_returns_404(self, tmp_path):
        app, _ = _fake_runner(tmp_path)
        resp = app.test_client().post("/api/run", json={"name": "nope"})
        assert resp.status_code == 404

    def test_success_path_calls_run_prompt_once_with_kind_and_returns_result(self, tmp_path, monkeypatch):
        app, project = _fake_runner(tmp_path)
        (project / "units").mkdir()
        (project / "units" / "u02_GPT_프롬프트.md").write_text("prompt body", encoding="utf-8")
        calls = {}

        def fake_run_prompt_once(prompt_file, output_file, mode, force, max_tokens):
            calls["mode"] = mode
            calls["force"] = force
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("generated result", encoding="utf-8")
            return output_file

        monkeypatch.setattr(web_app_scaffold, "run_prompt_once", fake_run_prompt_once)
        resp = app.test_client().post("/api/run", json={"name": project.name, "num": 2})
        data = resp.get_json()
        assert data["ok"] is True
        assert calls["mode"] == "teststory"
        assert "generated result" in data["result"]

    def test_file_exists_error_returns_409_with_exists_flag(self, tmp_path, monkeypatch):
        app, project = _fake_runner(tmp_path)
        (project / "units").mkdir()
        (project / "units" / "u02_GPT_프롬프트.md").write_text("prompt body", encoding="utf-8")

        def fake_run_prompt_once(*a, **kw):
            raise FileExistsError("이미 있음")

        monkeypatch.setattr(web_app_scaffold, "run_prompt_once", fake_run_prompt_once)
        resp = app.test_client().post("/api/run", json={"name": project.name, "num": 2})
        assert resp.status_code == 409
        assert resp.get_json()["exists"] is True


# ─────────────────────────────────────────
# web_app_story.py / web_app_scenario.py — thin-wrapper wiring
# Confirms the extraction preserved each app's identity (port, labels).
# ─────────────────────────────────────────

class TestWebAppStoryWiring:
    def test_module_exposes_app_and_port(self):
        import web_app_story
        assert web_app_story.PORT == 5400
        assert web_app_story.app is not None

    def test_index_html_reflects_story_config(self):
        import web_app_story
        html = web_app_story.app.test_client().get("/").get_data(as_text=True)
        assert "Story Prompt Runner" in html
        assert "port 5400" in html


class TestWebAppScenarioWiring:
    def test_module_exposes_app_and_port(self):
        import web_app_scenario
        assert web_app_scenario.PORT == 5300
        assert web_app_scenario.app is not None

    def test_index_html_reflects_scenario_config(self):
        import web_app_scenario
        html = web_app_scenario.app.test_client().get("/").get_data(as_text=True)
        assert "Scenario Prompt Runner" in html
        assert "port 5300" in html
