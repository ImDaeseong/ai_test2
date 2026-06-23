"""main.py 단위 + 통합 테스트."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from main import (
    Song,
    Section,
    PROJECT_ROOT,
    PROMPT_FILES,
    normalize_field_key,
    strip_noise_lines,
    parse_key_value,
    parse_loose_metadata,
    infer_title,
    parse_sections,
    infer_instruments,
    is_negative_tag,
    is_inline_note_line,
    strip_inline_notes,
    positive_tag_text,
    song_slug,
    has_identity_lock,
    role_lines,
    keyword_present,
    infer_profile,
    parse_song,
    validate_song_folder,
    create_song_folder,
    build_song_prompt_overview,
    summarize_prompt_outputs,
    soften_aggressive_residue,
    run_with_file_retries,
    SONG_OVERVIEW_FILE,
    ALL_OVERVIEW_FILE,
    PROMPT_AUDIT_FILE,
    GENRE_PROFILES_PATH,
    _GENRE_DATA,
)


# ---------------------------------------------------------------------------
# 공통 헬퍼
# ---------------------------------------------------------------------------

def make_song(**kwargs) -> Song:
    defaults = dict(
        title="테스트곡",
        genre="indie pop",
        bpm="96 BPM",
        mood="emotional",
        emotion="nostalgic",
        tempo="96 BPM groove",
        stage_energy="restrained",
        lighting_style="soft neon",
        camera_style="slow push-in",
        special_effects="drifting smoke",
        instruments="guitar, bass",
        sections=[],
        raw_text="",
    )
    defaults.update(kwargs)
    return Song(**defaults)


@pytest.fixture
def reference_dir(tmp_path: Path) -> Path:
    """유효한 기준 이미지 폴더 (더미 파일 포함)."""
    ref = tmp_path / "reference"
    ref.mkdir()
    (ref / "dummy_band.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    return ref


# ---------------------------------------------------------------------------
# normalize_field_key
# ---------------------------------------------------------------------------

class TestNormalizeFieldKey:
    def test_english_title(self):
        assert normalize_field_key("title") == "title"

    def test_korean_title(self):
        assert normalize_field_key("제목") == "title"

    def test_genre_aliases(self):
        assert normalize_field_key("장르") == "genre"
        assert normalize_field_key("style") == "genre"
        assert normalize_field_key("스타일") == "genre"

    def test_bpm(self):
        assert normalize_field_key("bpm") == "bpm"

    def test_case_insensitive(self):
        assert normalize_field_key("TITLE") == "title"
        assert normalize_field_key("  Title  ") == "title"

    def test_unknown_key_returns_none(self):
        assert normalize_field_key("unknown_field") is None

    def test_song_title_alias(self):
        assert normalize_field_key("song title") == "title"


# ---------------------------------------------------------------------------
# strip_noise_lines
# ---------------------------------------------------------------------------

class TestStripNoiseLines:
    def test_keeps_normal_lines(self):
        result = strip_noise_lines("안녕하세요\n테스트입니다")
        assert "안녕하세요" in result
        assert "테스트입니다" in result

    def test_removes_time_ago(self):
        result = strip_noise_lines("3d ago\n2h ago\nnormal")
        lines = [ln for ln in result if ln.strip()]
        assert all("ago" not in ln for ln in lines)

    def test_removes_cover_image_prefix(self):
        result = strip_noise_lines("cover image for this song\nnormal")
        assert not any("cover image for" in ln for ln in result)

    def test_removes_timestamp_format(self):
        result = strip_noise_lines("1:23\n12:34:56\nnormal")
        assert "1:23" not in result
        assert "12:34:56" not in result

    def test_preserves_empty_lines(self):
        result = strip_noise_lines("first\n\nsecond")
        assert "" in result


# ---------------------------------------------------------------------------
# parse_key_value
# ---------------------------------------------------------------------------

class TestParseKeyValue:
    def test_basic_english(self):
        assert parse_key_value("Title: 환승역") == ("title", "환승역")

    def test_utf8_bom_english(self):
        assert parse_key_value("\ufeffTitle: Sample") == ("title", "Sample")

    def test_korean_key(self):
        assert parse_key_value("장르: indie pop") == ("genre", "indie pop")

    def test_no_colon_returns_none(self):
        assert parse_key_value("no colon here") is None

    def test_unknown_key_returns_none(self):
        assert parse_key_value("unknown_key: value") is None

    def test_strips_value_whitespace(self):
        result = parse_key_value("title:  환승역  ")
        assert result is not None
        assert result[1] == "환승역"


# ---------------------------------------------------------------------------
# parse_loose_metadata
# ---------------------------------------------------------------------------

class TestParseLooseMetadata:
    def test_weirdness(self):
        assert parse_loose_metadata("Weirdness 18%") == ("weirdness", "18%")

    def test_style_influence(self):
        assert parse_loose_metadata("Style Influence 74%") == ("style_influence", "74%")

    def test_case_insensitive(self):
        assert parse_loose_metadata("WEIRDNESS 50%") is not None

    def test_no_match(self):
        assert parse_loose_metadata("normal line") is None


# ---------------------------------------------------------------------------
# infer_title
# ---------------------------------------------------------------------------

class TestInferTitle:
    def test_title_override_wins(self):
        assert infer_title([], {}, title_override="오버라이드") == "오버라이드"

    def test_fields_title_used(self):
        assert infer_title([], {"title": "환승역"}) == "환승역"

    def test_korean_label_in_lines(self):
        lines = ["제목: 환승역", "[Verse]", "가사"]
        assert infer_title(lines, {}) == "환승역"

    def test_title_label_in_lines(self):
        lines = ["title: My Song", "[Verse]"]
        assert infer_title(lines, {}) == "My Song"

    def test_fallback_used_when_no_title(self):
        assert infer_title([], {}, title_fallback="fallback_title") == "fallback_title"

    def test_no_title_raises(self):
        with pytest.raises(ValueError, match="곡 제목"):
            infer_title([], {})

    def test_single_ascii_word_not_treated_as_title(self):
        # "Korean" 한 단어만 있으면 제목 오탐 방지 → ValueError
        lines = ["Korean", "[Verse]", "가사"]
        with pytest.raises(ValueError):
            infer_title(lines, {})

    def test_korean_short_line_is_title(self):
        lines = ["환승역", "[Verse]"]
        assert infer_title(lines, {}) == "환승역"

    def test_bpm_line_skipped(self):
        lines = ["96 BPM", "환승역", "[Verse]"]
        assert infer_title(lines, {}) == "환승역"

    def test_percent_line_skipped(self):
        lines = ["Weirdness 18%", "환승역", "[Verse]"]
        assert infer_title(lines, {}) == "환승역"

    def test_stops_searching_at_section_header(self):
        lines = ["[Verse]", "환승역"]
        with pytest.raises(ValueError):
            infer_title(lines, {})

    def test_multiword_english_title_accepted(self):
        # 여러 단어 영어 제목은 허용
        lines = ["My Great Song", "[Verse]"]
        assert infer_title(lines, {}) == "My Great Song"


# ---------------------------------------------------------------------------
# parse_sections
# ---------------------------------------------------------------------------

class TestParseSections:
    def test_basic_verse(self):
        sections = parse_sections(["[Verse]", "가사 한 줄", "가사 두 줄"])
        assert len(sections) == 1
        assert sections[0].label == "Verse"
        assert "가사 한 줄" in sections[0].lines

    def test_multiple_sections(self):
        sections = parse_sections(["[Intro]", "인트로", "[Chorus]", "후렴"])
        assert len(sections) == 2
        assert sections[0].label == "Intro"
        assert sections[1].label == "Chorus"

    def test_pre_chorus_normalized(self):
        sections = parse_sections(["[Pre-Chorus]"])
        assert sections[0].label == "Pre-Chorus"

    def test_section_with_note(self):
        sections = parse_sections(["[Bridge: emotional climax]", "브릿지"])
        assert sections[0].note == "emotional climax"

    def test_unknown_label_ignored(self):
        sections = parse_sections(["[RandomLabel]", "텍스트"])
        assert len(sections) == 0

    def test_verse_numbered(self):
        sections = parse_sections(["[Verse 1]", "가사"])
        assert sections[0].label == "Verse 1"

    def test_final_chorus(self):
        sections = parse_sections(["[Final Chorus]", "가사"])
        assert sections[0].label == "Final Chorus"

    def test_empty_input(self):
        assert parse_sections([]) == []

    def test_instrumental_break_parsed(self):
        sections = parse_sections(["[Instrumental Break]", "ambient swell"])
        assert len(sections) == 1
        assert sections[0].label == "Instrumental Break"

    def test_instrumental_break_does_not_bleed_into_bridge(self):
        """[Instrumental Break]이 Bridge 가사에 섞이지 않아야 한다."""
        lines = [
            "[Bridge]", "브릿지 가사",
            "[Instrumental Break]", "ambient line",
            "[Final Chorus]", "파이널 코러스",
        ]
        sections = parse_sections(lines)
        labels = [s.label for s in sections]
        assert "Instrumental Break" in labels
        bridge = next(s for s in sections if s.label == "Bridge")
        assert "[Instrumental Break]" not in bridge.lines

    def test_instrumental_break_with_note(self):
        sections = parse_sections(["[Instrumental Break: taepyeongso ambient swell]"])
        assert sections[0].label == "Instrumental Break"
        assert "taepyeongso" in sections[0].note


# ---------------------------------------------------------------------------
# infer_instruments
# ---------------------------------------------------------------------------

class TestInferInstruments:
    def test_guitar_detected(self):
        assert "guitar" in infer_instruments("clean guitar melody")

    def test_subway_ambience_not_duplicated(self):
        # "subway ambience" 텍스트 + 한글 환승 동시 → 중복 없이 1회
        result = infer_instruments("subway ambience 환승 열차")
        assert result.count("subway ambience") == 1

    def test_korean_synth_converted(self):
        assert "warm synths" in infer_instruments("신스 패드")

    def test_subway_via_korean_only(self):
        result = infer_instruments("환승역 멜로디")
        assert "subway ambience" in result

    def test_default_when_nothing_matches(self):
        result = infer_instruments("nothing specific here")
        assert "vocal" in result

    def test_multiple_instruments(self):
        result = infer_instruments("guitar bass drum piano")
        for inst in ["guitar", "bass", "drum", "piano"]:
            assert inst in result

    def test_gayageum_detected(self):
        assert "gayageum" in infer_instruments("gayageum texture surf ambience")

    def test_ajaeng_detected(self):
        assert "ajaeng" in infer_instruments("ajaeng drone taepyeongso ambient")

    def test_taepyeongso_detected(self):
        assert "taepyeongso" in infer_instruments("taepyeongso ambient swell reverse texture")

    def test_haegeum_detected(self):
        assert "haegeum" in infer_instruments("haegeum melody folk emotional")

    def test_traditional_does_not_fallback_to_default(self):
        result = infer_instruments("gayageum ajaeng traditional korean")
        assert result != "vocal, guitar, bass, drums, cinematic atmosphere"


# ---------------------------------------------------------------------------
# is_negative_tag / positive_tag_text
# ---------------------------------------------------------------------------

class TestNegativeTags:
    def test_dash_prefix(self):
        assert is_negative_tag("-Heavy autotune") is True

    def test_no_prefix(self):
        assert is_negative_tag("no autotune") is True

    def test_not_prefix(self):
        assert is_negative_tag("not recommended") is True

    def test_normal_tag_is_positive(self):
        assert is_negative_tag("warm piano") is False

    def test_positive_tag_text_filters_negatives(self):
        text = "-Heavy autotune, warm piano, -EDM drop"
        result = positive_tag_text(text)
        assert "warm piano" in result
        assert "Heavy autotune" not in result
        assert "EDM drop" not in result


# ---------------------------------------------------------------------------
# song_slug
# ---------------------------------------------------------------------------

class TestSongSlug:
    def test_korean_title_unchanged(self):
        assert song_slug("환승역") == "환승역"

    def test_replaces_colon(self):
        assert ":" not in song_slug("My: Song")

    def test_replaces_angle_brackets(self):
        slug = song_slug("<test>")
        assert "<" not in slug
        assert ">" not in slug

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            song_slug("")

    def test_all_dots_raises(self):
        with pytest.raises(ValueError):
            song_slug("...")


# ---------------------------------------------------------------------------
# has_identity_lock
# ---------------------------------------------------------------------------

class TestHasIdentityLock:
    def test_detects_skeleton_band_phrase(self):
        assert has_identity_lock("AI Boy/AI Girl chibi toy robot figure on stage") is True

    def test_detects_do_not_redesign(self):
        assert has_identity_lock("Do not redesign the band") is True

    def test_detects_do_not_change(self):
        assert has_identity_lock("Do not change the identity") is True

    def test_no_lock_phrase(self):
        assert has_identity_lock("some random unrelated text") is False


# ---------------------------------------------------------------------------
# role_lines
# ---------------------------------------------------------------------------

class TestRoleLines:
    def test_subway_roles(self):
        s = make_song(raw_text="subway ambience 환승역 열차")
        roles = role_lines(s)
        vocal = roles["vocal"].lower()
        assert "restrained" in vocal or "subway" in vocal

    def test_rock_roles(self):
        s = make_song(raw_text="hard rock metal aggressive")
        roles = role_lines(s)
        assert "fierce" in roles["vocal"].lower()

    def test_pop_rap_roles(self):
        s = make_song(raw_text="힘들 pop rap melodic rap")
        roles = role_lines(s)
        assert "pop rap" in roles["vocal"].lower()

    def test_ballad_roles(self):
        s = make_song(raw_text="ballad piano acoustic")
        roles = role_lines(s)
        assert "softly" in roles["vocal"].lower()

    def test_default_roles(self):
        s = make_song(raw_text="general music nothing specific")
        roles = role_lines(s)
        assert "song-matched" in roles["vocal"].lower()

    def test_all_six_roles_present(self):
        s = make_song(raw_text="subway ambience")
        roles = role_lines(s)
        assert {"vocal", "guitar", "bass", "drum", "crowd", "stage"}.issubset(roles.keys())


# ---------------------------------------------------------------------------
# keyword_present
# ---------------------------------------------------------------------------

class TestKeywordPresent:
    def test_term_found(self):
        assert keyword_present("subway train ambience", ["subway"]) is True

    def test_term_not_found(self):
        assert keyword_present("indie pop song", ["rock"]) is False

    def test_case_insensitive(self):
        assert keyword_present("SUBWAY AMBIENCE", ["subway"]) is True

    def test_multiple_terms_any_match(self):
        assert keyword_present("soft indie", ["rock", "indie"]) is True


# ---------------------------------------------------------------------------
# validate_song_folder (통합)
# ---------------------------------------------------------------------------

class TestValidateSongFolder:
    def test_missing_folder_reported(self, tmp_path):
        errors = validate_song_folder(tmp_path / "nonexistent")
        assert any("폴더가 없습니다" in e for e in errors)

    def test_missing_files_reported(self, tmp_path, reference_dir):
        folder = tmp_path / "song"
        folder.mkdir()
        errors = validate_song_folder(folder, reference_dir=reference_dir)
        assert any("누락 파일" in e for e in errors)

    def test_placeholder_residue_detected(self, tmp_path, reference_dir):
        folder = tmp_path / "song"
        folder.mkdir()
        ref_str = str(reference_dir)
        for name in [*PROMPT_FILES, "README.md"]:
            (folder / name).write_text(
                f"same stylized fantasy cyberpunk skeleton music band\nDo not redesign\n"
                f"{ref_str}\n[SONG_TITLE] [GENRE]\n",
                encoding="utf-8",
            )
        errors = validate_song_folder(folder, reference_dir=reference_dir)
        assert any("placeholder" in e for e in errors)

    def test_previous_term_residue_detected(self, tmp_path, reference_dir):
        folder = tmp_path / "song"
        folder.mkdir()
        ref_str = str(reference_dir)
        for name in [*PROMPT_FILES, "README.md"]:
            (folder / name).write_text(
                f"same stylized fantasy cyberpunk skeleton music band\nDo not redesign\n"
                f"{ref_str}\n이전곡제목\n",
                encoding="utf-8",
            )
        errors = validate_song_folder(folder, previous_terms=["이전곡제목"],
                                      reference_dir=reference_dir)
        assert any("이전 곡 정보 잔여" in e for e in errors)

    def test_passes_when_all_valid(self, tmp_path, reference_dir):
        folder = tmp_path / "song"
        folder.mkdir()
        ref_str = str(reference_dir)
        for name in [*PROMPT_FILES, "README.md"]:
            (folder / name).write_text(
                f"same stylized fantasy cyberpunk skeleton music band\nDo not redesign\n{ref_str}\n",
                encoding="utf-8",
            )
        errors = validate_song_folder(folder, reference_dir=reference_dir)
        assert errors == []


# ---------------------------------------------------------------------------
# create_song_folder (통합)
# ---------------------------------------------------------------------------

class TestCreateSongFolder:
    def _basic_song(self) -> Song:
        return make_song(
            title="테스트곡",
            sections=[Section(label="Verse", note="", lines=["가사 한 줄"])],
        )

    def test_creates_all_expected_files(self, tmp_path, reference_dir):
        dest = create_song_folder(
            song=self._basic_song(),
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        for name in [*PROMPT_FILES, "README.md"]:
            assert (dest / name).exists(), f"누락: {name}"

    def test_no_placeholder_residue_after_create(self, tmp_path, reference_dir):
        dest = create_song_folder(
            song=self._basic_song(),
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], f"검증 실패:\n" + "\n".join(errors)

    def test_force_overwrites_existing(self, tmp_path, reference_dir):
        kwargs = dict(
            song=self._basic_song(),
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        create_song_folder(**kwargs)
        # --force 없이 두 번째 호출은 에러
        with pytest.raises(FileExistsError):
            create_song_folder(**kwargs)
        # --force 있으면 정상
        create_song_folder(**kwargs, force=True)

    def test_file_retry_recovers_from_temporary_windows_lock(self, tmp_path, monkeypatch):
        attempts = {"count": 0}

        def flaky_write() -> None:
            attempts["count"] += 1
            if attempts["count"] < 3:
                error = OSError("locked")
                error.winerror = 32
                raise error
            (tmp_path / "locked.md").write_text("ok", encoding="utf-8")

        monkeypatch.setattr("main.time.sleep", lambda _seconds: None)
        run_with_file_retries("write", tmp_path / "locked.md", flaky_write)

        assert attempts["count"] == 3
        assert (tmp_path / "locked.md").read_text(encoding="utf-8") == "ok"

    def test_missing_reference_dir_raises(self, tmp_path):
        with pytest.raises((FileNotFoundError, NotADirectoryError)):
            create_song_folder(
                song=self._basic_song(),
                template_dir=PROJECT_ROOT / "templates",
                output_dir=tmp_path / "output",
                reference_dir=tmp_path / "nonexistent_ref",
            )

    def test_build_song_prompt_overview_uses_generated_prompt_content(self, tmp_path, reference_dir):
        song = self._basic_song()
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        overview = build_song_prompt_overview(song, dest, [])
        assert "영상 설명" in overview
        assert "프롬프트별 영상 설명" in overview
        assert "03_vocal_image_prompt.md" in overview
        assert "보컬 클로즈업 장면" in overview
        assert "정상" in overview

    def test_summarize_prompt_outputs_writes_song_and_global_files(self, tmp_path, reference_dir):
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        input_file = input_dir / "Sample Song.txt"
        input_file.write_text(
            "Title: Sample Song\nGenre: indie pop\nBPM: 96 BPM\n\n[Verse]\nhello\n",
            encoding="utf-8",
        )
        song = parse_song(input_file, title_fallback=input_file.stem)
        output_dir = tmp_path / "output"
        create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=output_dir,
            reference_dir=reference_dir,
        )
        rows, written = summarize_prompt_outputs(input_dir, output_dir)
        assert len(rows) == 1
        assert rows[0]["status"] == "PASS"
        assert output_dir / ALL_OVERVIEW_FILE in written
        assert output_dir / PROMPT_AUDIT_FILE in written
        assert (output_dir / "Sample Song" / SONG_OVERVIEW_FILE).exists()

    def test_video_motion_signature_gestures_present(self, tmp_path, reference_dir):
        """09_video_motion_prompts.md 에 캐릭터 시그니처 동작이 포함되어 있어야 한다."""
        dest = create_song_folder(
            song=self._basic_song(),
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        text = (dest / "09_video_motion_prompts.md").read_text(encoding="utf-8")
        # 보컬 시그니처
        assert "left stylized hand holding the microphone stand close to the chest" in text
        assert "right stylized hand slowly pressing near the chest area between phrases" in text
        assert "head tilting slightly downward during emotional lines" in text
        # 기타 시그니처
        assert "weight shifted to the front foot, guitar angled slightly upward" in text
        assert "eyes closing during chord transitions, slight forward lean into the strings" in text
        # 베이스 시그니처
        assert "subtle groove-sway from the hips, eyes cast down watching the fretboard" in text
        assert "steady stylized nod on the beat" in text
        # 드럼 시그니처
        assert "one drumstick raised high between strikes, stylized wrist ready for the next beat" in text
        assert "leaning forward over the kit" in text

    def test_video_motion_kling_capcut_production_plan_present(self, tmp_path, reference_dir):
        """09_video_motion_prompts.md keeps the Kling multi-clip workflow."""
        dest = create_song_folder(
            song=self._basic_song(),
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        text = (dest / "09_video_motion_prompts.md").read_text(encoding="utf-8")
        assert "Kling Production Rule" in text
        assert "recommended 3-minute MV set" in text
        assert "recommended 4-minute MV set" in text
        assert "total: 26 clips" in text
        assert "total: 32 clips" in text
        assert "Motion Variants Per Image" in text
        assert "CapCut Editing Map" in text
        assert "Do not ask Kling to create all variants inside one generation" in text

    def test_subway_song_no_aggressive_residue(self, tmp_path, reference_dir):
        """subway/indie 곡에서 aggressive 잔여 문구가 남지 않는지 확인."""
        song = make_song(
            title="환승역테스트",
            genre="96 BPM emotional indie pop, subway ambience",
            mood="bittersweet nostalgic",
            emotion="lingering regret",
            tempo="96 BPM groove",
            stage_energy="restrained emotional indie live performance",
            lighting_style="soft neon magenta moonlight",
            camera_style="slow cinematic push-in",
            special_effects="drifting smoke",
            instruments="guitar, bass, subway ambience",
            sections=[Section(label="Chorus", note="", lines=["후렴 가사"])],
            raw_text="subway ambience 환승 열차 soft indie",
        )
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        for name in PROMPT_FILES:
            text = (dest / name).read_text(encoding="utf-8")
            assert "screams aggressively" not in text, f"{name} 에 aggressive 잔여"
            assert "headbanging" not in text, f"{name} 에 headbanging 잔여"


# ---------------------------------------------------------------------------
# 이미지 템플릿 잔여 표현 — soft / groove / retro / hiphop 장르 이미지 파일 검증
# ---------------------------------------------------------------------------

class TestImageResidueRemoval:
    """이미지 프롬프트(03~08)의 록/메탈 잔여 표현이 soft 장르에서 제거되는지 검증."""

    METAL_RESIDUES = [
        "dark synthwave metal concert atmosphere",
        "dark synthwave metal atmosphere",
        "fast energetic performance feeling",
        "dynamic low-angle camera shot",
        "smoke, sparks, laser beams, intense stage lighting",
        "powerful low-end concert atmosphere",
        "epic live concert scale",
        "epic festival-scale live performance atmosphere",
        "high contrast dark synthwave metal lighting",
        "flashing magenta lights, lasers, smoke, sparks",
        "powerful rhythm and impact",
        "heavy smoke and sparks around the vocalist",
    ]

    def _has_residue(self, text: str) -> list[str]:
        return [r for r in self.METAL_RESIDUES if r.lower() in text.lower()]

    def test_soft_rnb_image_files_no_metal_residue(self, tmp_path, reference_dir):
        """들리잖아 (R&B soft) 이미지 파일 03~08에 록/메탈 잔여 없어야 한다."""
        song = parse_song(PROJECT_ROOT / "input" / "들리잖아.txt")
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        image_prefixes = [f"0{n}_" for n in range(3, 9)]
        for name in PROMPT_FILES:
            if not any(name.startswith(p) for p in image_prefixes):
                continue
            text = (dest / name).read_text(encoding="utf-8")
            bad = self._has_residue(text)
            assert not bad, f"{name} 에 록/메탈 잔여 남음: {bad}"

    def test_soft_guitar_dark_synthwave_removed(self):
        s = make_song(raw_text="youth r&b heartbeat groove ballad")
        for residue in [
            "dark synthwave metal concert atmosphere,",
            "fast energetic performance feeling,",
            "smoke, sparks, laser beams, intense stage lighting,",
        ]:
            result = soften_aggressive_residue(residue, s)
            assert "metal" not in result.lower(), f"metal 잔여: {result}"
            assert result != residue, f"교체 안 됨: {residue}"

    def test_soft_stage_epic_scale_removed(self):
        s = make_song(raw_text="indie acoustic soft emotional ballad")
        for residue in ["epic live concert scale,", "dark synthwave metal atmosphere,"]:
            result = soften_aggressive_residue(residue, s)
            assert "metal" not in result.lower(), f"metal 잔여: {result}"
            assert result != residue, f"교체 안 됨: {residue}"

    def test_soft_crowd_flashing_lights_removed(self):
        s = make_song(raw_text="soft indie acoustic ballad emotional")
        for residue in [
            "flashing magenta lights, lasers, smoke, sparks,",
            "epic festival-scale live performance atmosphere,",
            "high contrast dark synthwave metal lighting,",
        ]:
            result = soften_aggressive_residue(residue, s)
            assert "metal" not in result.lower(), f"metal 잔여: {result}"
            assert result != residue, f"교체 안 됨: {residue}"

    def test_soft_drum_powerful_rhythm_removed(self):
        s = make_song(raw_text="ballad acoustic soft emotional")
        result = soften_aggressive_residue("powerful rhythm and impact,", s)
        assert "powerful" not in result.lower(), f"powerful 잔여: {result}"

    def test_soft_vocal_heavy_smoke_removed(self):
        s = make_song(raw_text="ballad acoustic soft emotional indie")
        result = soften_aggressive_residue("heavy smoke and sparks around the vocalist,", s)
        assert "heavy smoke and sparks" not in result.lower()

    def test_groove_image_residues_replaced(self):
        s = make_song(raw_text="afrobeats tropical house groovy")
        result = soften_aggressive_residue("dark synthwave metal concert atmosphere,", s)
        assert "metal" not in result.lower()
        assert "groove" in result.lower() or "vibrant" in result.lower()

    def test_retro_image_residues_replaced(self):
        s = make_song(raw_text="synth-pop new wave 80s retro")
        result = soften_aggressive_residue("fast energetic performance feeling,", s)
        assert "fast energetic" not in result.lower()
        assert "retro" in result.lower() or "dramatic" in result.lower()

    def test_hiphop_image_residues_replaced(self):
        s = make_song(raw_text="boom bap hip-hop industrial trap")
        result = soften_aggressive_residue("epic live concert scale,", s)
        assert "epic live" not in result.lower()
        assert "hip-hop" in result.lower() or "underground" in result.lower() or "raw" in result.lower()

    def test_rock_image_residues_preserved(self):
        """rock 장르는 이미지 잔여 표현이 그대로 유지되어야 한다."""
        s = make_song(raw_text="hard rock metal aggressive punk")
        for residue in [
            "dark synthwave metal concert atmosphere,",
            "fast energetic performance feeling,",
            "epic live concert scale,",
        ]:
            result = soften_aggressive_residue(residue, s)
            assert result == residue, f"rock 표현이 바뀌면 안 됨: {residue} -> {result}"

    def test_profile_first_overrides_keyword_fallback(self):
        """프로파일에 softening_type이 있으면 키워드 폴백을 건너뛴다."""
        # melodic_rap 프로파일(softening_type=soft)인데 raw_text에 'hip-hop' 키워드 포함 시
        # → soft 교체가 적용되어야 한다 (hiphop이 아닌)
        s = make_song(raw_text="melodic rap hip-hop late-night emotional")
        result = soften_aggressive_residue("crowd cheering wildly in the background,", s)
        # soft 교체 결과: "crowd phone lights shimmer quietly in the background,"
        assert "phone lights" in result or "quietly" in result, "soft 교체 미적용"
        assert "fists" not in result, "hiphop 교체가 잘못 적용됨"

    def test_profile_without_softening_type_uses_keyword_fallback(self):
        """프로파일에 softening_type이 없으면 키워드 폴백을 사용한다."""
        # hyper-pop 프로파일(softening_type=None), raw_text에 'soft' 키워드 없음
        s = make_song(raw_text="hyper-pop 128BPM dead dry staccato punchy")
        result = soften_aggressive_residue("dark synthwave metal concert atmosphere,", s)
        # soft/groove/retro/hiphop 키워드가 없으므로 교체 없음
        assert result == "dark synthwave metal concert atmosphere,", "교체가 발생하면 안 됨"


# ---------------------------------------------------------------------------
# is_inline_note_line / strip_inline_notes
# ---------------------------------------------------------------------------

class TestInlineNoteFilter:
    def test_production_note_detected(self):
        assert is_inline_note_line("[subway impact bass]") is True
        assert is_inline_note_line("[city night ambience]") is True
        assert is_inline_note_line("[heartbeat percussion]") is True
        assert is_inline_note_line("[cassette wobble]") is True

    def test_section_header_not_filtered(self):
        assert is_inline_note_line("[Intro]") is False
        assert is_inline_note_line("[Chorus]") is False
        assert is_inline_note_line("[Bridge: emotional climax]") is False
        assert is_inline_note_line("[Instrumental]") is False

    def test_normal_lyric_not_filtered(self):
        assert is_inline_note_line("들리잖아 내 심장 소리") is False
        assert is_inline_note_line("") is False

    def test_strip_removes_production_notes(self):
        text = "[city night ambience]\n들리잖아 내 심장 소리\n[subway impact bass]\n[Chorus]\n쿵 하고 울려"
        result = strip_inline_notes(text)
        assert "[city night ambience]" not in result
        assert "[subway impact bass]" not in result
        assert "[Chorus]" in result          # 섹션 헤더는 유지
        assert "심장 소리" in result
        assert "쿵 하고 울려" in result

    def test_strip_does_not_remove_section_headers(self):
        text = "[Intro]\n[subway chime]\n[Verse 1]\n가사"
        result = strip_inline_notes(text)
        assert "[Intro]" in result
        assert "[Verse 1]" in result
        assert "[subway chime]" not in result


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 들리잖아
# ---------------------------------------------------------------------------

class TestParseSongDeullijana:
    INPUT = PROJECT_ROOT / "input" / "들리잖아.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "들리잖아.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "들리잖아"

    def test_genre_parsed(self):
        song = parse_song(self.INPUT)
        assert "r&b" in song.genre.lower()
        assert "heartbeat groove" in song.genre.lower()

    def test_subway_bracket_note_does_not_pollute_profile(self):
        """[subway impact bass] 등 제작 주석이 subway 프로필을 유발하면 안 됨."""
        song = parse_song(self.INPUT)
        # subway 프로필 키워드가 mood/emotion/stage_energy에 없어야 함
        assert "subway transfer" not in song.mood
        assert "missed-stop nostalgia" not in song.emotion
        assert "subway pulse" not in song.stage_energy

    def test_rnb_profile_applied(self):
        song = parse_song(self.INPUT)
        assert "r&b" in song.stage_energy.lower() or "heartbeat" in song.stage_energy.lower()
        assert "heartbeat" in song.lighting_style.lower() or "city glow" in song.lighting_style.lower()

    def test_emotion_is_confession_type(self):
        song = parse_song(self.INPUT)
        assert "confession" in song.emotion.lower() or "heartbeat" in song.emotion.lower()

    def test_sections_parsed(self):
        song = parse_song(self.INPUT)
        labels = [s.label for s in song.sections]
        assert "Chorus" in labels
        assert "Bridge" in labels
        assert "Intro" in labels

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)

    def test_no_subway_residue_in_output(self, tmp_path, reference_dir):
        """subway 프로필 잔여가 들리잖아 출력에 없어야 함."""
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        subway_phrases = [
            "subway transfer station",
            "subway pulse percussion",
            "96 BPM bass pulse like distant train",
            "subway chime light pulses",
            "train window reflections",
        ]
        for name in PROMPT_FILES:
            text = (dest / name).read_text(encoding="utf-8")
            for phrase in subway_phrases:
                assert phrase not in text, f"{name} 에 subway 잔여: '{phrase}'"


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 다시 사랑해 줘
# ---------------------------------------------------------------------------

class TestParseSongDasiSaranghaeJwo:
    INPUT = PROJECT_ROOT / "input" / "다시 사랑해 줘.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "다시 사랑해 줘.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "다시 사랑해 줘"

    def test_genre_contains_soul_pop(self):
        song = parse_song(self.INPUT)
        assert "soul-pop" in song.genre.lower() or "soul pop" in song.genre.lower()

    def test_mood_is_soul_longing(self):
        """cinematic soul-pop 장르는 dark cinematic soul longing 무드여야 함."""
        song = parse_song(self.INPUT)
        assert "soul" in song.mood.lower()
        assert "longing" in song.mood.lower() or "heartbreak" in song.mood.lower()

    def test_emotion_is_desperate_longing(self):
        """갱망/이별 가사(못 놓아, 돌아와, 제발)는 desperate longing 감정이어야 함."""
        song = parse_song(self.INPUT)
        assert "longing" in song.emotion.lower() or "heartbreak" in song.emotion.lower()
        assert "confession" not in song.emotion.lower(), (
            "사랑해 줘 가사에서 confession 감정이 나오면 안 됨 (longing 우선)"
        )

    def test_stage_energy_is_soul_pop(self):
        song = parse_song(self.INPUT)
        assert "soul" in song.stage_energy.lower()

    def test_lighting_is_soul_pop(self):
        song = parse_song(self.INPUT)
        assert "soul" in song.lighting_style.lower() or "magenta" in song.lighting_style.lower()

    def test_piano_does_not_trigger_ballad_profile(self):
        """warm Rhodes piano 키워드 단독으로 ballad 프로필이 나오면 안 됨."""
        song = parse_song(self.INPUT)
        assert "minimal emotional" not in song.stage_energy, (
            "piano 가 ballad 오탐 유발 — 발라드 체크에서 piano 제거 필요"
        )
        assert "soft neon magenta moonlight, warm spotlight, gentle haze" not in song.lighting_style, (
            "piano 가 ballad 조명 오탐 유발"
        )

    def test_vocal_role_is_soul_power(self):
        song = parse_song(self.INPUT)
        roles = role_lines(song)
        assert "soul" in roles["vocal"].lower() or "heartbreak" in roles["vocal"].lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)

    def test_no_ballad_residue_in_output(self, tmp_path, reference_dir):
        """ballad 오탐 잔여가 출력에 없어야 함."""
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        ballad_phrases = [
            "minimal emotional live performance",
            "soft neon magenta moonlight, warm spotlight, gentle haze",
            "slow close-ups, steady emotional push-in, minimal wide shots",
            "singing softly and emotionally",
        ]
        for name in PROMPT_FILES:
            text = (dest / name).read_text(encoding="utf-8")
            for phrase in ballad_phrases:
                assert phrase not in text, f"{name} 에 ballad 오탐 잔여: '{phrase}'"


# ---------------------------------------------------------------------------
# infer_profile 단위 — soul-pop / longing / piano-not-ballad
# ---------------------------------------------------------------------------

class TestInferProfileSoulPop:
    def test_soul_pop_mood(self):
        s = make_song(raw_text="cinematic soul-pop dark soul anthem")
        profile = infer_profile(s.raw_text, {})
        assert "soul" in profile["mood"].lower()
        assert "longing" in profile["mood"].lower() or "heartbreak" in profile["mood"].lower()

    def test_soul_pop_stage_energy(self):
        s = make_song(raw_text="cinematic soul-pop stomp drums choir")
        profile = infer_profile(s.raw_text, {})
        assert "soul" in profile["stage_energy"].lower()
        assert "ballad" not in profile["stage_energy"].lower()

    def test_soul_pop_lighting(self):
        s = make_song(raw_text="dark soul anthem soul-pop")
        profile = infer_profile(s.raw_text, {})
        assert "soul" in profile["lighting_style"].lower()

    def test_longing_emotion_before_confession(self):
        """'못 놓아', '돌아와' 등 이별 키워드가 있으면 confession보다 longing이 우선."""
        s = make_song(raw_text="사랑 못 놓아 돌아와 제발 기다리잖아 soul-pop dark soul anthem")
        profile = infer_profile(s.raw_text, {})
        assert "longing" in profile["emotion"].lower() or "heartbreak" in profile["emotion"].lower()
        assert "confession" not in profile["emotion"].lower()

    def test_piano_alone_not_ballad(self):
        """'piano' 단어만으로 ballad stage_energy가 나오면 안 됨."""
        s = make_song(raw_text="warm Rhodes piano groove soul-pop")
        profile = infer_profile(s.raw_text, {})
        assert "minimal emotional" not in profile["stage_energy"], (
            "piano 단독으로 ballad 오탐"
        )

    def test_soul_pop_role_lines(self):
        s = make_song(raw_text="cinematic soul-pop dark soul anthem choir")
        roles = role_lines(s)
        assert "soul" in roles["vocal"].lower() or "heartbreak" in roles["vocal"].lower()
        assert "choir" not in roles["vocal"].lower() or "soul" in roles["vocal"].lower()


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 멈출 수 없어 (Hyper-pop)
# ---------------------------------------------------------------------------

class TestParseSongMeomchulSuEomseo:
    INPUT = PROJECT_ROOT / "input" / "멈출 수 없어.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "멈출 수 없어.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "멈출 수 없어"

    def test_genre_contains_hyperpop(self):
        song = parse_song(self.INPUT)
        assert "hyper" in song.genre.lower()

    def test_mood_is_hyperpop(self):
        """hyper-pop 장르는 high-energy/punchy 무드여야 함."""
        song = parse_song(self.INPUT)
        assert "high-energy" in song.mood.lower() or "punchy" in song.mood.lower()

    def test_stage_energy_is_hyperpop(self):
        song = parse_song(self.INPUT)
        assert "hyperpop" in song.stage_energy.lower() or "high-energy" in song.stage_energy.lower()

    def test_acoustics_does_not_trigger_ballad(self):
        """'Dead dry acoustics' 섹션 헤더가 ballad 프로필을 유발하면 안 됨."""
        song = parse_song(self.INPUT)
        assert "minimal emotional" not in song.stage_energy, (
            "acoustics 서브스트링이 ballad stage_energy 오탐 — acoustic guitar 로 수정 필요"
        )
        assert "slow close-ups, steady emotional push-in, minimal wide shots" not in song.camera_style, (
            "acoustics 가 ballad camera 오탐"
        )

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 첫 번째 봄 (subway 감정 오탐 방지)
# ---------------------------------------------------------------------------

class TestParseSongCheotBeonjjaeBom:
    INPUT = PROJECT_ROOT / "input" / "첫 번째 봄.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "첫 번째 봄.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "첫 번째 봄"

    def test_subway_emotion_not_triggered_by_후회(self):
        """'후회는 없어' 가사가 subway/reunion 감정을 유발하면 안 됨."""
        song = parse_song(self.INPUT)
        assert "missed-stop nostalgia" not in song.emotion, (
            "'후회' 키워드가 subway 감정 오탐 — emotion 체크에서 '후회' 제거 필요"
        )
        assert "unexpected reunion" not in song.emotion

    def test_mood_is_romantic_or_dreamy(self):
        """첫사랑 노래 → 첫사랑/사랑 키워드로 romantic/dreamy 무드여야 함."""
        song = parse_song(self.INPUT)
        assert "romantic" in song.mood.lower() or "dreamy" in song.mood.lower() or "intimate" in song.mood.lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 오늘도 네 곁을 맴돌아 (dance-pop)
# ---------------------------------------------------------------------------

class TestParseSongONeuoldoNe:
    INPUT = PROJECT_ROOT / "input" / "오늘도 네 곁을 맴돌아.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "오늘도 네 곁을 맴돌아.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "오늘도 네 곁을 맴돌아"

    def test_mood_is_dance_pop(self):
        song = parse_song(self.INPUT)
        assert "dance" in song.mood.lower() or "bittersweet" in song.mood.lower()

    def test_stage_energy_is_dance_pop(self):
        song = parse_song(self.INPUT)
        assert "dance" in song.stage_energy.lower() or "club" in song.stage_energy.lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# infer_profile 단위 — hyper-pop / dance-pop / indie / 후회 비subway
# ---------------------------------------------------------------------------

class TestInferProfileNewGenres:
    def test_hyperpop_mood(self):
        s = make_song(raw_text="hyper-pop 128BPM dead dry staccato synth")
        profile = infer_profile(s.raw_text, {})
        assert "high-energy" in profile["mood"].lower() or "punchy" in profile["mood"].lower()

    def test_hyperpop_stage_energy(self):
        s = make_song(raw_text="hyper-pop hyperpop vacuum tight punchy")
        profile = infer_profile(s.raw_text, {})
        assert "hyperpop" in profile["stage_energy"].lower()

    def test_dance_pop_mood(self):
        s = make_song(raw_text="dance pop future house 124 BPM melancholic")
        profile = infer_profile(s.raw_text, {})
        assert "dance" in profile["mood"].lower() or "bittersweet" in profile["mood"].lower()

    def test_dance_pop_stage_energy(self):
        s = make_song(raw_text="dance-pop future house groovy club emotional")
        profile = infer_profile(s.raw_text, {})
        assert "dance" in profile["stage_energy"].lower() or "club" in profile["stage_energy"].lower()

    def test_indie_lighting(self):
        s = make_song(raw_text="indie bedroom pop dreamy warm alternative")
        profile = infer_profile(s.raw_text, {})
        assert "indie" in profile["lighting_style"].lower() or "dreamy" in profile["lighting_style"].lower()

    def test_indie_role_lines(self):
        s = make_song(raw_text="indie bedroom pop warm intimate")
        roles = role_lines(s)
        assert "indie" in roles["vocal"].lower() or "intimate" in roles["vocal"].lower()

    def test_후회_alone_does_not_trigger_subway_emotion(self):
        """'후회' 단어 하나로 subway/reunion 감정이 나오면 안 됨."""
        s = make_song(raw_text="후회는 없어 부드러운 한숨만 ballad acoustic piano")
        profile = infer_profile(s.raw_text, {})
        assert "missed-stop nostalgia" not in profile["emotion"]
        assert "unexpected reunion" not in profile["emotion"]

    def test_acoustics_not_ballad(self):
        """'dead dry acoustics' 단어가 ballad stage_energy를 유발하면 안 됨."""
        s = make_song(raw_text="hyper-pop dead dry acoustics 128BPM staccato")
        profile = infer_profile(s.raw_text, {})
        assert "minimal emotional" not in profile["stage_energy"]


# ---------------------------------------------------------------------------
# genre_profiles.json 구조 검증
# ---------------------------------------------------------------------------

class TestGenreProfilesJson:
    REQUIRED_PROFILE_FIELDS = {"name", "keywords", "stage_energy", "lighting_style", "camera_style", "special_effects", "roles"}
    REQUIRED_ROLE_KEYS = {"vocal", "vocal_action", "guitar", "bass", "drum", "crowd", "stage"}
    REQUIRED_DEFAULT_FIELDS = {"mood", "emotion", "stage_energy", "lighting_style", "camera_style", "special_effects", "roles"}

    def test_json_file_exists(self):
        assert GENRE_PROFILES_PATH.exists(), "genre_profiles.json 파일 없음"

    def test_json_is_valid(self):
        data = json.loads(GENRE_PROFILES_PATH.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_required_top_level_keys(self):
        assert "profiles" in _GENRE_DATA
        assert "mood_rules" in _GENRE_DATA
        assert "emotion_rules" in _GENRE_DATA
        assert "defaults" in _GENRE_DATA

    def test_each_profile_has_required_fields(self):
        for p in _GENRE_DATA["profiles"]:
            missing = self.REQUIRED_PROFILE_FIELDS - p.keys()
            assert not missing, f"프로필 '{p.get('name')}' 누락 필드: {missing}"

    def test_each_profile_roles_has_required_keys(self):
        for p in _GENRE_DATA["profiles"]:
            missing = self.REQUIRED_ROLE_KEYS - p["roles"].keys()
            assert not missing, f"프로필 '{p['name']}' roles 누락 키: {missing}"

    def test_each_profile_keywords_nonempty(self):
        for p in _GENRE_DATA["profiles"]:
            assert p["keywords"], f"프로필 '{p['name']}' keywords 비어 있음"

    def test_mood_rules_have_keywords_and_mood(self):
        for rule in _GENRE_DATA["mood_rules"]:
            assert "keywords" in rule and rule["keywords"]
            assert "mood" in rule and rule["mood"]

    def test_emotion_rules_have_keywords_and_emotion(self):
        for rule in _GENRE_DATA["emotion_rules"]:
            assert "keywords" in rule and rule["keywords"]
            assert "emotion" in rule and rule["emotion"]

    def test_defaults_has_required_fields(self):
        missing = self.REQUIRED_DEFAULT_FIELDS - _GENRE_DATA["defaults"].keys()
        assert not missing, f"defaults 누락 필드: {missing}"

    def test_defaults_roles_has_required_keys(self):
        missing = self.REQUIRED_ROLE_KEYS - _GENRE_DATA["defaults"]["roles"].keys()
        assert not missing, f"defaults roles 누락 키: {missing}"

    def test_no_duplicate_profile_names(self):
        names = [p["name"] for p in _GENRE_DATA["profiles"]]
        assert len(names) == len(set(names)), f"중복 프로필 이름: {names}"

    def test_genre_data_loaded_at_module_level(self):
        assert _GENRE_DATA is not None
        assert isinstance(_GENRE_DATA["profiles"], list)
        assert len(_GENRE_DATA["profiles"]) >= 13

    def test_new_genre_profiles_present(self):
        names = [p["name"] for p in _GENRE_DATA["profiles"]]
        for expected in ["afrobeats", "synth-pop", "house", "hip-hop", "jazz", "lo-fi", "psychedelic",
                         "neo-soul", "folk", "ambient"]:
            assert expected in names, f"신규 장르 프로필 없음: {expected}"

    def test_subway_keywords_no_train(self):
        """subway 프로파일에 'train' 키워드가 없어야 함 — restrained/strained 오탐 방지."""
        subway = next(p for p in _GENRE_DATA["profiles"] if p["name"] == "subway")
        assert "train" not in subway["keywords"], "'train' 키워드가 subway에 남아 있음 — 오탐 원인"

    def test_restrained_does_not_trigger_subway(self):
        """'restrained vocal delivery' 등 제작 주석이 subway 프로파일을 유발하면 안 됨."""
        s = make_song(raw_text="lo-fi k-indie, male hushed intimate vocals, restrained vocal delivery, warm acoustic")
        profile = infer_profile(s.raw_text, {})
        assert "subway" not in profile["stage_energy"].lower(), "'restrained'가 subway 프로파일 오탐"
        assert "train" not in profile["stage_energy"].lower()

    def test_strained_does_not_trigger_subway(self):
        """'emotional strain' 등 영어 단어의 'train' 부분 문자열 오탐 방지."""
        s = make_song(raw_text="boom bap hip hop, emotional strain, building tension, male vocal")
        profile = infer_profile(s.raw_text, {})
        assert "subway" not in profile["stage_energy"].lower(), "'strain' 속 'train'이 subway 오탐"

    def test_ambient_song_not_subway(self):
        """ambient 장르 곡은 subway 프로파일로 오탐되면 안 됨 (train 제거로 해결)."""
        s = make_song(raw_text="indie folktronica, cinematic winter ost, ambient, modern minimalist, lo-fi aesthetic")
        profile = infer_profile(s.raw_text, {})
        assert "subway" not in profile["stage_energy"].lower(), "ambient 곡이 subway 프로파일 오탐"


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 그 소녀 (Afrobeats)
# ---------------------------------------------------------------------------

class TestParseSongGeuSonyeo:
    INPUT = PROJECT_ROOT / "input" / "그 소녀.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "그 소녀.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "그 소녀"

    def test_genre_contains_afrobeats(self):
        song = parse_song(self.INPUT)
        assert "afrobeats" in song.genre.lower()

    def test_mood_is_afrobeats(self):
        song = parse_song(self.INPUT)
        assert "joyful" in song.mood.lower() or "groove" in song.mood.lower() or "afrobeats" in song.mood.lower()

    def test_stage_energy_is_afrobeats(self):
        song = parse_song(self.INPUT)
        assert "afrobeats" in song.stage_energy.lower()

    def test_drum_role_is_polyrhythmic(self):
        song = parse_song(self.INPUT)
        roles = role_lines(song)
        assert "afrobeats" in roles["drum"].lower() or "polyrhythmic" in roles["drum"].lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 남겨진 우산 (80s Synth-pop)
# ---------------------------------------------------------------------------

class TestParseSongNamgyeojinUsan:
    INPUT = PROJECT_ROOT / "input" / "남겨진 우산.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "남겨진 우산.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "남겨진 우산"

    def test_genre_contains_synth_pop(self):
        song = parse_song(self.INPUT)
        assert "synth" in song.genre.lower() or "80s" in song.genre.lower()

    def test_mood_is_synth_pop(self):
        song = parse_song(self.INPUT)
        assert "retro" in song.mood.lower() or "80s" in song.mood.lower() or "yearning" in song.mood.lower()

    def test_stage_energy_is_synth_pop(self):
        song = parse_song(self.INPUT)
        assert "synth-pop" in song.stage_energy.lower() or "80s" in song.stage_energy.lower()

    def test_lighting_has_neon_grid(self):
        song = parse_song(self.INPUT)
        assert "neon" in song.lighting_style.lower() or "grid" in song.lighting_style.lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 기억나 (House/Tropical House)
# ---------------------------------------------------------------------------

class TestParseSongGieongna:
    INPUT = PROJECT_ROOT / "input" / "기억나.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "기억나.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "기억나"

    def test_genre_contains_house(self):
        song = parse_song(self.INPUT)
        assert "tropical" in song.genre.lower() or "acid" in song.genre.lower() or "house" in song.genre.lower()

    def test_stage_energy_and_lighting_are_house(self):
        """mood는 가사 내 '사랑' 키워드로 재정의될 수 있음 — stage_energy/lighting으로 house 프로필 확인."""
        song = parse_song(self.INPUT)
        assert "club" in song.stage_energy.lower() or "house" in song.stage_energy.lower()
        assert "club" in song.lighting_style.lower() or "laser" in song.lighting_style.lower()

    def test_stage_energy_is_house(self):
        song = parse_song(self.INPUT)
        assert "club" in song.stage_energy.lower() or "house" in song.stage_energy.lower()

    def test_drum_role_has_four_on_the_floor(self):
        song = parse_song(self.INPUT)
        roles = role_lines(song)
        assert "club" in roles["drum"].lower() or "four-on-the-floor" in roles["drum"].lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 오후의 여백 (90s Boom Bap Hip-hop)
# ---------------------------------------------------------------------------

class TestParseSongOhuhYeobaek:
    INPUT = PROJECT_ROOT / "input" / "오후의 여백.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "오후의 여백.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "오후의 여백"

    def test_genre_contains_hip_hop(self):
        song = parse_song(self.INPUT)
        assert "boom bap" in song.genre.lower() or "hip" in song.genre.lower()

    def test_mood_is_hip_hop(self):
        song = parse_song(self.INPUT)
        assert "urban" in song.mood.lower() or "raw" in song.mood.lower() or "power" in song.mood.lower()

    def test_stage_energy_is_hip_hop(self):
        song = parse_song(self.INPUT)
        assert "hip-hop" in song.stage_energy.lower() or "hip hop" in song.stage_energy.lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# infer_profile 단위 — 신규 장르 4종
# ---------------------------------------------------------------------------

class TestInferProfileNewGenres2:
    def test_afrobeats_mood(self):
        s = make_song(raw_text="afrobeats polyrhythmic groove 100 BPM")
        profile = infer_profile(s.raw_text, {})
        assert "joyful" in profile["mood"].lower() or "afrobeats" in profile["mood"].lower()

    def test_afrobeats_stage_energy(self):
        s = make_song(raw_text="afrobeats tropical groove")
        profile = infer_profile(s.raw_text, {})
        assert "afrobeats" in profile["stage_energy"].lower()

    def test_synth_pop_mood(self):
        s = make_song(raw_text="synth-pop new wave 80s retro analog")
        profile = infer_profile(s.raw_text, {})
        assert "retro" in profile["mood"].lower() or "80s" in profile["mood"].lower()

    def test_synth_pop_lighting_has_neon_grid(self):
        s = make_song(raw_text="synth-pop 1980s synth gated reverb")
        profile = infer_profile(s.raw_text, {})
        assert "neon" in profile["lighting_style"].lower() or "grid" in profile["lighting_style"].lower()

    def test_house_stage_energy(self):
        s = make_song(raw_text="tropical house acid house 105 BPM club groove")
        profile = infer_profile(s.raw_text, {})
        assert "club" in profile["stage_energy"].lower() or "house" in profile["stage_energy"].lower()

    def test_house_mood_euphoric(self):
        s = make_song(raw_text="groovy house nu-disco dance floor energy")
        profile = infer_profile(s.raw_text, {})
        assert "club" in profile["mood"].lower() or "euphoric" in profile["mood"].lower()

    def test_hip_hop_stage_energy(self):
        s = make_song(raw_text="90s boom bap jazzy hip hop heavy kick snare")
        profile = infer_profile(s.raw_text, {})
        assert "hip-hop" in profile["stage_energy"].lower() or "hip hop" in profile["stage_energy"].lower()

    def test_hip_hop_mood(self):
        s = make_song(raw_text="boom bap hard hitting hip-hop urban")
        profile = infer_profile(s.raw_text, {})
        assert "urban" in profile["mood"].lower() or "power" in profile["mood"].lower()

    def test_city_pop_maps_to_citypop(self):
        s = make_song(raw_text="city pop 124 BPM funky upbeat easy listening")
        profile = infer_profile(s.raw_text, {})
        assert "city" in profile["stage_energy"].lower() or "groove" in profile["stage_energy"].lower()

    def test_nu_disco_maps_to_house(self):
        s = make_song(raw_text="nu-disco funky disco-pop chic female vocals")
        profile = infer_profile(s.raw_text, {})
        assert "club" in profile["stage_energy"].lower() or "house" in profile["stage_energy"].lower()

    def test_trap_maps_to_hip_hop(self):
        # 'aggressive'는 rock 키워드이므로 제외 — trap/hip-hop 키워드만 사용
        s = make_song(raw_text="dark industrial trap heavy 808 bass hip-hop")
        profile = infer_profile(s.raw_text, {})
        assert "hip-hop" in profile["stage_energy"].lower() or "hip hop" in profile["stage_energy"].lower()

    def test_signal_pop_stage_energy(self):
        s = make_song(
            raw_text=(
                "korean signal pop warm male vocal ajaeng lead "
                "telephone pulse rhythm minimal drums spacious uplifting atmosphere"
            )
        )
        profile = infer_profile(s.raw_text, {})
        assert "telephone-signal-pop" in profile["stage_energy"].lower()
        assert "song-matched live performance" not in profile["stage_energy"].lower()

    def test_signal_pop_mood(self):
        s = make_song(raw_text="telephone connection tone ajaeng motif signal pop")
        profile = infer_profile(s.raw_text, {})
        assert "telephone-signal-pop" in profile["mood"].lower() or "telephone pulse" in profile["mood"].lower()

    def test_afrobeats_role_lines(self):
        s = make_song(raw_text="afrobeats groove polyrhythmic percussion")
        roles = role_lines(s)
        assert "afrobeats" in roles["vocal"].lower() or "groove" in roles["vocal"].lower()

    def test_synth_pop_role_lines(self):
        s = make_song(raw_text="synth-pop new wave 80s retro")
        roles = role_lines(s)
        assert "80s" in roles["vocal"].lower() or "synth" in roles["vocal"].lower()

    def test_house_role_lines(self):
        s = make_song(raw_text="tropical house groovy club dance floor")
        roles = role_lines(s)
        assert "club" in roles["vocal"].lower() or "euphoric" in roles["vocal"].lower()

    def test_hip_hop_role_lines(self):
        s = make_song(raw_text="boom bap hip-hop hard hitting rap flow")
        roles = role_lines(s)
        assert "hip-hop" in roles["vocal"].lower() or "rap" in roles["vocal"].lower()


# ---------------------------------------------------------------------------
# infer_profile 단위 — neo-soul / folk / ambient (신규 3종)
# ---------------------------------------------------------------------------

class TestInferProfileNewGenres4:
    def test_neosoul_profile_matched(self):
        s = make_song(raw_text="neo-soul warm groove 90 BPM soulful male vocals")
        profile = infer_profile(s.raw_text, {})
        assert "neo-soul" in profile["stage_energy"].lower() or "soulful" in profile["stage_energy"].lower()

    def test_neosoul_stage_energy(self):
        s = make_song(raw_text="neo-soul organic groove warm soulful")
        profile = infer_profile(s.raw_text, {})
        assert "neo-soul" in profile["stage_energy"].lower() or "soulful" in profile["stage_energy"].lower()

    def test_neosoul_lighting_warm_amber(self):
        s = make_song(raw_text="neo soul warm groove vintage soulful")
        profile = infer_profile(s.raw_text, {})
        assert "amber" in profile["lighting_style"].lower() or "soul" in profile["lighting_style"].lower()

    def test_neosoul_no_rock_residue(self):
        s = make_song(raw_text="neo-soul warm organic groove")
        profile = infer_profile(s.raw_text, {})
        assert "headbanging" not in profile["stage_energy"].lower()
        assert "screams" not in profile["stage_energy"].lower()

    def test_neosoul_role_lines(self):
        s = make_song(raw_text="neo-soul groove soulful warm")
        roles = role_lines(s)
        assert "neo-soul" in roles["vocal"].lower() or "soulful" in roles["vocal"].lower()

    def test_folk_profile_matched(self):
        s = make_song(raw_text="folk acoustic singer-songwriter 75 BPM fingerstyle guitar")
        profile = infer_profile(s.raw_text, {})
        assert "folk" in profile["stage_energy"].lower() or "acoustic" in profile["stage_energy"].lower()

    def test_neofolk_profile_matched(self):
        s = make_song(raw_text="neo-folk warm acoustic indie pop fingerstyle guitar")
        profile = infer_profile(s.raw_text, {})
        assert "folk" in profile["stage_energy"].lower() or "acoustic" in profile["stage_energy"].lower()

    def test_folk_stage_energy_acoustic(self):
        s = make_song(raw_text="folk acoustic earthy storytelling")
        profile = infer_profile(s.raw_text, {})
        assert "acoustic" in profile["stage_energy"].lower() or "folk" in profile["stage_energy"].lower()

    def test_folk_lighting_warm(self):
        s = make_song(raw_text="folk singer-songwriter warm acoustic")
        profile = infer_profile(s.raw_text, {})
        assert "warm" in profile["lighting_style"].lower() or "folk" in profile["lighting_style"].lower()

    def test_folk_role_lines(self):
        s = make_song(raw_text="folk singer-songwriter intimate acoustic")
        roles = role_lines(s)
        assert "folk" in roles["vocal"].lower() or "storytelling" in roles["vocal"].lower()

    def test_ambient_profile_matched(self):
        s = make_song(raw_text="ambient 70 BPM slow atmospheric floating ethereal")
        profile = infer_profile(s.raw_text, {})
        assert "minimal" in profile["stage_energy"].lower() or "atmospheric" in profile["stage_energy"].lower()

    def test_ambient_stage_energy_minimal(self):
        s = make_song(raw_text="ambient floating atmospheric minimal")
        profile = infer_profile(s.raw_text, {})
        assert "minimal" in profile["stage_energy"].lower() or "atmospheric" in profile["stage_energy"].lower()

    def test_ambient_camera_static(self):
        s = make_song(raw_text="ambient atmospheric slow floating")
        profile = infer_profile(s.raw_text, {})
        assert "static" in profile["camera_style"].lower() or "drift" in profile["camera_style"].lower()

    def test_ambient_not_triggered_by_indie_songs(self):
        """indie + ambient synths 조합은 indie 프로필이 우선이어야 함."""
        s = make_song(raw_text="dreamy indie pop bedroom pop ambient synths warm guitar")
        profile = infer_profile(s.raw_text, {})
        assert "indie" in profile["stage_energy"].lower() or "dreamy" in profile["lighting_style"].lower()

    def test_lofi_neosoul_stays_lofi(self):
        """lo-fi hip-hop + neo-soul 조합은 lo-fi 프로필이 우선이어야 함."""
        s = make_song(raw_text="lo-fi hip hop neo-soul mellow cassette warm study beats")
        profile = infer_profile(s.raw_text, {})
        assert "lo-fi" in profile["stage_energy"].lower() or "cassette" in profile["stage_energy"].lower()

    def test_neosoul_role_vocal_action(self):
        s = make_song(raw_text="neo-soul warm groove soulful vocals")
        roles = role_lines(s)
        assert roles.get("vocal_action", "") != ""

    def test_folk_role_vocal_action(self):
        s = make_song(raw_text="folk singer-songwriter acoustic warm")
        roles = role_lines(s)
        assert roles.get("vocal_action", "") != ""

    def test_ambient_role_vocal_action(self):
        s = make_song(raw_text="ambient atmospheric floating minimal")
        roles = role_lines(s)
        assert roles.get("vocal_action", "") != ""


# ---------------------------------------------------------------------------
# vocal_action — 장르별 보컬 액션 단위 테스트
# ---------------------------------------------------------------------------

class TestVocalAction:
    """각 장르 프로필의 vocal_action이 장르 특성에 맞는지 검증."""

    def _get_vocal_action(self, raw_text: str) -> str:
        s = make_song(raw_text=raw_text)
        return role_lines(s).get("vocal_action", "")

    def test_all_profiles_have_vocal_action(self):
        for p in _GENRE_DATA["profiles"]:
            assert "vocal_action" in p["roles"], f"프로필 '{p['name']}' vocal_action 없음"

    def test_defaults_has_vocal_action(self):
        assert "vocal_action" in _GENRE_DATA["defaults"]["roles"]

    def test_ballad_presses_to_rib_cage(self):
        action = self._get_vocal_action("ballad acoustic gentle")
        assert "chest" in action.lower() or "bowed" in action.lower()

    def test_hip_hop_pointing_gesture(self):
        action = self._get_vocal_action("boom bap hip-hop rap flow")
        assert "gesture" in action.lower() or "pointing" in action.lower()

    def test_dance_pop_hips_extending(self):
        action = self._get_vocal_action("dance pop future house groovy club")
        assert "hips" in action.lower() or "extending" in action.lower() or "crowd" in action.lower()

    def test_rnb_trembling_heart(self):
        action = self._get_vocal_action("r&b heartbeat groove confession")
        assert "trembling" in action.lower() or "heart" in action.lower()

    def test_soul_pop_raised_high(self):
        action = self._get_vocal_action("cinematic soul-pop dark soul anthem")
        assert "raised" in action.lower() or "upward" in action.lower()

    def test_indie_eyes_closed(self):
        action = self._get_vocal_action("indie bedroom pop dreamy warm")
        assert "eyes closed" in action.lower() or "resting" in action.lower()

    def test_rock_defiant_stance(self):
        action = self._get_vocal_action("rock metal aggressive live")
        assert "stance" in action.lower() or "gripping" in action.lower()

    def test_subway_distant_gaze(self):
        action = self._get_vocal_action("subway train emotional indie pop 환승")
        assert "gaze" in action.lower() or "tracing" in action.lower()

    def test_hyper_pop_head_jerking(self):
        action = self._get_vocal_action("hyper-pop hyperpop staccato")
        assert "snapping" in action.lower() or "jerking" in action.lower()

    def test_synth_pop_theatrical(self):
        action = self._get_vocal_action("synth-pop new wave 80s retro")
        assert "theatrical" in action.lower() or "sweeping" in action.lower()

    def test_afrobeats_swaying(self):
        action = self._get_vocal_action("afrobeats polyrhythmic groove")
        assert "swaying" in action.lower() or "rocking" in action.lower()

    def test_house_pulsing_beat(self):
        action = self._get_vocal_action("tropical house groovy club floor")
        assert "pulsing" in action.lower() or "reaching" in action.lower()

    def test_pop_rap_head_bob(self):
        action = self._get_vocal_action("pop rap melodic rap smooth groove 힘들")
        assert "head bob" in action.lower() or "gesturing" in action.lower()

    def test_vocal_action_injected_into_03_vocal_prompt(self, tmp_path, reference_dir):
        """03_vocal_image_prompt.md 출력에 vocal_action 문구가 포함되어야 한다."""
        song = make_song(
            title="테스트발라드",
            genre="ballad acoustic",
            raw_text="ballad acoustic gentle",
            sections=[Section(label="Verse", note="", lines=["가사"])],
        )
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        text = (dest / "03_vocal_image_prompt.md").read_text(encoding="utf-8")
        assert "chest" in text.lower() or "bowed" in text.lower(), \
            "ballad vocal_action이 03_vocal 출력에 없음"

    def test_vocal_action_hip_hop_in_03_prompt(self, tmp_path, reference_dir):
        """hip-hop 03_vocal 출력에 pointing/gesture 문구가 포함되어야 한다."""
        song = make_song(
            title="테스트힙합",
            genre="boom bap hip-hop",
            raw_text="boom bap hip-hop rap flow 90 BPM",
            sections=[Section(label="Verse", note="", lines=["랩 가사"])],
        )
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        text = (dest / "03_vocal_image_prompt.md").read_text(encoding="utf-8")
        assert "pointing" in text.lower() or "gesture" in text.lower(), \
            "hip-hop vocal_action이 03_vocal 출력에 없음"

    def test_vocal_action_dance_pop_in_03_prompt(self, tmp_path, reference_dir):
        """dance-pop 03_vocal 출력에 hips/extending 문구가 포함되어야 한다."""
        song = make_song(
            title="테스트댄스팝",
            genre="dance pop future house",
            raw_text="dance-pop future house 124 BPM groovy club",
            sections=[Section(label="Chorus", note="", lines=["후렴"])],
        )
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        text = (dest / "03_vocal_image_prompt.md").read_text(encoding="utf-8")
        assert "hips" in text.lower() or "extending" in text.lower(), \
            "dance-pop vocal_action이 03_vocal 출력에 없음"

    def test_no_placeholder_after_vocal_action_injection(self, tmp_path, reference_dir):
        """vocal_action 주입 후에도 placeholder가 남지 않아야 한다."""
        song = parse_song(PROJECT_ROOT / "input" / "들리잖아.txt")
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# soften_aggressive_residue — 신규 장르 4종 residue 처리 테스트
# ---------------------------------------------------------------------------

class TestSoftenResidueNewGenres:
    """신규 장르 groove / retro / hip-hop residue 교체 검증."""

    def _song(self, raw_text: str) -> Song:
        return make_song(raw_text=raw_text)

    # ── groove (afrobeats / house) ──────────────────────────────────────────

    def test_groove_replaces_headbanging(self):
        s = self._song("afrobeats polyrhythmic 100 BPM")
        text = "crowd silhouettes raising hands, headbanging, cheering wildly, sparks flying,"
        result = soften_aggressive_residue(text, s)
        assert "headbanging" not in result
        assert "groove" in result.lower() or "infectious" in result.lower()

    def test_groove_replaces_sparks_flying(self):
        s = self._song("tropical house acid house 105 BPM")
        result = soften_aggressive_residue("sparks flying,", s)
        assert "sparks flying" not in result
        assert "golden" in result.lower() or "particle" in result.lower()

    def test_groove_replaces_intense_energy(self):
        s = self._song("groovy house nu-disco funky")
        result = soften_aggressive_residue("intense live performance energy,", s)
        assert "intense live" not in result
        assert "groove" in result.lower()

    def test_groove_replaces_massive_cyberpunk(self):
        s = self._song("afrobeats tropical groove 100 BPM")
        result = soften_aggressive_residue("massive cyberpunk concert atmosphere,", s)
        assert "massive cyberpunk" not in result
        assert "groove" in result.lower() or "vibrant" in result.lower()

    # ── retro synth-pop ─────────────────────────────────────────────────────

    def test_retro_replaces_headbanging(self):
        s = self._song("synth-pop new wave 80s retro 124 BPM")
        text = "crowd silhouettes raising hands, headbanging, cheering wildly,"
        result = soften_aggressive_residue(text, s)
        assert "headbanging" not in result
        assert "retro" in result.lower() or "80s" in result.lower()

    def test_retro_replaces_sparks_with_scan_line(self):
        s = self._song("synth-pop retro electronics 124 BPM")
        result = soften_aggressive_residue("sparks flying,", s)
        assert "sparks flying" not in result
        assert "retro" in result.lower() or "scan" in result.lower()

    def test_retro_replaces_intense_energy(self):
        s = self._song("1980s synth-pop new wave yearning")
        result = soften_aggressive_residue("intense live performance energy,", s)
        assert "intense live" not in result
        assert "dramatic" in result.lower() or "retro" in result.lower()

    def test_retro_replaces_magenta_lights(self):
        s = self._song("synth-pop 80s retro scan-line")
        result = soften_aggressive_residue("magenta concert lights flashing,", s)
        assert "flashing" not in result
        assert "cyan" in result.lower() or "retro" in result.lower() or "pulsing" in result.lower()

    # ── hip-hop ─────────────────────────────────────────────────────────────

    def test_hiphop_replaces_headbanging(self):
        s = self._song("boom bap hip-hop 90 BPM jazzy")
        text = "crowd silhouettes raising hands, headbanging, cheering wildly,"
        result = soften_aggressive_residue(text, s)
        assert "headbanging" not in result
        assert "hip-hop" in result.lower() or "fist" in result.lower()

    def test_hiphop_replaces_crowd_cheering(self):
        s = self._song("hip-hop boom bap hard hitting")
        result = soften_aggressive_residue("crowd cheering wildly in the background,", s)
        assert "cheering wildly" not in result
        assert "fist" in result.lower() or "hype" in result.lower() or "raised" in result.lower()

    def test_hiphop_replaces_camera_push_in(self):
        s = self._song("industrial trap hip-hop 95 BPM")
        result = soften_aggressive_residue("dramatic front-facing camera push-in,", s)
        assert "dramatic front-facing" not in result
        assert "hip-hop" in result.lower() or "low-angle" in result.lower()

    # ── 기존 soft 장르 회귀 ──────────────────────────────────────────────────

    def test_soft_still_replaces_headbanging(self):
        """기존 soft 처리가 신규 장르 추가 후에도 정상 동작해야 함."""
        s = self._song("ballad acoustic guitar soft emotional")
        text = "crowd silhouettes raising hands, headbanging, cheering wildly,"
        result = soften_aggressive_residue(text, s)
        assert "headbanging" not in result
        assert "phone lights" in result.lower() or "swaying" in result.lower()

    def test_soft_still_replaces_sparks(self):
        s = self._song("indie bedroom pop dreamy soft lo-fi")
        result = soften_aggressive_residue("sparks flying,", s)
        assert "sparks flying" not in result
        assert "glowing" in result.lower() or "particles" in result.lower()

    def test_rock_unchanged(self):
        """rock 장르는 어떤 residue 처리도 받지 않아야 한다."""
        s = self._song("hard rock metal aggressive punk")
        text = "sparks flying, crowd cheering wildly in the background, intense live performance energy,"
        result = soften_aggressive_residue(text, s)
        assert result == text

    # ── 실제 파일 통합 ────────────────────────────────────────────────────────

    def test_afrobeats_song_no_headbanging_in_output(self, tmp_path, reference_dir):
        """그 소녀 (afrobeats) 출력 전체에 headbanging이 없어야 한다."""
        song = parse_song(PROJECT_ROOT / "input" / "그 소녀.txt")
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        for name in PROMPT_FILES:
            text = (dest / name).read_text(encoding="utf-8")
            assert "headbanging" not in text, f"{name} 에 headbanging 잔여"

    def test_synth_pop_song_no_headbanging_in_output(self, tmp_path, reference_dir):
        """남겨진 우산 (synth-pop) 출력 전체에 headbanging이 없어야 한다."""
        song = parse_song(PROJECT_ROOT / "input" / "남겨진 우산.txt")
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        for name in PROMPT_FILES:
            text = (dest / name).read_text(encoding="utf-8")
            assert "headbanging" not in text, f"{name} 에 headbanging 잔여"

    def test_hip_hop_song_no_headbanging_in_output(self, tmp_path, reference_dir):
        """오후의 여백 (hip-hop) 출력 전체에 headbanging이 없어야 한다."""
        song = parse_song(PROJECT_ROOT / "input" / "오후의 여백.txt")
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        for name in PROMPT_FILES:
            text = (dest / name).read_text(encoding="utf-8")
            assert "headbanging" not in text, f"{name} 에 headbanging 잔여"


# ---------------------------------------------------------------------------
# soften_aggressive_residue — 신규 추가 항목 검증
# (groove·retro에 newly added: slow_powerful_body, drumsticks, cymbals,
#  crowd_hands, high_contrast, dramatic_camera; hiphop: 대폭 확장)
# ---------------------------------------------------------------------------

class TestSoftenResidueNewlyAdded:
    """이번 업데이트에서 새로 추가된 residue 교체 항목 검증."""

    # ── Groove ──────────────────────────────────────────────────────────────

    def test_groove_slow_powerful_body(self):
        s = make_song(raw_text="afrobeats tropical house groovy")
        result = soften_aggressive_residue("slow powerful body movement,", s)
        assert "powerful" not in result
        assert "groove" in result.lower() or "rhythmic" in result.lower() or "sway" in result.lower()

    def test_groove_drumsticks_powerful(self):
        s = make_song(raw_text="afrobeats tropical house groovy")
        result = soften_aggressive_residue("drumsticks moving with powerful rhythm,", s)
        assert "powerful" not in result
        assert "groove" in result.lower() or "infectious" in result.lower()

    def test_groove_cymbals_shaking(self):
        s = make_song(raw_text="afrobeats city pop nu-disco groovy")
        result = soften_aggressive_residue("cymbals shaking,", s)
        assert "shaking" not in result

    def test_groove_crowd_hands_waving(self):
        s = make_song(raw_text="afrobeats tropical house city pop")
        result = soften_aggressive_residue("crowd hands waving,", s)
        assert "groove" in result.lower() or "rhythm" in result.lower() or "moving" in result.lower()

    def test_groove_high_contrast_backlight(self):
        s = make_song(raw_text="afrobeats groovy house tropical")
        result = soften_aggressive_residue("high contrast cinematic backlight,", s)
        assert "high contrast" not in result.lower()
        assert "warm" in result.lower() or "groove" in result.lower() or "ambient" in result.lower()

    def test_groove_dramatic_camera_push_in(self):
        s = make_song(raw_text="afrobeats tropical house groovy")
        result = soften_aggressive_residue("dramatic front-facing camera push-in,", s)
        assert "dramatic front-facing" not in result
        assert "groove" in result.lower() or "fluid" in result.lower()

    # ── Retro ────────────────────────────────────────────────────────────────

    def test_retro_epic_concert_lighting(self):
        s = make_song(raw_text="synth-pop new wave 80s retro")
        result = soften_aggressive_residue("epic concert lighting movement,", s)
        assert "epic" not in result
        assert "retro" in result.lower() or "80s" in result.lower() or "dramatic" in result.lower()

    def test_retro_drumsticks_powerful(self):
        s = make_song(raw_text="synth-pop synthpop retro synth")
        result = soften_aggressive_residue("drumsticks moving with powerful rhythm,", s)
        assert "powerful" not in result
        assert "80s" in result.lower() or "synth" in result.lower() or "retro" in result.lower()

    def test_retro_cymbals_shaking(self):
        s = make_song(raw_text="synth-pop new wave 80s retro")
        result = soften_aggressive_residue("cymbals shaking,", s)
        assert "shaking" not in result
        assert "retro" in result.lower() or "strobe" in result.lower() or "glinting" in result.lower()

    def test_retro_crowd_hands_waving(self):
        s = make_song(raw_text="synth-pop new wave 80s retro")
        result = soften_aggressive_residue("crowd hands waving,", s)
        assert "retro" in result.lower() or "concert" in result.lower() or "energy" in result.lower()

    def test_retro_high_contrast_backlight(self):
        s = make_song(raw_text="synthpop new wave 80s retro neon")
        result = soften_aggressive_residue("high contrast cinematic backlight,", s)
        assert "high contrast" not in result
        assert "retro" in result.lower() or "neon" in result.lower()

    def test_retro_dramatic_camera_push_in(self):
        s = make_song(raw_text="synth-pop new wave 80s retro")
        result = soften_aggressive_residue("dramatic front-facing camera push-in,", s)
        assert "dramatic front-facing" not in result
        assert "retro" in result.lower() or "theatrical" in result.lower() or "slow" in result.lower()

    # ── Hip-hop ──────────────────────────────────────────────────────────────

    def test_hiphop_intense_live_performance(self):
        s = make_song(raw_text="boom bap hip-hop industrial trap")
        result = soften_aggressive_residue("intense live performance energy,", s)
        assert "intense live performance" not in result
        assert "hip-hop" in result.lower() or "cipher" in result.lower() or "raw" in result.lower()

    def test_hiphop_massive_cyberpunk(self):
        s = make_song(raw_text="boom bap hip-hop industrial trap")
        result = soften_aggressive_residue("massive cyberpunk concert atmosphere,", s)
        assert "massive cyberpunk" not in result
        assert "hip-hop" in result.lower() or "underground" in result.lower() or "raw" in result.lower()

    def test_hiphop_epic_concert_lighting(self):
        s = make_song(raw_text="hip hop boom bap industrial trap")
        result = soften_aggressive_residue("epic concert lighting movement,", s)
        assert "epic concert" not in result
        assert "beat" in result.lower() or "hip-hop" in result.lower() or "smoke" in result.lower()

    def test_hiphop_drumsticks_powerful(self):
        s = make_song(raw_text="boom bap hip-hop")
        result = soften_aggressive_residue("drumsticks moving with powerful rhythm,", s)
        assert "powerful" not in result
        assert "hip-hop" in result.lower() or "precision" in result.lower()

    def test_hiphop_cymbals_shaking(self):
        s = make_song(raw_text="boom bap hip-hop industrial trap")
        result = soften_aggressive_residue("cymbals shaking,", s)
        assert "shaking" not in result
        assert "hi-hat" in result.lower() or "snap" in result.lower() or "crisp" in result.lower()

    def test_hiphop_smoke_bursts(self):
        s = make_song(raw_text="boom bap hip hop")
        result = soften_aggressive_residue("smoke bursts behind the drum set,", s)
        assert "smoke bursts" not in result
        assert "haze" in result.lower() or "smoke" in result.lower() or "kit" in result.lower()

    def test_hiphop_high_contrast_backlight(self):
        s = make_song(raw_text="boom bap hip-hop industrial trap")
        result = soften_aggressive_residue("high contrast cinematic backlight,", s)
        assert "high contrast" not in result
        assert "hip-hop" in result.lower() or "gritty" in result.lower()

    def test_hiphop_crowd_hands_waving(self):
        s = make_song(raw_text="boom bap hip-hop industrial trap")
        result = soften_aggressive_residue("crowd hands waving,", s)
        assert "waving" not in result
        assert "fist" in result.lower() or "hands" in result.lower() or "break" in result.lower()


# ---------------------------------------------------------------------------
# vocal_action — 전체 13개 프로필 일괄 검증
# ---------------------------------------------------------------------------

class TestVocalActionAllProfilesCoverage:
    """모든 프로필의 vocal_action이 03_vocal_image_prompt.md에 반영되는지 일괄 검증."""

    def _key_words(self, vocal_action: str) -> list[str]:
        return [w.lower().strip(".,") for w in vocal_action.split() if len(w) >= 4]

    def test_all_profiles_have_vocal_action_defined(self):
        """모든 13개 프로필에 vocal_action이 비어 있지 않아야 한다."""
        for profile in _GENRE_DATA["profiles"]:
            va = profile["roles"].get("vocal_action", "")
            assert va, f"프로필 '{profile['name']}' vocal_action 비어 있음"

    def test_all_profiles_vocal_action_in_03_output(self, tmp_path, reference_dir):
        """모든 프로필의 vocal_action 핵심 단어가 03_vocal 출력에 2개 이상 포함되어야 한다."""
        for profile in _GENRE_DATA["profiles"]:
            va = profile["roles"].get("vocal_action", "")
            if not va:
                continue
            keywords_raw = " ".join(profile["keywords"][:2])
            song = make_song(raw_text=keywords_raw, genre=profile["name"])
            dest = create_song_folder(
                song=song,
                template_dir=PROJECT_ROOT / "templates",
                output_dir=tmp_path / profile["name"],
                reference_dir=reference_dir,
            )
            text = (dest / "03_vocal_image_prompt.md").read_text(encoding="utf-8").lower()
            key_words = self._key_words(va)
            matched = [w for w in key_words if w in text]
            assert len(matched) >= 2, (
                f"프로필 '{profile['name']}' vocal_action 미반영 — "
                f"va: {va!r}, 매칭: {matched} / 기대: {key_words[:4]}"
            )


# ---------------------------------------------------------------------------
# 신규 장르 프로파일 — lo-fi / jazz / psychedelic 단위 테스트
# ---------------------------------------------------------------------------

class TestInferProfileNewGenres3:
    """lo-fi, jazz, psychedelic 신규 프로파일 infer_profile 단위 검증."""

    def test_lofi_hiphop_not_urban_mood(self):
        """lo-fi hip hop 장르는 hard-hitting urban 무드가 나오면 안 됨 (P1 핵심 수정)."""
        s = make_song(raw_text="lo-fi hip hop indie chill female lazy vocal cassette hiss rhodes piano cozy study vibe")
        profile = infer_profile(s.raw_text, {})
        assert "urban" not in profile["mood"].lower(), "lo-fi hip hop에 urban 무드 오탐"
        assert "hard-hitting" not in profile["mood"].lower(), "lo-fi hip hop에 hard-hitting 무드 오탐"
        assert "cozy" in profile["mood"].lower() or "cassette" in profile["mood"].lower() or "lo-fi" in profile["mood"].lower()

    def test_lofi_profile_matched(self):
        s = make_song(raw_text="lo-fi hip hop cassette hiss cozy study rhodes piano")
        profile = infer_profile(s.raw_text, {})
        assert "lo-fi" in profile["stage_energy"].lower() or "cassette" in profile["stage_energy"].lower() or "bedroom" in profile["stage_energy"].lower()

    def test_lofi_stage_energy_not_hiphop(self):
        """lo-fi 곡은 hip-hop stage_energy가 나오면 안 됨."""
        s = make_song(raw_text="lo-fi hip hop cassette hiss cozy study")
        profile = infer_profile(s.raw_text, {})
        assert "hard-hitting" not in profile["stage_energy"].lower()
        assert "boom-bap" not in profile["stage_energy"].lower()

    def test_lofi_indie_also_matches_lofi(self):
        s = make_song(raw_text="lo-fi indie bedroom chill dreamy soft")
        profile = infer_profile(s.raw_text, {})
        assert "hard-hitting" not in profile["mood"].lower()

    def test_jazz_profile_matched(self):
        s = make_song(raw_text="jazz ballad emotional male vocal warm piano upright bass brush drums")
        profile = infer_profile(s.raw_text, {})
        assert "jazz" in profile["stage_energy"].lower() or "swing" in profile["stage_energy"].lower()

    def test_jazz_mood_not_ballad_defaults(self):
        """jazz ballad는 ballad 기본 무드('cinematic, emotional')가 아닌 jazz 무드여야 함."""
        s = make_song(raw_text="jazz ballad upright bass brush drums")
        profile = infer_profile(s.raw_text, {})
        assert "jazz" in profile["mood"].lower() or "swing" in profile["mood"].lower()

    def test_jazz_lighting_is_warm_amber(self):
        s = make_song(raw_text="smooth jazz bossa nova swing bebop")
        profile = infer_profile(s.raw_text, {})
        assert "amber" in profile["lighting_style"].lower() or "jazz" in profile["lighting_style"].lower() or "warm" in profile["lighting_style"].lower()

    def test_psychedelic_profile_matched(self):
        s = make_song(raw_text="psychedelic indie dreamy vocal surreal visuals warm mix lofi texture")
        profile = infer_profile(s.raw_text, {})
        assert "psychedelic" in profile["stage_energy"].lower() or "surreal" in profile["stage_energy"].lower() or "dreamlike" in profile["stage_energy"].lower()

    def test_psychedelic_mood_not_intense(self):
        """psychedelic 곡은 rock의 'intense, defiant' 무드가 나오면 안 됨."""
        s = make_song(raw_text="psychedelic indie surreal visuals warm dreamy lofi texture")
        profile = infer_profile(s.raw_text, {})
        assert "intense" not in profile["mood"].lower() or "surreal" in profile["mood"].lower()
        assert "dreamlike" in profile["mood"].lower() or "surreal" in profile["mood"].lower() or "psychedelic" in profile["mood"].lower()

    def test_psychedelic_not_lofi_profile(self):
        """psychedelic 곡의 lofi texture가 lo-fi 프로파일을 오탐하면 안 됨."""
        s = make_song(raw_text="psychedelic indie dreamy vocal lofi texture surreal visuals warm mix")
        profile = infer_profile(s.raw_text, {})
        assert "cassette" not in profile["stage_energy"].lower(), "lofi texture가 lo-fi 프로파일 오탐"
        assert "dreamlike" in profile["stage_energy"].lower() or "psychedelic" in profile["stage_energy"].lower()

    def test_lofi_role_lines(self):
        s = make_song(raw_text="lo-fi hip hop cassette hiss cozy study rhodes piano")
        roles = role_lines(s)
        assert "lo-fi" in roles["vocal"].lower() or "soft" in roles["vocal"].lower() or "intimate" in roles["vocal"].lower()

    def test_jazz_role_lines(self):
        s = make_song(raw_text="jazz ballad upright bass brush drums warm piano")
        roles = role_lines(s)
        assert "jazz" in roles["vocal"].lower() or "vibrato" in roles["vocal"].lower() or "phrasing" in roles["vocal"].lower()

    def test_psychedelic_role_lines(self):
        s = make_song(raw_text="psychedelic indie surreal visuals dreamy vocal")
        roles = role_lines(s)
        assert "psychedelic" in roles["vocal"].lower() or "dreamy" in roles["vocal"].lower() or "floating" in roles["vocal"].lower()


# ---------------------------------------------------------------------------
# 신규 장르 soften_aggressive_residue — lo-fi / jazz / psychedelic
# ---------------------------------------------------------------------------

class TestSoftenResidueNewGenres2:
    """lo-fi, jazz, psychedelic 장르 잔여 표현 처리 검증."""

    def test_lofi_hiphop_no_hiphop_residue(self):
        """lo-fi hip hop 곡은 hip-hop 잔여 교체가 적용되지 않아야 함."""
        s = make_song(raw_text="lo-fi hip hop cassette hiss cozy study")
        result = soften_aggressive_residue("dark synthwave metal concert atmosphere,", s)
        assert "metal" not in result.lower(), "lo-fi 곡에 metal 잔여"
        assert "hip-hop" not in result.lower(), "lo-fi 곡에 hip-hop 교체 잔여"

    def test_lofi_hiphop_gets_soft_treatment(self):
        """lo-fi hip hop 곡은 soft 잔여 교체가 적용되어야 함 (hip-hop 교체 아님)."""
        s = make_song(raw_text="lo-fi hip hop cassette hiss cozy study")
        result = soften_aggressive_residue("dark synthwave metal concert atmosphere,", s)
        # metal 잔여가 제거되어야 함 (soft 처리)
        assert "metal" not in result.lower(), "lo-fi 곡에 metal 잔여 남음"
        # hip-hop 교체("gritty underground hip-hop")가 적용되면 안 됨
        assert "underground hip-hop" not in result.lower(), "lo-fi 곡에 hiphop 잔여 교체 적용됨"

    def test_lofi_no_headbanging_in_output(self, tmp_path, reference_dir):
        """늘어진 카세트처럼 (lo-fi) 출력에 headbanging이 없어야 함."""
        song = parse_song(PROJECT_ROOT / "input" / "늘어진 카세트처럼.txt")
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        for name in PROMPT_FILES:
            text = (dest / name).read_text(encoding="utf-8")
            assert "headbanging" not in text, f"{name} 에 headbanging 잔여"
            assert "hard-hitting urban" not in text, f"{name} 에 hip-hop 잔여"

    def test_jazz_no_metal_residue_in_output(self, tmp_path, reference_dir):
        """여름밤 (jazz ballad) 출력에 metal 잔여가 없어야 함."""
        song = parse_song(PROJECT_ROOT / "input" / "여름밤.txt")
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        for name in PROMPT_FILES:
            text = (dest / name).read_text(encoding="utf-8")
            assert "headbanging" not in text, f"{name} 에 headbanging 잔여"

    def test_psychedelic_no_headbanging_in_output(self, tmp_path, reference_dir):
        """흐린 밤 (psychedelic) 출력에 headbanging이 없어야 함."""
        song = parse_song(PROJECT_ROOT / "input" / "흐린 밤.txt")
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        for name in PROMPT_FILES:
            text = (dest / name).read_text(encoding="utf-8")
            assert "headbanging" not in text, f"{name} 에 headbanging 잔여"
            assert "screams aggressively" not in text, f"{name} 에 aggressive 잔여"


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 늘어진 카세트처럼 (lo-fi hip hop)
# ---------------------------------------------------------------------------

class TestParseSongNeurojinCassette:
    INPUT = PROJECT_ROOT / "input" / "늘어진 카세트처럼.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "늘어진 카세트처럼.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "늘어진 카세트처럼"

    def test_genre_contains_lofi(self):
        song = parse_song(self.INPUT)
        assert "lo-fi" in song.genre.lower()

    def test_mood_is_cozy_not_urban(self):
        """lo-fi hip hop은 urban/hard-hitting 무드가 아닌 cozy/cassette 무드여야 함."""
        song = parse_song(self.INPUT)
        assert "urban" not in song.mood.lower(), "lo-fi 곡에 urban 무드 오탐"
        assert "hard-hitting" not in song.mood.lower()
        assert "cozy" in song.mood.lower() or "cassette" in song.mood.lower() or "lo-fi" in song.mood.lower()

    def test_stage_energy_is_lofi_not_hiphop(self):
        song = parse_song(self.INPUT)
        assert "lo-fi" in song.stage_energy.lower() or "bedroom" in song.stage_energy.lower() or "cassette" in song.stage_energy.lower()
        assert "hard-hitting" not in song.stage_energy.lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 여름밤 (jazz ballad)
# ---------------------------------------------------------------------------

class TestParseSongYeoreumBam:
    INPUT = PROJECT_ROOT / "input" / "여름밤.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "여름밤.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "여름밤"

    def test_genre_contains_jazz(self):
        song = parse_song(self.INPUT)
        assert "jazz" in song.genre.lower()

    def test_mood_is_jazz_not_generic_cinematic(self):
        """jazz ballad는 generic 'cinematic, emotional' 무드가 아닌 jazz 무드여야 함."""
        song = parse_song(self.INPUT)
        assert "jazz" in song.mood.lower() or "swing" in song.mood.lower() or "club" in song.mood.lower()

    def test_stage_energy_is_jazz(self):
        song = parse_song(self.INPUT)
        assert "jazz" in song.stage_energy.lower() or "swing" in song.stage_energy.lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# parse_song 실제 파일 통합 — 흐린 밤 (psychedelic indie)
# ---------------------------------------------------------------------------

class TestParseSongHeurinBam:
    INPUT = PROJECT_ROOT / "input" / "흐린 밤.txt"

    def test_file_exists(self):
        assert self.INPUT.exists(), "흐린 밤.txt 가 input 폴더에 없음"

    def test_title_parsed(self):
        song = parse_song(self.INPUT)
        assert song.title == "흐린 밤"

    def test_genre_contains_psychedelic(self):
        song = parse_song(self.INPUT)
        assert "psychedelic" in song.genre.lower()

    def test_profile_is_psychedelic_not_lofi(self):
        """lofi texture 키워드가 lo-fi 프로파일을 오탐하면 안 됨."""
        song = parse_song(self.INPUT)
        assert "cassette" not in song.stage_energy.lower(), "lofi texture가 lo-fi 프로파일 오탐"
        assert "dreamlike" in song.stage_energy.lower() or "psychedelic" in song.stage_energy.lower() or "surreal" in song.stage_energy.lower()

    def test_mood_is_dreamlike_not_urban(self):
        song = parse_song(self.INPUT)
        assert "urban" not in song.mood.lower()
        assert "dreamlike" in song.mood.lower() or "surreal" in song.mood.lower() or "psychedelic" in song.mood.lower()

    def test_no_placeholder_in_output(self, tmp_path, reference_dir):
        song = parse_song(self.INPUT)
        dest = create_song_folder(
            song=song,
            template_dir=PROJECT_ROOT / "templates",
            output_dir=tmp_path / "output",
            reference_dir=reference_dir,
        )
        errors = validate_song_folder(dest, reference_dir=reference_dir)
        assert errors == [], "\n".join(errors)
