"""
youtube_research/analyze.py
수집된 raw JSON → 마크다운 리포트 생성
사용법: python analyze.py [raw_json_파일]  (생략 시 최신 파일 자동 선택)
"""

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT           = Path(__file__).parent
OUTPUT_RAW     = ROOT / "output" / "raw"
OUTPUT_REPORTS = ROOT / "output" / "reports"
CHANNELS_FILE  = ROOT / "channels.json"


# ── AI 채널 필터 ─────────────────────────────────────────────────────────────

def filter_ai_channels(videos: list[dict]) -> tuple[list[dict], int]:
    """비AI 채널(아티스트, 일반 로파이 등) 제거. 등록 채널 + AI 키워드 채널만 통과."""
    try:
        config = json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return videos, 0

    ai_tokens = set(config.get("ai_filter_keywords", []))
    known     = {ch.get("handle", "").lstrip("@").lower()
                 for ch in config.get("channels", []) if ch.get("handle")}

    keep, drop = [], 0
    for v in videos:
        ch_handle = (v.get("channel_handle") or "").lstrip("@").lower()
        ch_name   = (v.get("channel_name")   or "").lower()

        if ch_handle in known:
            keep.append(v)
            continue

        # 채널명을 단어 단위로 분해해 AI 키워드 포함 여부 확인
        name_tokens = set(re.findall(r"[a-z]+", ch_name))
        if name_tokens & ai_tokens:
            keep.append(v)
        else:
            drop += 1

    return keep, drop


# ── 분석 함수 ────────────────────────────────────────────────────────────────

def top_videos(videos: list[dict], n: int = 20) -> list[dict]:
    return sorted(videos, key=lambda x: x["view_count"], reverse=True)[:n]


def keyword_freq(videos: list[dict], n: int = 30) -> list[tuple[str, int]]:
    STOPWORDS = {
        "the","a","an","and","or","of","in","to","is","for","with","on","at","by",
        "from","this","that","as","are","was","be","it","its","we","you","i","my",
        "your","our","-","|","&",
        "official","video","music","audio","ai","new","full","feat","ft",
        "so","no","not","but","just","me","im",
    }
    _STRIP = "()[].,!?\"'#@"
    words: list[str] = []
    for v in videos:
        for w in v["title"].lower().split():
            w = w.strip(_STRIP)
            if w and w not in STOPWORDS and len(w) > 1:
                words.append(w)
    return Counter(words).most_common(n)


def channel_stats(videos: list[dict]) -> dict[str, dict]:
    stats: dict[str, dict] = {}
    for v in videos:
        ch = v.get("channel_name") or v.get("channel_handle") or "Unknown"
        if ch not in stats:
            stats[ch] = {"count": 0, "total_views": 0, "titles": []}
        stats[ch]["count"] += 1
        stats[ch]["total_views"] += v.get("view_count") or 0
        stats[ch]["titles"].append(v["title"])
    for ch in stats:
        stats[ch]["avg_views"] = stats[ch]["total_views"] // max(stats[ch]["count"], 1)
    return stats


def upload_trend(videos: list[dict]) -> dict[str, int]:
    trend: dict[str, int] = {}
    for v in videos:
        d = v.get("upload_date", "")
        if len(d) >= 6:
            ym = f"{d[:4]}-{d[4:6]}"
            trend[ym] = trend.get(ym, 0) + 1
    return dict(sorted(trend.items()))


def tag_freq(videos: list[dict], n: int = 20) -> list[tuple[str, int]]:
    tags: list[str] = []
    for v in videos:
        tags.extend(t.lower() for t in (v.get("tags") or []))
    return Counter(tags).most_common(n)


# ── URL 목록 생성 ────────────────────────────────────────────────────────────

def build_url_list(videos: list[dict]) -> str:
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M")
    tops = sorted(videos, key=lambda x: x["view_count"], reverse=True)
    lines = [
        "# YouTube 순위별 URL 목록",
        f"# 기준: 조회수 높은 순 | 생성: {ts} | 총 {len(tops)}개",
        "",
    ]
    for i, v in enumerate(tops, 1):
        vid_id = v.get("id", "")
        url    = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else "(URL 없음)"
        ch     = (v.get("channel_name") or "")[:28]
        title  = v["title"][:60]
        views  = v.get("view_count") or 0
        date   = v.get("upload_date", "")
        date_f = f"{date[:4]}-{date[4:6]}-{date[6:8]}" if len(date) == 8 else ""
        lines.append(f"{i:3}. [{views:>10,}] {ch:<28}  {date_f}  {title}")
        lines.append(f"     {url}")
        lines.append("")
    return "\n".join(lines)


# ── 마크다운 리포트 생성 ─────────────────────────────────────────────────────

