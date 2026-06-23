"""
youtube_research/tests_unit.py
순수 함수 단위 테스트: analyze.py + collect.py 유틸
네트워크 호출 없음. yt-dlp 실행 없음.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pytest
from analyze import (
    filter_ai_channels,
    top_videos,
    keyword_freq,
    channel_stats,
    upload_trend,
    tag_freq,
    build_url_list,
    build_report,
)
from collect import _parse_jsonl, _normalize

# ── 공통 픽스처 데이터 ────────────────────────────────────────────────────────

VIDEOS = [
    {
        "id": "v1", "title": "AI Music Video Epic", "channel_name": "AI Tunes",
        "channel_handle": "aitunes", "view_count": 50000,
        "upload_date": "20240101", "tags": ["ai", "music"], "description": "great",
    },
    {
        "id": "v2", "title": "Chill Lofi Study Beats", "channel_name": "Lofi AI Studio",
        "channel_handle": "lofiAI", "view_count": 20000,
        "upload_date": "20240215", "tags": ["lofi", "chill"], "description": "relax",
    },
    {
        "id": "v3", "title": "Rock Anthem Forever Live", "channel_name": "Human Artist",
        "channel_handle": "humanartist", "view_count": 100000,
        "upload_date": "20240310", "tags": ["rock"], "description": "x" * 400,
    },
]


# ── top_videos ────────────────────────────────────────────────────────────────

def test_top_videos_returns_n():
    assert len(top_videos(VIDEOS, n=2)) == 2


def test_top_videos_sorted_descending():
    result = top_videos(VIDEOS)
    assert result[0]["view_count"] >= result[-1]["view_count"]


def test_top_videos_fewer_than_n():
    assert len(top_videos(VIDEOS, n=100)) == len(VIDEOS)


def test_top_videos_empty():
    assert top_videos([], n=5) == []


# ── keyword_freq ──────────────────────────────────────────────────────────────

def test_keyword_freq_stopwords_excluded():
    vids = [{"title": "The Best Music Video AI Official", "view_count": 1}]
    words = [w for w, _ in keyword_freq(vids, n=30)]
    assert "the" not in words
    assert "music" not in words
    assert "video" not in words
    assert "ai" not in words      # ai 는 STOPWORDS 에 포함
    assert "best" in words        # best 는 STOPWORDS 에 없음


def test_keyword_freq_returns_at_most_n():
    assert len(keyword_freq(VIDEOS, n=3)) <= 3


def test_keyword_freq_empty():
    assert keyword_freq([], n=10) == []


def test_keyword_freq_sorted_by_count():
    vids = [
        {"title": "rock rock rock", "view_count": 1},
        {"title": "chill rock", "view_count": 1},
    ]
    result = keyword_freq(vids, n=10)
    counts = [c for _, c in result]
    assert counts == sorted(counts, reverse=True)


# ── channel_stats ─────────────────────────────────────────────────────────────

def test_channel_stats_keys_present():
    stats = channel_stats(VIDEOS)
    assert "AI Tunes" in stats
    assert "Human Artist" in stats


def test_channel_stats_count_each():
    stats = channel_stats(VIDEOS)
    for ch in stats.values():
        assert ch["count"] >= 1


def test_channel_stats_avg_views():
    vids = [
        {"channel_name": "X", "view_count": 1000, "title": "T"},
        {"channel_name": "X", "view_count": 3000, "title": "T"},
    ]
    stats = channel_stats(vids)
    assert stats["X"]["avg_views"] == 2000
    assert stats["X"]["total_views"] == 4000


def test_channel_stats_total_views():
    stats = channel_stats(VIDEOS)
    assert stats["Human Artist"]["total_views"] == 100000


# ── upload_trend ──────────────────────────────────────────────────────────────

def test_upload_trend_basic():
    trend = upload_trend(VIDEOS)
    assert "2024-01" in trend
    assert "2024-02" in trend
    assert "2024-03" in trend


def test_upload_trend_sorted():
    trend = upload_trend(VIDEOS)
    keys = list(trend.keys())
    assert keys == sorted(keys)


def test_upload_trend_empty_date_ignored():
    vids = [{"upload_date": "", "view_count": 1}]
    assert upload_trend(vids) == {}


def test_upload_trend_short_date_ignored():
    # 4자리 날짜는 len < 6 조건 미충족 → 무시
    vids = [{"upload_date": "2024", "view_count": 1}]
    assert upload_trend(vids) == {}


def test_upload_trend_groups_same_month():
    vids = [
        {"upload_date": "20240101", "view_count": 1},
        {"upload_date": "20240115", "view_count": 1},
    ]
    trend = upload_trend(vids)
    assert trend["2024-01"] == 2


# ── tag_freq ──────────────────────────────────────────────────────────────────

def test_tag_freq_returns_tags():
    result = tag_freq(VIDEOS, n=5)
    assert len(result) > 0


def test_tag_freq_lowercased():
    vids = [{"tags": ["AI", "Music"]}]
    result = tag_freq(vids, n=5)
    tags = [t for t, _ in result]
    assert "ai" in tags
    assert "AI" not in tags


def test_tag_freq_none_tags_safe():
    vids = [{"tags": None}, {"tags": []}]
    assert tag_freq(vids, n=5) == []


def test_tag_freq_returns_at_most_n():
    assert len(tag_freq(VIDEOS, n=1)) <= 1


# ── build_url_list ────────────────────────────────────────────────────────────

def test_build_url_list_contains_youtube_url():
    result = build_url_list(VIDEOS)
    assert "youtube.com/watch?v=" in result


def test_build_url_list_highest_views_first():
    # Human Artist(100k)이 AI Tunes(50k)보다 앞에 위치해야 함
    result = build_url_list(VIDEOS)
    assert result.find("100,000") < result.find("50,000")


def test_build_url_list_all_ids_present():
    result = build_url_list(VIDEOS)
    for v in VIDEOS:
        assert v["id"] in result


# ── build_report ──────────────────────────────────────────────────────────────

def test_build_report_sections_present():
    result = build_report(VIDEOS, "test.json")
    assert "TOP 20" in result
    assert "채널별 통계" in result
    assert "키워드" in result
    assert "트렌드" in result


def test_build_report_contains_channel_name():
    result = build_report(VIDEOS, "test.json")
    assert "AI Tunes" in result


# ── filter_ai_channels ────────────────────────────────────────────────────────

def test_filter_ai_channels_missing_file_returns_all(tmp_path, monkeypatch):
    import analyze
    monkeypatch.setattr(analyze, "CHANNELS_FILE", tmp_path / "nonexistent.json")
    result, dropped = filter_ai_channels(VIDEOS)
    assert result == VIDEOS
    assert dropped == 0


def test_filter_ai_channels_known_handle_kept(tmp_path, monkeypatch):
    import analyze
    config = {
        "channels": [{"handle": "@aitunes", "name": "AI Tunes"}],
        "ai_filter_keywords": [],
    }
    (tmp_path / "channels.json").write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(analyze, "CHANNELS_FILE", tmp_path / "channels.json")
    result, _ = filter_ai_channels(VIDEOS)
    handles = [v["channel_handle"] for v in result]
    assert "aitunes" in handles


def test_filter_ai_channels_keyword_drops_non_ai(tmp_path, monkeypatch):
    import analyze
    config = {"channels": [], "ai_filter_keywords": ["ai", "lofi"]}
    (tmp_path / "channels.json").write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(analyze, "CHANNELS_FILE", tmp_path / "channels.json")
    result, dropped = filter_ai_channels(VIDEOS)
    ch_names = [v["channel_name"] for v in result]
    # "Human Artist" 에는 ai/lofi 키워드 없음 → 제거
    assert "Human Artist" not in ch_names
    assert dropped == 1


# ── _parse_jsonl (collect.py) ──────────────────────────────────────────────────

def test_parse_jsonl_basic():
    raw = '{"id": "v1"}\n{"id": "v2"}'
    result = _parse_jsonl(raw)
    assert len(result) == 2
    assert result[0]["id"] == "v1"


def test_parse_jsonl_skips_invalid_json():
    raw = '{"id": "v1"}\nnot json at all\n{"id": "v2"}'
    result = _parse_jsonl(raw)
    assert len(result) == 2


def test_parse_jsonl_empty_string():
    assert _parse_jsonl("") == []


def test_parse_jsonl_empty_lines_ignored():
    raw = '{"id": "v1"}\n\n{"id": "v2"}'
    assert len(_parse_jsonl(raw)) == 2


# ── _normalize (collect.py) ───────────────────────────────────────────────────

def test_normalize_strips_at_from_handle():
    result = _normalize({}, channel_handle="@mychannel")
    assert result["channel_handle"] == "mychannel"


def test_normalize_basic_fields():
    data = {"id": "abc", "title": "My Video", "view_count": 1000, "tags": ["tag1"]}
    result = _normalize(data, channel_name="Ch")
    assert result["id"] == "abc"
    assert result["title"] == "My Video"
    assert result["view_count"] == 1000
    assert result["channel_name"] == "Ch"


def test_normalize_truncates_description():
    data = {"description": "x" * 400}
    result = _normalize(data)
    assert len(result["description"]) == 300


def test_normalize_missing_fields_default():
    result = _normalize({})
    assert result["view_count"] == 0
    assert result["tags"] == []
    assert result["title"] == ""
