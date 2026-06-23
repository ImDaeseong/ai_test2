"""
youtube_research/collect.py
AI 음악 유튜브 채널 벤치마킹 - 메타데이터 수집기
사용법:
  python collect.py channel [max_videos]   # channels.json 채널 수집
  python collect.py search  [max_results]  # 키워드 검색 수집
  python collect.py thumb                  # 최신 raw JSON 기준 썸네일 다운로드
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
CHANNELS_FILE = ROOT / "channels.json"
OUTPUT_RAW    = ROOT / "output" / "raw"
OUTPUT_THUMB  = ROOT / "output" / "thumbnails"


# ── yt-dlp 경로 자동 탐지 ────────────────────────────────────────────────────

def _find_ytdlp() -> str:
    found = shutil.which("yt-dlp")
    if found:
        return found
    appdata = os.environ.get("APPDATA", "")
    pattern = os.path.join(appdata, "Python", "Python3*", "Scripts", "yt-dlp.exe")
    matches = sorted(glob.glob(pattern), reverse=True)  # 최신 버전 우선
    if matches:
        return matches[0]
    raise FileNotFoundError(
        "yt-dlp를 찾을 수 없습니다. 설치: pip install yt-dlp"
    )

YTDLP = _find_ytdlp()


# ── 내부 유틸 ────────────────────────────────────────────────────────────────

def _ytdlp(*args) -> str:
    r = subprocess.run(
        [YTDLP, *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if r.returncode != 0 and r.stderr:
        print(f"  [경고] yt-dlp 오류 (exit {r.returncode}): {r.stderr.strip()[:200]}", flush=True)
    return r.stdout


def _parse_jsonl(raw: str) -> list[dict]:
    rows = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def _normalize(data: dict, channel_name: str = "", channel_handle: str = "") -> dict:
    raw_handle = channel_handle or data.get("uploader_id") or ""
    return {
        "channel_name":   channel_name or data.get("channel") or "",
        "channel_handle": raw_handle.lstrip("@"),  # @ 제거로 모드 간 통일
        "id":             data.get("id") or "",
        "title":          data.get("title") or "",
        "url":            data.get("url") or data.get("webpage_url") or "",
        "view_count":     data.get("view_count") or 0,
        "upload_date":    data.get("upload_date") or "",
        "duration_sec":   data.get("duration") or 0,
        "tags":           data.get("tags") or [],
        "description":    (data.get("description") or "")[:300],
    }


# ── 수집 함수 ────────────────────────────────────────────────────────────────

def collect_channel(ch: dict, max_videos: int = 50) -> list[dict]:
    print(f"\n[채널] {ch['name']}  {ch['url']}")
    raw = _ytdlp(
        "--no-download", "--flat-playlist", "--print-json",
        f"--playlist-end={max_videos}",
        ch["url"],
    )
    rows = [_normalize(d, ch["name"], ch.get("handle", "")) for d in _parse_jsonl(raw)]
    print(f"  ->{len(rows)}개")
    time.sleep(1)
    return rows


def collect_search(query: str, max_results: int = 30) -> list[dict]:
    print(f"\n[검색] {query}")
    raw = _ytdlp(
        "--no-download", "--flat-playlist", "--print-json",
        f"--playlist-end={max_results}",
        query,
    )
    rows = [_normalize(d) for d in _parse_jsonl(raw)]
    print(f"  ->{len(rows)}개")
    time.sleep(1)
    return rows


def download_thumbnails(videos: list[dict], limit: int = 10):
    OUTPUT_THUMB.mkdir(parents=True, exist_ok=True)
    top = sorted(videos, key=lambda x: x["view_count"], reverse=True)[:limit]
    for v in top:
        vid_id = v.get("id", "")
        if not vid_id:
            continue
        url = f"https://www.youtube.com/watch?v={vid_id}"
        out = str(OUTPUT_THUMB / f"{vid_id}.%(ext)s")
        print(f"  {v['title'][:60]}")
        _ytdlp("--skip-download", "--write-thumbnail", "--convert-thumbnails", "jpg", "-o", out, url)
        time.sleep(1)


def save_raw(videos: list[dict], label: str) -> Path:
    OUTPUT_RAW.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_RAW / f"{label}_{ts}.json"
    path.write_text(json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[저장] {path}  ({len(videos)}개)")
    return path


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    mode    = sys.argv[1] if len(sys.argv) > 1 else "channel"
    max_n   = int(sys.argv[2]) if len(sys.argv) > 2 else 50

    config  = json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
    all_v: list[dict] = []

    if mode == "channel":
        for ch in config["channels"]:
            if "PLACEHOLDER" in ch["name"]:
                print(f"[건너뜀] {ch['name']} - channels.json 실제 채널로 교체 필요")
                continue
            all_v.extend(collect_channel(ch, max_n))

    elif mode == "search":
        for q in config["search_queries"]:
            all_v.extend(collect_search(q, max_results=max_n))

    elif mode == "thumb":
        raw_files = sorted(OUTPUT_RAW.glob("*.json"), reverse=True)
        if not raw_files:
            print("먼저 collect.py channel 또는 search 실행 필요")
            return
        all_v = json.loads(raw_files[0].read_text(encoding="utf-8"))
        print(f"[썸네일] {raw_files[0].name} 기준 상위 10개 다운로드")
        download_thumbnails(all_v, limit=10)
        return

    else:
        print(__doc__)
        return

    if all_v:
        # 중복 제거 (video id 기준)
        seen, unique = set(), []
        for v in all_v:
            if v["id"] and v["id"] not in seen:
                seen.add(v["id"])
                unique.append(v)
        print(f"\n완료 - 수집 {len(all_v)}개 -> 중복 제거 후 {len(unique)}개")
        save_raw(unique, mode)
        print("다음: python analyze.py")


if __name__ == "__main__":
    main()
