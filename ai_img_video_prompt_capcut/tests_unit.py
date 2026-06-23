"""ai_img_video_prompt_capcut 단위 테스트 (파일 I/O 없는 순수 함수 검증)"""
import json
import tempfile
from pathlib import Path

import pytest

from main import (
    SECTION_RE,
    _normalize_section_name,
    load_config,
    normalize_timestamps,
    match_sections,
    build_slots,
    parse_lrc,
    parse_srt,
    parse_capcut_map_from_md,
)
from capcut_draft import _us, _DEFAULT_CLIP_DUR_MS, _TRANSITION_DUR_MS, build_draft, write_draft


# ─── helpers ─────────────────────────────────────────────────────────────────

def _write_config(data: dict) -> Path:
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(data, tmp)
    tmp.close()
    return Path(tmp.name)


def _config(sections_mvp: list) -> dict:
    return {
        "mode": "mvp",
        "modes": {"mvp": {"capcut_map": {"sections": sections_mvp}}},
    }


def _sec(name, start=0, end=30000):
    return {"name": name, "start_ms": start, "end_ms": end}


# ─── SECTION_RE ──────────────────────────────────────────────────────────────

def test_section_re_intro():
    assert SECTION_RE.match("intro")

def test_section_re_chorus_numbered():
    assert SECTION_RE.match("Chorus 2")

def test_section_re_verse_numbered():
    assert SECTION_RE.match("verse 1")

def test_section_re_pre_chorus():
    assert SECTION_RE.match("pre-chorus")

def test_section_re_outro():
    assert SECTION_RE.match("Outro")

def test_section_re_bridge():
    assert SECTION_RE.match("bridge")

def test_section_re_post_chorus():
    assert SECTION_RE.match("post-chorus")

def test_section_re_invalid_junk():
    assert not SECTION_RE.match("some random text")

def test_section_re_invalid_empty():
    assert not SECTION_RE.match("")


# ─── load_config ─────────────────────────────────────────────────────────────

def test_load_config_mode_and_shots():
    tmp = _write_config(_config(["Intro: stage_A, vocal_A"]))
    mode, capcut_map = load_config(tmp)
    tmp.unlink()
    assert mode == "mvp"
    assert "Intro" in capcut_map
    assert capcut_map["Intro"] == [("stage_A", None), ("vocal_A", None)]


def test_load_config_or_fallback():
    tmp = _write_config(_config(["Outro: stage A or atmosphere A"]))
    _, capcut_map = load_config(tmp)
    tmp.unlink()
    assert capcut_map["Outro"] == [("stage_A", "atmosphere_A")]


def test_load_config_skips_no_colon():
    tmp = _write_config(_config(["this line has no colon"]))
    _, capcut_map = load_config(tmp)
    tmp.unlink()
    assert capcut_map == {}


# ─── normalize_timestamps ────────────────────────────────────────────────────

def test_normalize_timestamps_sets_end_ms():
    sections = [
        {"name": "Intro", "start_ms": 0},
        {"name": "Verse", "start_ms": 15000},
    ]
    result = normalize_timestamps(sections, audio_ms=60000)
    assert result[0]["end_ms"] == 15000
    assert result[1]["end_ms"] == 60000


def test_normalize_timestamps_empty():
    assert normalize_timestamps([], audio_ms=60000) == []


def test_normalize_timestamps_no_audio_ms():
    sections = [{"name": "Outro", "start_ms": 0}]
    result = normalize_timestamps(sections, audio_ms=None)
    assert result[0]["end_ms"] == 30000


def test_normalize_timestamps_scaling_compressed_lrc():
    """Suno LRC 압축 타임스탬프 스케일링 검증 — last_start이 audio_ms의 1/5 미만이면 스케일링 적용"""
    # LRC 타임스탬프가 실제 길이의 1/10 수준으로 압축된 케이스
    sections = [
        {"name": "Intro", "start_ms": 0},
        {"name": "Verse 1", "start_ms": 1000},
        {"name": "Chorus", "start_ms": 2000},
    ]
    result = normalize_timestamps(sections, audio_ms=30000)
    # 스케일링 후 첫 섹션은 항상 0
    assert result[0]["start_ms"] == 0
    # 마지막 섹션 end_ms는 audio_ms와 일치해야 함
    assert result[-1]["end_ms"] == 30000
    # 스케일링 적용 여부: audio_ms(30000) / last_start(2000) = 15 > 5 → 스케일링 됨
    assert result[1]["start_ms"] > 1000


