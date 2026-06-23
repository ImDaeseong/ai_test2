"""
rank_channels.py  -  수집된 raw JSON에서 채널 조회수 랭킹 출력
사용법: python rank_channels.py [raw_json_파일]  (생략 시 최신 파일 자동 선택)
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT       = Path(__file__).parent
OUTPUT_RAW = ROOT / "output" / "raw"

# analyze.py와 동일한 AI 채널 필터 적용
try:
    from analyze import filter_ai_channels
    _FILTER_AVAILABLE = True
except ImportError:
    _FILTER_AVAILABLE = False


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

    print(f"[소스] {src.name}")
    videos = json.loads(src.read_text(encoding="utf-8"))

    if _FILTER_AVAILABLE:
        videos, dropped = filter_ai_channels(videos)
        if dropped:
            print(f"  비AI 채널 {dropped}개 제외 -> {len(videos)}개 남음")

    channels: dict = defaultdict(lambda: {"count": 0, "views": 0, "handle": ""})
    seen_ids: dict = defaultdict(set)

    for d in videos:
        ch     = d.get("channel_name") or d.get("channel_handle") or "Unknown"
        handle = d.get("channel_handle", "")
        vid_id = d.get("id", "")
        views  = d.get("view_count") or 0

        if vid_id and vid_id in seen_ids[ch]:
            continue
        if vid_id:
            seen_ids[ch].add(vid_id)

        channels[ch]["count"] += 1
        channels[ch]["views"] += views
        if handle and not channels[ch]["handle"]:
            channels[ch]["handle"] = handle

    ranked = sorted(channels.items(), key=lambda x: x[1]["views"], reverse=True)
    print(f"총 채널 수: {len(ranked)}\n")
    for i, (name, s) in enumerate(ranked[:25], 1):
        avg = s["views"] // max(s["count"], 1)
        print(
            f"{i:2}. {s['views']:>12,}  avg {avg:>9,}  "
            f"{s['count']}편  {name[:40]:<40}  {s['handle']}"
        )


if __name__ == "__main__":
    main()
