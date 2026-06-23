"""Unit tests for ai_anime main.py pipeline (rebuilt 2026-06-08)."""
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from main import (
    Song, VisualIdentity,
    parse_song, load_profiles, build_visual_identity,
    _build_scene_image_blocks, _build_scene_video_blocks,
    adapt_template, safety_filter, _unresolved_placeholders,
    build_readme, _DEFAULT_SECTIONS, SAFETY_BLOCKLIST,
    PROMPT_FILES, PROFILES_FILE, TEMPLATE_DIR,
    _required_variants,
)

ROOT = Path(__file__).parent


# ─── helpers ────────────────────────────────────────────────────────────────

def _make_song(title="Test Song", genre="rock metal", bpm="120 BPM", mood="energetic"):
    return Song(title=title, genre=genre, bpm=bpm, mood=mood)


def _make_identity(genre="rock metal"):
    profiles = load_profiles()
    return build_visual_identity(_make_song(genre=genre), profiles)


# ─── Song dataclass ──────────────────────────────────────────────────────────

def test_song_defaults():
    song = Song(title="", genre="", bpm="", mood="")
    assert song.title == ""
    assert song.genre == ""
    assert song.bpm == ""
    assert song.mood == ""
    assert song.sections == []


def test_song_fields():
    song = Song(title="테스트 곡", genre="ballad", bpm="80 BPM", mood="sad")
    assert song.title == "테스트 곡"
    assert song.genre == "ballad"
    assert song.bpm == "80 BPM"


# ─── parse_song ──────────────────────────────────────────────────────────────

def test_parse_song_basic_fields():
    with tempfile.TemporaryDirectory() as td:
        txt = Path(td) / "my_song.txt"
        txt.write_text(
            "Song Title: My Song\nGenre: rock\nBPM: 120\nMood: energetic\n",
            encoding="utf-8",
        )
        song = parse_song(txt)
    assert song.title == "My Song"
    assert song.genre == "rock"
    assert "120" in song.bpm
    assert song.mood == "energetic"


def test_parse_song_title_fallback():
    with tempfile.TemporaryDirectory() as td:
        txt = Path(td) / "fallback_title.txt"
        # BPM-only line is skipped by _infer_title → triggers filename fallback
        txt.write_text("120 BPM\n", encoding="utf-8")
        song = parse_song(txt)
    assert song.title == "fallback_title"


def test_parse_song_bpm_from_genre_text():
    with tempfile.TemporaryDirectory() as td:
        txt = Path(td) / "s.txt"
        txt.write_text("Song Title: X\nGenre: indie pop, 95 BPM, acoustic\n", encoding="utf-8")
        song = parse_song(txt)
    assert "95" in song.bpm


def test_parse_song_sections_parsed():
    with tempfile.TemporaryDirectory() as td:
        txt = Path(td) / "s.txt"
        txt.write_text(
            "Song Title: S\nGenre: rock\n\n[Intro]\nhello\n[Chorus]\nworld\n",
            encoding="utf-8",
        )
        song = parse_song(txt)
    labels = [s.label for s in song.sections]
    assert "Intro" in labels
    assert "Chorus" in labels


def test_parse_song_korean_title():
    with tempfile.TemporaryDirectory() as td:
        txt = Path(td) / "korean_song.txt"
        txt.write_text("Song Title: 그래서 더 좋아\nGenre: k-pop\n", encoding="utf-8")
        song = parse_song(txt)
    assert song.title == "그래서 더 좋아"


def test_parse_song_ignores_unknown_keys():
    with tempfile.TemporaryDirectory() as td:
        txt = Path(td) / "s.txt"
        txt.write_text("Song Title: S\nUnknown Key: value\n", encoding="utf-8")
        song = parse_song(txt)
    assert song.title == "S"


# ─── load_profiles ───────────────────────────────────────────────────────────

def test_load_profiles_has_profiles_key():
    profiles = load_profiles()
    assert "profiles" in profiles


def test_load_profiles_schema_version():
    profiles = load_profiles()
    assert profiles.get("schema_version") == 1


def test_load_profiles_contains_telephone_signal_pop():
    profiles = load_profiles()
    assert "telephone-signal-pop" in profiles["profiles"]


def test_load_profiles_contains_rock():
    profiles = load_profiles()
    assert "rock" in profiles["profiles"]


def test_load_profiles_each_has_required_fields():
    profiles = load_profiles()
    required = ["environments", "camera_shots", "motion_language"]
    for name, prof in profiles["profiles"].items():
        for field_name in required:
            assert field_name in prof, f"Profile '{name}' missing '{field_name}'"