def test_normalize_timestamps_no_scaling_realtime_lrc():
    """실제 타임스탬프 LRC는 스케일링 안 함 — audio_ms / last_start ≤ 5"""
    sections = [
        {"name": "Intro", "start_ms": 0},
        {"name": "Chorus", "start_ms": 90000},
    ]
    result = normalize_timestamps(sections, audio_ms=187000)
    # 187000 / 90000 ≈ 2.07 < 5 → 스케일링 안 함
    assert result[1]["start_ms"] == 90000
    assert result[1]["end_ms"] == 187000


# ─── match_sections ──────────────────────────────────────────────────────────

def test_match_sections_intro():
    capcut_map = {"Intro": [("stage_A", None)]}
    result = match_sections([_sec("intro")], capcut_map)
    assert result[0]["capcut_key"] == "Intro"


def test_match_sections_chorus_rank():
    capcut_map = {
        "Chorus 1": [("stage_B", None)],
        "Final Chorus": [("stage_C", None)],
    }
    sections = [
        _sec("intro"),
        _sec("Chorus"),
        _sec("Verse 2"),
        _sec("Chorus"),
    ]
    result = match_sections(sections, capcut_map)
    chorus_results = [r for r in result if "chorus" in r["name"].lower()]
    assert chorus_results[0]["capcut_key"] == "Chorus 1"
    assert chorus_results[1]["capcut_key"] == "Final Chorus"


def test_match_sections_bridge_solo():
    capcut_map = {"Bridge/Solo": [("guitar_A", None)]}
    result = match_sections([_sec("bridge")], capcut_map)
    assert result[0]["capcut_key"] == "Bridge/Solo"


def test_match_sections_pre_chorus():
    capcut_map = {"Pre-Chorus": [("stage_B", None)]}
    result = match_sections([_sec("Pre-Chorus")], capcut_map)
    assert result[0]["capcut_key"] == "Pre-Chorus"


def test_match_sections_post_chorus():
    capcut_map = {"Post-Chorus": [("atmosphere_a", None)]}
    result = match_sections([_sec("Post-Chorus")], capcut_map)
    assert result[0]["capcut_key"] == "Post-Chorus"


def test_match_sections_chorus_final_not_confused_by_post_chorus():
    """Chorus + Post-Chorus + Chorus 패턴에서 마지막 Chorus가 Final Chorus로 승격되는지 검증"""
    capcut_map = {
        "Chorus 1": [("stage_B", None)],
        "Final Chorus": [("stage_C", None)],
        "Post-Chorus": [("atmosphere_a", None)],
    }
    sections = [
        _sec("Intro"),
        _sec("Chorus", 10000, 40000),
        _sec("Post-Chorus", 40000, 52000),
        _sec("Chorus", 52000, 90000),
    ]
    result = match_sections(sections, capcut_map)
    chorus_results = [r for r in result if r["name"] == "Chorus"]
    assert chorus_results[0]["capcut_key"] == "Chorus 1"
    assert chorus_results[1]["capcut_key"] == "Final Chorus"


# ─── build_slots ─────────────────────────────────────────────────────────────

def test_build_slots_assigned():
    sections = [{"name": "Intro", "capcut_key": "Intro", "start_ms": 0, "end_ms": 15000}]
    capcut_map = {"Intro": [("stage_a", None)]}
    clips = {"stage_a": "stage_A.mp4"}
    slots = build_slots(sections, capcut_map, clips)
    assert len(slots) == 1
    assert slots[0]["source"] == "assigned"
    assert slots[0]["clip_file"] == "stage_A.mp4"


def test_build_slots_placeholder():
    sections = [{"name": "Intro", "capcut_key": "Intro", "start_ms": 0, "end_ms": 15000}]
    capcut_map = {"Intro": [("stage_a", None)]}
    slots = build_slots(sections, capcut_map, {})
    assert slots[0]["source"] == "placeholder"
    assert slots[0]["review_required"] is True


def test_build_slots_slot_id_dedup():
    sections = [
        {"name": "Chorus", "capcut_key": "Chorus 1", "start_ms": 0, "end_ms": 30000},
        {"name": "Chorus", "capcut_key": "Chorus 1", "start_ms": 60000, "end_ms": 90000},
    ]
    capcut_map = {"Chorus 1": [("vocal_a", None)]}
    clips = {"vocal_a": "vocal_A.mp4"}
    slots = build_slots(sections, capcut_map, clips)
    assert slots[0]["slot_id"] != slots[1]["slot_id"]


