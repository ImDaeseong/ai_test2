"""
run.py  -  AI music channel research: collect + thumbnails + report
usage:
  python run.py [search|channel] [max_per_query]
"""

import json
import sys
from datetime import datetime

import collect as col
import analyze as ana


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    mode  = sys.argv[1] if len(sys.argv) > 1 else "search"
    max_n = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    config = json.loads(col.CHANNELS_FILE.read_text(encoding="utf-8"))
    all_v: list[dict] = []

    print(f"\n[1/3] Collecting ({mode}, max {max_n} per query)...", flush=True)

    if mode == "channel":
        for ch in config["channels"]:
            if "PLACEHOLDER" in ch["name"]:
                continue
            all_v.extend(col.collect_channel(ch, max_n))
    else:
        for q in config["search_queries"]:
            all_v.extend(col.collect_search(q, max_results=max_n))

    # 중복 제거 (video id 기준)
    seen, unique = set(), []
    for v in all_v:
        if v["id"] and v["id"] not in seen:
            seen.add(v["id"])
            unique.append(v)
    all_v = unique
    print(f"  -> {len(all_v)} videos collected", flush=True)

    raw_path = col.save_raw(all_v, mode)

    all_v, dropped = ana.filter_ai_channels(all_v)
    if dropped:
        print(f"  -> 비AI 채널 {dropped}개 제외 (AI 음악 유튜버만 포함)", flush=True)
    print(f"  -> {len(all_v)} AI 채널 영상 확정", flush=True)

    print("\n[2/3] Downloading thumbnails (TOP 10)...", flush=True)
    col.download_thumbnails(all_v, limit=10)

    print("\n[3/3] Generating report...", flush=True)
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    ana.OUTPUT_REPORTS.mkdir(parents=True, exist_ok=True)

    report = ana.build_report(all_v, raw_path.name)
    out    = ana.OUTPUT_REPORTS / f"report_{ts}.md"
    out.write_text(report, encoding="utf-8")
    print(f"  -> {out.name} saved", flush=True)

    url_list = ana.build_url_list(all_v)
    url_out  = ana.OUTPUT_REPORTS / f"urls_{ts}.txt"
    url_out.write_text(url_list, encoding="utf-8")
    print(f"  -> {url_out.name} saved", flush=True)
    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