# ─── build_visual_identity ───────────────────────────────────────────────────

def test_build_visual_identity_returns_identity():
    profiles = load_profiles()
    identity = build_visual_identity(_make_song(), profiles)
    assert isinstance(identity, VisualIdentity)


def test_build_visual_identity_rock_keywords():
    profiles = load_profiles()
    identity = build_visual_identity(_make_song(genre="rock metal punk"), profiles)
    assert identity.profile_key == "rock"


def test_build_visual_identity_ballad_keywords():
    profiles = load_profiles()
    identity = build_visual_identity(_make_song(genre="acoustic ballad piano gentle"), profiles)
    assert identity.profile_key == "acoustic_ballad"


def test_build_visual_identity_default_fallback():
    profiles = load_profiles()
    identity = build_visual_identity(_make_song(genre="unknown unusual genre xyz"), profiles)
    assert identity.profile_key == "electronic_synth_default"
    assert identity.reference_image == "reference/base.png"


def test_build_visual_identity_matched_genre_uses_genre_reference():
    profiles = load_profiles()
    identity = build_visual_identity(_make_song(genre="rock metal"), profiles)
    assert identity.reference_image == "reference/rock.png"


def test_build_visual_identity_avoid_populated():
    profiles = load_profiles()
    identity = build_visual_identity(_make_song(genre="rock metal"), profiles)
    assert isinstance(identity.avoid, list)
    assert len(identity.avoid) > 0


def test_build_visual_identity_environments_list():
    assert len(_make_identity("rock").environments) == 10


def test_build_visual_identity_camera_shots_list():
    assert len(_make_identity("rock").camera_shots) == 10


# ─── SAFETY_BLOCKLIST ────────────────────────────────────────────────────────

def test_safety_blocklist_no_minor():
    assert "minor" not in SAFETY_BLOCKLIST


def test_safety_blocklist_has_underage():
    assert "underage" in SAFETY_BLOCKLIST


def test_safety_blocklist_has_blood():
    assert "blood" in SAFETY_BLOCKLIST


# ─── safety_filter ───────────────────────────────────────────────────────────

def test_safety_filter_blood():
    result = safety_filter("blood red sky")
    assert "blood" not in result.lower()
    assert "energy glow" in result


def test_safety_filter_weapon():
    result = safety_filter("holding a weapon")
    assert "weapon" not in result.lower()
    assert "prop" in result


def test_safety_filter_gore():
    result = safety_filter("intense gore effects")
    assert "gore" not in result.lower()


def test_safety_filter_nude():
    result = safety_filter("nude scene")
    assert "nude" not in result.lower()


def test_safety_filter_case_insensitive():
    result = safety_filter("BLOOD and GORE")
    assert "blood" not in result.lower()
    assert "gore" not in result.lower()


def test_safety_filter_preserves_safe_text():
    safe = "anime cinematic lighting with electric blue glow"
    assert safety_filter(safe) == safe


# ─── _unresolved_placeholders ────────────────────────────────────────────────

def test_unresolved_empty():
    assert _unresolved_placeholders("clean text") == []


def test_unresolved_detects_placeholder():
    found = _unresolved_placeholders("Hello [SONG_TITLE] world [GENRE]")
    assert "SONG_TITLE" in found
    assert "GENRE" in found


def test_unresolved_ignores_short_tokens():
    assert _unresolved_placeholders("[AB] text") == []


# ─── _DEFAULT_SECTIONS ───────────────────────────────────────────────────────

def test_default_sections_has_intro():
    assert _DEFAULT_SECTIONS[0] == "Intro"


def test_default_sections_has_outro():
    assert _DEFAULT_SECTIONS[-1] == "Outro"


def test_default_sections_minimum_count():
    assert len(_DEFAULT_SECTIONS) >= 6


# ─── _build_scene_image_blocks ───────────────────────────────────────────────

def test_build_scene_image_blocks_scene_count():
    song = _make_song()
    identity = _make_identity()
    result = _build_scene_image_blocks(song, identity)
    assert result.count("## Scene") == len(_DEFAULT_SECTIONS)


def test_build_scene_image_blocks_all_platforms():
    song = _make_song()
    identity = _make_identity()
    result = _build_scene_image_blocks(song, identity)
    assert "GPT Image" in result
    assert "Google Gemini" in result
    assert "Midjourney v7" in result
    assert "Nijijourney" in result
    assert "FLUX.1" in result
    assert "Leonardo.Ai" in result


