"""Provide a beginner-friendly dry-run-first command line interface."""

from __future__ import annotations

import argparse
import json
import logging

from community_integrations.publisher import ADAPTERS, HttpTransport, PublishError, PublishRequest, load_environment


def build_parser() -> argparse.ArgumentParser:
    """Build the community publisher command-line parser."""
    parser = argparse.ArgumentParser(description="공식 API 기반 커뮤니티 게시 도구(기본값: 미리보기)")
    parser.add_argument("platform", choices=sorted(ADAPTERS))
    parser.add_argument("--text", required=True)
    parser.add_argument("--media-url")
    parser.add_argument("--media-type")
    parser.add_argument("--title")
    parser.add_argument("--privacy-level")
    parser.add_argument("--media-id", help="플랫폼에 이미 업로드된 미디어 ID/URN")
    parser.add_argument("--execute", action="store_true", help="실제 API 요청을 전송합니다")
    parser.add_argument("--confirm", action="store_true", help="게시 내용을 사람이 최종 확인했음을 표시합니다")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Preview a request or execute it only after two explicit operator flags."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    content = PublishRequest(args.text, args.media_url, args.media_type, args.title, privacy_level=args.privacy_level, media_id=args.media_id)
    adapter = ADAPTERS[args.platform]
    try:
        preview = [item.safe_dict() for item in adapter.preview(content, load_environment())]
        if not args.execute:
            print(json.dumps({"mode": "DRY_RUN", "platform": args.platform, "requests": preview}, ensure_ascii=False, indent=2))
            return 0
        if not args.confirm:
            raise PublishError("실제 게시에는 --execute와 --confirm이 모두 필요합니다")
        result = adapter.publish(content, load_environment(), HttpTransport())
        print(json.dumps({"mode": "EXECUTED", "result": result}, ensure_ascii=False, indent=2))
        return 0
    except PublishError as exc:
        print(f"HOLD: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