def build_report(videos: list[dict], source_file: str) -> str:
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M")
    tops   = top_videos(videos, 20)
    kw     = keyword_freq(videos, 30)
    ch_s   = channel_stats(videos)
    trend  = upload_trend(videos)
    tags   = tag_freq(videos, 20)

    lines = [
        f"# AI 음악 채널 벤치마킹 리포트",
        f"> 생성: {ts} | 소스: `{source_file}` | 영상 수: {len(videos)}개",
        "",
        "---",
        "",
        "## 1. 조회수 TOP 20",
        "",
        "| # | 제목 | 채널 | 조회수 | 날짜 |",
        "|---|------|------|--------|------|",
    ]
    for i, v in enumerate(tops, 1):
        title  = v["title"][:45].replace("|", "\\|")
        ch     = (v.get("channel_name") or "")[:20]
        views  = f"{v['view_count']:,}"
        date   = v.get("upload_date", "")
        date_f = f"{date[:4]}-{date[4:6]}-{date[6:8]}" if len(date) == 8 else date
        vid_id = v.get("id", "")
        url    = f"https://www.youtube.com/watch?v={vid_id}" if vid_id else ""
        title_link = f"[{title}]({url})" if url else title
        lines.append(f"| {i} | {title_link} | {ch} | {views} | {date_f} |")

    lines += [
        "",
        "---",
        "",
        "## 2. 채널별 통계",
        "",
        "| 채널 | 영상 수 | 평균 조회수 | 총 조회수 |",
        "|------|---------|------------|----------|",
    ]
    for ch, s in sorted(ch_s.items(), key=lambda x: x[1]["total_views"], reverse=True):
        lines.append(
            f"| {ch[:30]} | {s['count']} | {s['avg_views']:,} | {s['total_views']:,} |"
        )

    lines += [
        "",
        "---",
        "",
        "## 3. 제목 키워드 TOP 30",
        "",
        "| 키워드 | 빈도 | 키워드 | 빈도 |",
        "|--------|------|--------|------|",
    ]
    for i in range(0, len(kw), 2):
        w1, c1 = kw[i]
        w2, c2 = kw[i + 1] if i + 1 < len(kw) else ("", "")
        lines.append(f"| `{w1}` | {c1} | `{w2}` | {c2} |")

    lines += [
        "",
        "---",
        "",
        "## 4. 월별 업로드 트렌드",
        "",
        "| 월 | 영상 수 | 추세 |",
        "|----|---------|------|",
    ]
    max_count = max(trend.values(), default=1)
    for ym, cnt in trend.items():
        bar = "█" * int(cnt / max_count * 20)
        lines.append(f"| {ym} | {cnt} | {bar} |")

    lines += [
        "",
        "---",
        "",
        "## 5. 인기 태그 TOP 20",
        "",
        "| 태그 | 빈도 |",
        "|------|------|",
    ]
    for tag, cnt in tags:
        lines.append(f"| `{tag}` | {cnt} |")

    lines += [
        "",
        "---",
        "",
        "## 6. 내 채널 개선 인사이트",
        "",
        "### 제목 패턴",
        f"- 상위 키워드: `{'`, `'.join(w for w, _ in kw[:5])}`",
        "- 조회수 상위 영상 제목 분석 결과를 참고해 제목 공식 도출",
        "",
        "### 썸네일",
        "- `python collect.py thumb` 실행 → `output/thumbnails/` 에서 시각 스타일 비교",
        "",
        "### 업로드 주기",
        f"- 가장 활발한 달: {max(trend, key=trend.get) if trend else 'N/A'}",
        "",
        "### 태그 전략",
        f"- 핵심 태그: `{'`, `'.join(t for t, _ in tags[:5])}`",
    ]

    return "\n".join(lines)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) > 1:
        src = Path(sys.argv[1])
    else:
        raw_files = sorted(OUTPUT_RAW.glob("*.json"), reverse=True)
        if not raw_files:
            print("raw JSON 없음 - 먼저 python collect.py 실행")
            return
        src = raw_files[0]

    print(f"[분석] {src.name}")
    raw = json.loads(src.read_text(encoding="utf-8"))

    # 중복 제거 (video id 기준)
    seen, videos = set(), []
    for v in raw:
        if v.get("id") and v["id"] not in seen:
            seen.add(v["id"])
            videos.append(v)
    if len(raw) != len(videos):
        print(f"  중복 제거: {len(raw)}개 -> {len(videos)}개")

    videos, dropped = filter_ai_channels(videos)
    if dropped:
        print(f"  비AI 채널 제외: {dropped}개 제거 -> {len(videos)}개 남음")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    report  = build_report(videos, src.name)
    out     = OUTPUT_REPORTS / f"report_{ts}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"[리포트] {out}")

    url_list = build_url_list(videos)
    url_out  = OUTPUT_REPORTS / f"urls_{ts}.txt"
    url_out.write_text(url_list, encoding="utf-8")
    print(f"[URL 목록] {url_out}")


if __name__ == "__main__":
    main()