def test_build_scene_image_blocks_avoid_in_output():
    song = _make_song(genre="rock metal punk")
    identity = _make_identity("rock metal punk")
    result = _build_scene_image_blocks(song, identity)
    if identity.avoid:
        assert identity.avoid[0] in result


def test_build_scene_image_blocks_no_unresolved_placeholders():
    song = _make_song()
    identity = _make_identity()
    result = _build_scene_image_blocks(song, identity)
    assert _unresolved_placeholders(result) == []


# ─── _build_scene_video_blocks ───────────────────────────────────────────────

def test_build_scene_video_blocks_scene_count():
    song = _make_song(genre="acoustic ballad piano")
    profiles = load_profiles()
    identity = build_visual_identity(song, profiles)
    result = _build_scene_video_blocks(song, identity)
    assert result.count("## Scene") == len(_DEFAULT_SECTIONS)


def test_build_scene_video_blocks_has_kling():
    song = _make_song()
    identity = _make_identity()
    result = _build_scene_video_blocks(song, identity)
    assert "Kling AI" in result


def test_build_scene_video_blocks_has_variants():
    song = _make_song()
    identity = _make_identity()
    result = _build_scene_video_blocks(song, identity)
    assert "Variant A" in result
    assert "Variant B" in result
    assert "Variant C" in result


def test_build_scene_video_blocks_has_capcut_map():
    song = _make_song()
    identity = _make_identity()
    result = _build_scene_video_blocks(song, identity)
    assert "CapCut Editing Map" in result


def test_build_scene_video_blocks_clip_count_matches_capcut():
    song = _make_song()
    identity = _make_identity()
    result = _build_scene_video_blocks(song, identity)
    expected = sum(len(_required_variants(s)) for s in _DEFAULT_SECTIONS)
    assert f"실제 생성 클립 {expected}개" in result


# ─── _required_variants ──────────────────────────────────────────────────────

def test_required_variants_intro():
    assert _required_variants("Intro") == ["A"]


def test_required_variants_chorus():
    assert _required_variants("Chorus") == ["B", "C"]


def test_required_variants_verse():
    assert _required_variants("Verse 1") == ["base", "A"]


def test_required_variants_pre_chorus():
    assert _required_variants("Pre-Chorus") == ["B"]


def test_required_variants_outro():
    assert _required_variants("Outro") == ["A"]


def test_required_variants_no_duplicates():
    for section in _DEFAULT_SECTIONS:
        result = _required_variants(section)
        assert len(result) == len(set(result)), f"Duplicates in {section}: {result}"


def test_required_variants_total_less_than_4x_scenes():
    total = sum(len(_required_variants(s)) for s in _DEFAULT_SECTIONS)
    max_possible = len(_DEFAULT_SECTIONS) * 4
    assert total < max_possible


# ─── adapt_template ──────────────────────────────────────────────────────────

def test_adapt_template_replaces_song_title():
    song = _make_song(title="My Song")
    identity = _make_identity()
    result = adapt_template("[SONG_TITLE] prompt", song, identity)
    assert "My Song" in result
    assert "[SONG_TITLE]" not in result


def test_adapt_template_scene_range_replaced():
    song = _make_song()
    identity = _make_identity()
    result = adapt_template("scenes [SCENE_RANGE]", song, identity)
    assert "[SCENE_RANGE]" not in result
    assert "01" in result


def test_adapt_template_scene_count_replaced():
    song = _make_song()
    identity = _make_identity()
    result = adapt_template("total [SCENE_COUNT] clips", song, identity)
    assert "[SCENE_COUNT]" not in result
    assert str(len(_DEFAULT_SECTIONS)) in result


def test_adapt_template_safety_applied():
    song = _make_song()
    identity = _make_identity()
    result = adapt_template("blood scene [SONG_TITLE]", song, identity)
    assert "blood" not in result.lower()


# ─── build_readme ────────────────────────────────────────────────────────────

def test_build_readme_contains_title():
    song = _make_song(title="My Song")
    identity = _make_identity()
    readme = build_readme(song, identity)
    assert "My Song" in readme


def test_build_readme_contains_file_list():
    song = _make_song()
    identity = _make_identity()
    readme = build_readme(song, identity)
    assert "00_character_sheet.md" in readme
    assert "01_image_prompts.md" in readme
    assert "02_video_prompts.md" in readme


def test_build_readme_filtered_when_safety_applied():
    song = Song(title="X", genre="rock", bpm="", mood="blood of heroes")
    identity = _make_identity("rock metal")
    readme = safety_filter(build_readme(song, identity))
    assert "blood" not in readme.lower()


# ─── PROMPT_FILES constant ───────────────────────────────────────────────────