def test_build_slots_fallback_used():
    sections = [{"name": "Outro", "capcut_key": "Outro", "start_ms": 0, "end_ms": 30000}]
    capcut_map = {"Outro": [("stage_a", "atmosphere_a")]}
    clips = {"atmosphere_a": "atmosphere_A.mp4"}
    slots = build_slots(sections, capcut_map, clips)
    assert slots[0]["fallback_used"] == "atmosphere_a"
    assert slots[0]["clip_file"] == "atmosphere_A.mp4"


def test_build_slots_duration_ms():
    sections = [{"name": "Intro", "capcut_key": "Intro", "start_ms": 5000, "end_ms": 20000}]
    capcut_map = {"Intro": [("stage_a", None)]}
    slots = build_slots(sections, capcut_map, {"stage_a": "stage_A.mp4"})
    assert slots[0]["duration_ms"] == 15000


# ─── _normalize_section_name ─────────────────────────────────────────────────

def test_normalize_explosive_chorus():
    assert _normalize_section_name("explosive chorus") == "Chorus"

def test_normalize_build_chorus():
    assert _normalize_section_name("build chorus") == "Chorus"

def test_normalize_final_chorus_decorated():
    assert _normalize_section_name("explosive final chorus") == "Final Chorus"

def test_normalize_pre_chorus_unchanged():
    assert _normalize_section_name("Pre-Chorus") == "Pre-Chorus"

def test_normalize_non_chorus_unchanged():
    assert _normalize_section_name("build intensity") == "build intensity"

def test_normalize_breath_before_chorus_unchanged():
    assert _normalize_section_name("breath before chorus") == "breath before chorus"

def test_normalize_build_to_chorus_unchanged():
    assert _normalize_section_name("build to chorus") == "build to chorus"


# ─── parse_lrc ────────────────────────────────────────────────────────────────

