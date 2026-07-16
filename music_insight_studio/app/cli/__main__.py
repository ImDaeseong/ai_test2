from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.core import AnalysisMode, TrackInput, Verdict
from app.services import AnalysisService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="music-insight", description="Analyze a music file and generate reports.")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Analyze one audio file")
    analyze.add_argument("audio", type=Path, help="Path to MP3/WAV/FLAC file. WAV works in stdlib MVP.")
    analyze.add_argument("--out", type=Path, default=Path("outputs"), help="Output directory")
    analyze.add_argument("--mode", choices=[mode.value for mode in AnalysisMode], default=AnalysisMode.AUTO.value)
    analyze.add_argument("--lyrics", type=Path, default=None, help="Optional lyrics text file")
    analyze.add_argument("--prompt", type=Path, default=None, help="Optional prompt text file")
    analyze.add_argument("--target", default="general", help="Target platform or context")
    return parser


def read_optional(path: Path | None) -> str:
    return "" if path is None else path.read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        track = TrackInput(args.audio, AnalysisMode(args.mode), read_optional(args.lyrics), read_optional(args.prompt), args.target)
        service = AnalysisService()
        report = service.analyze(track)
        paths = service.write_reports(report, args.out)
        score = "N/A" if report.overall_score is None else f"{report.overall_score:.1f}"
        print(f"verdict={report.overall_verdict.value} score={score}")
        for path in paths:
            print(path)
        return 2 if report.overall_verdict == Verdict.HOLD else 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