def test_prompt_files_count():
    assert len(PROMPT_FILES) == 4


def test_prompt_files_has_character_sheet():
    assert "00_character_sheet.md" in PROMPT_FILES


def test_prompt_files_has_production_guide():
    assert "03_production_guide.md" in PROMPT_FILES


# ─── templates exist ─────────────────────────────────────────────────────────

def test_templates_all_exist():
    for fname in PROMPT_FILES:
        p = TEMPLATE_DIR / fname
        assert p.exists(), f"Template missing: {fname}"


# ─── anime_profiles.json validity ────────────────────────────────────────────

def test_profiles_json_valid():
    assert PROFILES_FILE.exists()
    data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
    assert "profiles" in data


def test_profiles_telephone_has_10_environments():
    data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
    assert len(data["profiles"]["telephone-signal-pop"]["environments"]) == 10


def test_profiles_telephone_has_10_camera_shots():
    data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
    assert len(data["profiles"]["telephone-signal-pop"]["camera_shots"]) == 10


def test_profiles_rock_no_crowd_in_environments():
    data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
    envs = data["profiles"]["rock"]["environments"]
    crowd_terms = ["crowd", "audience", "spectator"]
    for env in envs:
        for term in crowd_terms:
            assert term not in env.lower(), (
                f"rock environment mentions '{term}': {env}"
            )


def test_profiles_all_have_avoid_field():
    data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
    for name, prof in data["profiles"].items():
        assert "avoid" in prof, f"Profile '{name}' missing 'avoid' field"


# ─── style_keywords ──────────────────────────────────────────────────────────

def test_profiles_all_have_style_keywords():
    data = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
    for name, prof in data["profiles"].items():
        assert "style_keywords" in prof, f"Profile '{name}' missing 'style_keywords' field"
        assert prof["style_keywords"].strip(), f"Profile '{name}' has empty style_keywords"


def test_identity_style_keywords_in_output():
    profiles = load_profiles()
    identity = build_visual_identity(_make_song(genre="rock metal"), profiles)
    assert identity.style_keywords
    blocks = _build_scene_image_blocks(_make_song(genre="rock metal"), identity)
    assert identity.style_keywords in blocks


# ─── Genre Profile 직접 지정 ─────────────────────────────────────────────────

def test_parse_song_genre_profile_field():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as f:
        f.write("Title: 테스트\nGenre: unknown xyz\nGenre Profile: jazz_soul\n")
        tmp = Path(f.name)
    song = parse_song(tmp)
    tmp.unlink()
    assert song.genre_profile == "jazz_soul"


def test_build_visual_identity_genre_profile_override():
    profiles = load_profiles()
    song = Song(title="T", genre="unknown xyz", bpm="90", mood="", genre_profile="jazz_soul")
    identity = build_visual_identity(song, profiles)
    assert identity.profile_key == "jazz_soul"


def test_build_visual_identity_invalid_genre_profile_raises():
    import pytest
    profiles = load_profiles()
    song = Song(title="T", genre="rock", bpm="120", mood="", genre_profile="nonexistent_key")
    with pytest.raises(ValueError, match="anime_profiles.json에 없습니다"):
        build_visual_identity(song, profiles)


# ─── reference_image ─────────────────────────────────────────────────────────

def test_identity_has_reference_image():
    profiles = load_profiles()
    identity = build_visual_identity(_make_song(genre="rock metal"), profiles)
    assert identity.reference_image
    assert identity.reference_image.startswith("reference/")
    assert identity.reference_image.endswith(".png")


def test_reference_image_file_exists():
    from main import REFERENCE_DIR
    profiles = load_profiles()
    for genre, song in [
        ("rock metal", _make_song(genre="rock metal")),
        ("hip hop rap", _make_song(genre="hip hop rap")),
        ("jazz soul", _make_song(genre="jazz soul")),
        ("acoustic ballad folk", _make_song(genre="acoustic ballad folk")),
    ]:
        identity = build_visual_identity(song, profiles)
        ref_path = REFERENCE_DIR.parent / identity.reference_image
        assert ref_path.exists(), f"Reference file missing: {identity.reference_image}"


def test_reference_fallback_to_base():
    from main import REFERENCE_DIR, REFERENCE_IMAGE_MAP
    base = REFERENCE_DIR / "base.png"
    assert base.exists(), "base.png must exist as fallback"


def test_reference_image_in_prompt_output():
    profiles = load_profiles()
    identity = build_visual_identity(_make_song(genre="rock metal"), profiles)
    blocks = _build_scene_image_blocks(_make_song(genre="rock metal"), identity)
    assert identity.reference_image in blocks