def _write_lrc(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile("w", suffix=".lrc", delete=False, encoding="utf-8")
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def test_parse_lrc_explosive_chorus_detected():
    """[explosive chorus] 섹션이 'Chorus'로 파싱되는지 검증"""
    lrc = _write_lrc(
        "[00:11.37][Intro]\n"
        "[00:21.67][Verse 1]\n"
        "[00:33.00][Pre-Chorus]\n"
        "[00:43.16][explosive chorus]\n"
        "[00:43.16][wider stereo guitars]\n"
        "[01:00.68][Post-Chorus]\n"
        "[End]\n"
    )
    sections = parse_lrc(lrc)
    lrc.unlink()
    names = [s["name"] for s in sections]
    assert "Chorus" in names
    chorus = next(s for s in sections if s["name"] == "Chorus")
    assert chorus["start_ms"] == 43160


def test_parse_lrc_pre_chorus_ends_at_chorus():
    """[explosive chorus] 감지 후 Pre-Chorus 종료 시각이 Chorus 시작과 일치하는지 검증"""
    lrc = _write_lrc(
        "[00:11.37][Intro]\n"
        "[00:21.67][Verse 1]\n"
        "[00:33.00][Pre-Chorus]\n"
        "[00:43.16][explosive chorus]\n"
        "[01:00.68][Post-Chorus]\n"
        "[End]\n"
    )
    sections = parse_lrc(lrc)
    lrc.unlink()
    sections = normalize_timestamps(sections, audio_ms=187032)
    pre = next(s for s in sections if s["name"] == "Pre-Chorus")
    chorus = next(s for s in sections if s["name"] == "Chorus")
    assert pre["end_ms"] == chorus["start_ms"] == 43160


# ─── parse_srt ───────────────────────────────────────────────────────────────

def _write_srt(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".srt", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def test_parse_srt_skips_before_end():
    srt = _write_srt(
        "1\n00:00:00,000 --> 00:00:00,180\n[Intro]\n\n"
        "2\n00:00:00,180 --> 00:00:00,360\n압축 가사\n\n"
        "3\n00:00:00,360 --> 00:00:01,000\n[End]\n\n"
        "4\n00:00:24,000 --> 00:00:27,000\n실제 가사입니다\n"
    )
    result = parse_srt(srt)
    srt.unlink()
    assert len(result) == 1
    assert result[0]["text"] == "실제 가사입니다"


def test_parse_srt_filters_brackets():
    srt = _write_srt(
        "1\n00:00:00,000 --> 00:00:01,000\n[End]\n\n"
        "2\n00:00:24,000 --> 00:00:27,000\n[Verse 1]\n\n"
        "3\n00:00:27,000 --> 00:00:30,000\n진짜 가사\n"
    )
    result = parse_srt(srt)
    srt.unlink()
    assert len(result) == 1
    assert result[0]["text"] == "진짜 가사"


def _write_md(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(
        "w", suffix=".md", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


# ─── parse_capcut_map_from_md ─────────────────────────────────────────────────

def test_parse_capcut_map_from_md_basic():
    md = _write_md(
        "## CapCut Editing Map\n\n"
        "```text\n"
        "Intro       : stage_A, atmosphere_A\n"
        "Outro       : stage_A or atmosphere_A\n"
        "```\n"
    )
    result = parse_capcut_map_from_md(md)
    md.unlink()
    assert result is not None
    assert result["Intro"] == [("stage_A", None), ("atmosphere_A", None)]
    assert result["Outro"] == [("stage_A", "atmosphere_A")]


def test_parse_capcut_map_from_md_no_section():
    md = _write_md("## Motion Variants\n\nno editing map here\n")
    result = parse_capcut_map_from_md(md)
    md.unlink()
    assert result is None


def test_parse_srt_timestamps():
    srt = _write_srt(
        "1\n00:00:00,000 --> 00:00:01,000\n[End]\n\n"
        "2\n00:01:30,500 --> 00:01:33,200\n타임스탬프 확인\n"
    )
    result = parse_srt(srt)
    srt.unlink()
    assert result[0]["start_ms"] == 90500
    assert result[0]["end_ms"] == 93200


# ─── capcut_draft: 헬퍼 ──────────────────────────────────────────────────────

def _make_timeline(total_ms=60000, clips=None):
    if clips is None:
        clips = [
            {
                "source": "assigned",
                "clip_file": "stage_A.mp4",
                "start_ms": 0,
                "end_ms": total_ms,
                "duration_ms": total_ms,
            }
        ]
    return {"song_title": "테스트곡", "total_duration_ms": total_ms, "clips": clips}


def _build(timeline=None, srt_kr=None, srt_en=None):
    if timeline is None:
        timeline = _make_timeline()
    return build_draft(
        timeline,
        Path("C:/fake/song.wav"),
        Path("C:/fake/clips"),
        {"stage_a": 5000},
        srt_kr,
        srt_en,
    )


# ─── capcut_draft: ms → μs 변환 ──────────────────────────────────────────────

def test_us_zero():
    assert _us(0) == 0


def test_us_one_second():
    assert _us(1000) == 1_000_000


def test_us_real_duration():
    assert _us(187032) == 187_032_000


# ─── capcut_draft: draft_content 필수 키 ─────────────────────────────────────

def test_draft_content_required_keys():
    content, _, _ = _build()
    for key in ("canvas_config", "duration", "materials", "tracks", "id", "new_version", "draft_type"):
        assert key in content, f"필수 키 누락: {key}"


def test_draft_content_canvas_resolution():
    content, _, _ = _build()
    assert content["canvas_config"]["width"] == 1920
    assert content["canvas_config"]["height"] == 1080


def test_draft_content_duration_matches_timeline():
    content, _, _ = _build()
    assert content["duration"] == _us(60000)


def test_draft_content_materials_required_keys():
    content, _, _ = _build()
    mats = content["materials"]
    for key in ("videos", "audios", "texts", "speeds", "beats", "canvases",
                "placeholder_infos", "sound_channel_mappings", "vocal_separations"):
        assert key in mats, f"materials 필수 키 누락: {key}"


# ─── capcut_draft: draft_meta_info 필수 키 ───────────────────────────────────

def test_draft_meta_required_keys():
    _, meta, _ = _build()
    for key in ("draft_id", "draft_name", "draft_materials", "tm_duration", "draft_cover"):
        assert key in meta, f"메타 필수 키 누락: {key}"


def test_draft_meta_name_format():
    _, meta, _ = _build()
    assert meta["draft_name"] == "테스트곡_MV"


def test_draft_meta_id_consistency():
    _, meta, draft_id = _build()
    assert meta["draft_id"] == draft_id


def test_draft_meta_duration():
    _, meta, _ = _build()
    assert meta["tm_duration"] == _us(60000)


# ─── capcut_draft: video/audio/text track 개수 ───────────────────────────────

def test_tracks_no_srt_two_tracks():
    content, _, _ = _build()
    types = [t["type"] for t in content["tracks"]]
    assert types.count("video") == 1
    assert types.count("audio") == 1
    assert types.count("text") == 0


def test_tracks_with_kr_srt_adds_text_track():
    srt_kr = [{"text": "안녕", "start_ms": 0, "end_ms": 1000}]
    content, _, _ = _build(srt_kr=srt_kr)
    types = [t["type"] for t in content["tracks"]]
    assert types.count("text") == 1
    assert len(content["tracks"]) == 3


def test_tracks_with_both_srt_four_tracks():
    srt_kr = [{"text": "안녕", "start_ms": 0, "end_ms": 1000}]
    srt_en = [{"text": "Hello", "start_ms": 0, "end_ms": 1000}]
    content, _, _ = _build(srt_kr=srt_kr, srt_en=srt_en)
    types = [t["type"] for t in content["tracks"]]
    assert types.count("text") == 2
    assert len(content["tracks"]) == 4


# ─── capcut_draft: write_draft 폴더 구조 ─────────────────────────────────────

def test_write_draft_creates_folder_and_files():
    content, meta, draft_id = _build()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        folder = write_draft(content, meta, draft_id, root)
        assert folder.exists()
        assert (folder / "draft_content.json").exists()
        assert (folder / "draft_meta_info.json").exists()


def test_write_draft_folder_named_by_draft_id():
    content, meta, draft_id = _build()
    with tempfile.TemporaryDirectory() as tmp:
        folder = write_draft(content, meta, draft_id, Path(tmp))
        assert folder.name == draft_id


def test_write_draft_paths_in_meta():
    content, meta, draft_id = _build()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        folder = write_draft(content, meta, draft_id, root)
        assert meta["draft_fold_path"] == folder.as_posix()
        assert meta["draft_root_path"] == root.as_posix()


def test_write_draft_valid_json():
    content, meta, draft_id = _build()
    with tempfile.TemporaryDirectory() as tmp:
        folder = write_draft(content, meta, draft_id, Path(tmp))
        json.loads((folder / "draft_content.json").read_text(encoding="utf-8"))
        json.loads((folder / "draft_meta_info.json").read_text(encoding="utf-8"))


# ─── normalize_timestamps: Bug1+2 회귀 테스트 ────────────────────────────────

def test_normalize_timestamps_scaling_nonzero_first_start():
    """Bug1+2 수정 검증 — first_start > 0인 압축 LRC에서 offset 보정 후 올바른 간격 유지"""
    # first_start=500, last_start=2000, audio_ms=30000 → ratio=15 > 5 → 스케일링 적용
    # 수정 전: Verse.start = int(1000 * scale) ≠ 의도 값 (offset 미보정)
    # 수정 후: Verse.start = int((1000-500) * scale), Intro.start = 0
    sections = [
        {"name": "Intro", "start_ms": 500},
        {"name": "Verse 1", "start_ms": 1000},
        {"name": "Chorus", "start_ms": 2000},
    ]
    result = normalize_timestamps(sections, audio_ms=30000)
    # 첫 섹션은 반드시 0
    assert result[0]["start_ms"] == 0
    # span=1500, avg_dur=750, scale=30000/2250=13.33
    # Verse: (1000-500)*13.33 ≈ 6666, Chorus: (2000-500)*13.33 ≈ 20000
    # 수정 전 Verse: 1000*13.33=13333 (섹션 간격이 2배 이상 왜곡됨)
    assert result[1]["start_ms"] < 10_000  # Bug1 수정 전은 13333 → 이 검사 실패
    assert result[1]["start_ms"] < result[2]["start_ms"]
    assert result[-1]["end_ms"] == 30000


# ─── capcut_draft: clip duration 폴백 freeze 방지 ──────────────────────────

def test_clip_duration_unknown_uses_default_not_section_duration():
    """clip_durations 비어 있을 때 section_duration 대신 _DEFAULT_CLIP_DUR_MS 사용 — freeze 방지"""
    section_dur_ms = 60_000  # section이 60s지만 실제 클립은 기본값(8s)으로 처리되어야 함
    timeline = _make_timeline(total_ms=section_dur_ms)
    content, _, _ = build_draft(
        timeline,
        Path("C:/fake/song.wav"),
        Path("C:/fake/clips"),
        {},  # clip_durations 비어있음 → 폴백 발동
    )
    tracks = content["tracks"]
    video_track = next(t for t in tracks if t.get("type") == "video")
    for seg in video_track["segments"]:
        src_dur_us = seg["source_timerange"]["duration"]
        # 수정 전: src_dur_us == _us(section_dur_ms) = 60_000_000 → CapCut freeze
        # 수정 후: src_dur_us <= _us(_DEFAULT_CLIP_DUR_MS) = 8_000_000
        assert src_dur_us <= _us(_DEFAULT_CLIP_DUR_MS), (
            f"source_timerange.duration {src_dur_us} > _DEFAULT ({_us(_DEFAULT_CLIP_DUR_MS)}): "
            "clip이 section 전체를 덮으면 CapCut이 마지막 프레임에서 freeze됨"
        )


# ─── capcut_draft: transition (섹션 경계 디졸브) ──────────────────────────────

def _make_two_section_timeline(clip_dur_ms=5000):
    """섹션 2개 타임라인 — Section1(0~30s), Section2(30s~60s), 각 섹션에 클립 1개"""
    return {
        "song_title": "전환테스트",
        "total_duration_ms": 60_000,
        "clips": [
            {"source": "assigned", "clip_file": "clip_a.mp4",
             "start_ms": 0, "end_ms": 30_000, "duration_ms": 30_000},
            {"source": "assigned", "clip_file": "clip_b.mp4",
             "start_ms": 30_000, "end_ms": 60_000, "duration_ms": 30_000},
        ],
    }


def test_transition_added_at_section_boundary():
    """섹션 경계(2번째 섹션 첫 클립)에 transition이 materials.transitions에 추가됨"""
    content, _, _ = build_draft(
        _make_two_section_timeline(),
        Path("C:/fake/song.wav"),
        Path("C:/fake/clips"),
        {"clip_a": 5000, "clip_b": 5000},
    )
    transitions = content["materials"]["transitions"]
    assert len(transitions) >= 1, "섹션 경계 transition이 생성되어야 함"
    t = transitions[0]
    assert t["type"] == "transition"
    assert t["is_overlap"] is True
    assert t["duration"] == _us(_TRANSITION_DUR_MS)


def test_transition_no_transition_on_first_section():
    """첫 섹션의 첫 클립에는 transition이 없어야 함"""
    content, _, _ = build_draft(
        _make_two_section_timeline(),
        Path("C:/fake/song.wav"),
        Path("C:/fake/clips"),
        {"clip_a": 5000, "clip_b": 5000},
    )
    tracks = content["tracks"]
    video_track = next(t for t in tracks if t.get("type") == "video")
    first_seg = video_track["segments"][0]
    # 첫 세그먼트는 6개 refs (transition 없음)
    assert len(first_seg["extra_material_refs"]) == 6, "첫 클립에 transition refs가 없어야 함"


def test_transition_refs_on_second_section_first_clip():
    """2번째 섹션 첫 클립의 extra_material_refs는 8개 (transition + sticker_anim 포함)"""
    content, _, _ = build_draft(
        _make_two_section_timeline(),
        Path("C:/fake/song.wav"),
        Path("C:/fake/clips"),
        {"clip_a": 5000, "clip_b": 5000},
    )
    tracks = content["tracks"]
    video_track = next(t for t in tracks if t.get("type") == "video")
    segs = video_track["segments"]
    # clip_a(5s) × 6 cycles = 30s section1, clip_b의 첫 클립이 transition 대상
    # section1은 clip_a 5000ms × 6 = 30000ms → 6개 세그먼트
    # section2 첫 세그먼트 = segs[6]
    sec2_first = segs[6]
    refs = sec2_first["extra_material_refs"]
    assert len(refs) == 8, f"전환 세그먼트 refs는 8개여야 함, 실제: {len(refs)}"
    # transition ID가 materials.transitions에 있어야 함
    transition_ids = {t["id"] for t in content["materials"]["transitions"]}
    assert refs[2] in transition_ids, "refs[2]가 transition material ID여야 함"
