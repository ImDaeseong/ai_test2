"""Print the verified media capability and local implementation matrix."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence


CAPABILITIES: dict[str, dict[str, str]] = {
    "threads": {"text": "YES", "image": "YES", "video": "YES", "audio": "NO_STANDALONE", "file": "NO", "local": "TEXT_IMAGE_VIDEO"},
    "instagram": {"text": "CAPTION_ONLY", "image": "YES", "video": "YES_REELS_STORIES_CONDITIONAL", "audio": "NO_STANDALONE", "file": "NO", "local": "IMAGE_VIDEO_REELS_STORIES_OFFLINE"},
    "telegram": {"text": "YES", "image": "YES", "video": "YES", "audio": "YES", "file": "YES", "local": "TEXT_IMAGE_VIDEO"},
    "tiktok": {"text": "CAPTION_ONLY", "image": "YES", "video": "YES", "audio": "NO_STANDALONE", "file": "NO", "local": "PHOTO_VIDEO_OFFLINE_POLICY_HOLD"},
    "x": {"text": "YES", "image": "YES", "video": "YES", "audio": "NO_STANDALONE", "file": "NO", "local": "TEXT_ONLY_MEDIA_UPLOAD_HOLD"},
    "kakao": {"text": "YES_MESSAGE", "image": "YES_TEMPLATE", "video": "LINK_ONLY", "audio": "LINK_ONLY", "file": "NO", "local": "SEND_TO_SELF_TEXT_LINK"},
    "naver": {"text": "MANUAL_SHARE_TITLE", "image": "MANUAL", "video": "MANUAL", "audio": "MANUAL", "file": "MANUAL", "local": "SHARE_UI_ONLY"},
    "naver_cafe": {"text": "YES", "image": "YES_MULTIPART", "video": "APP_SCHEME_MANUAL", "audio": "APP_SCHEME_MANUAL", "file": "APP_SCHEME_MANUAL", "local": "TEXT_LINK"},
    "facebook_page": {"text": "YES", "image": "YES", "video": "YES_REELS_CONDITIONAL", "audio": "NO_STANDALONE", "file": "NO", "local": "TEXT_LINK_IMAGE_VIDEO_OFFLINE"},
    "youtube": {"text": "NO_COMMUNITY_WRITE_API", "image": "NO_COMMUNITY_WRITE_API", "video": "YES", "audio": "VIDEO_CONTAINER_ONLY", "file": "NO", "local": "BOUNDARY_ONLY_UPLOAD_HOLD"},
    "linkedin": {"text": "YES", "image": "YES", "video": "YES", "audio": "NO_STANDALONE", "file": "YES_DOCUMENT", "local": "TEXT_PREUPLOADED_ASSET_URN"},
    "discord": {"text": "YES", "image": "YES", "video": "YES", "audio": "YES", "file": "YES", "local": "TEXT_REMOTE_LINK_EMBED"},
    "reddit": {"text": "YES", "image": "YES", "video": "YES", "audio": "NO_NATIVE", "file": "NO_NATIVE", "local": "TEXT_LINK"},
}

PLATFORM_LABELS = {
    "threads": "Threads", "instagram": "Instagram", "telegram": "Telegram",
    "tiktok": "TikTok", "x": "X", "kakao": "KakaoTalk", "naver": "Naver 공유",
    "naver_cafe": "Naver Cafe", "facebook_page": "Facebook Page", "youtube": "YouTube",
    "linkedin": "LinkedIn", "discord": "Discord", "reddit": "Reddit",
}


def render_markdown() -> str:
    """Render a compact human-readable capability table."""
    lines = ["| 플랫폼 | 글 | 이미지 | 영상 | 음악/오디오 | 일반 파일 | 현재 코드 |", "|---|---|---|---|---|---|---|"]
    for platform, row in CAPABILITIES.items():
        lines.append(f"| {platform} | {row['text']} | {row['image']} | {row['video']} | {row['audio']} | {row['file']} | {row['local']} |")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Print the full matrix or one platform without making network calls."""
    parser = argparse.ArgumentParser(description="공식 미디어 지원 및 현재 구현 범위")
    parser.add_argument("--platform", choices=sorted(CAPABILITIES))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    selected = {args.platform: CAPABILITIES[args.platform]} if args.platform else CAPABILITIES
    print(json.dumps(selected, ensure_ascii=False, indent=2) if args.json else render_markdown() if not args.platform else render_markdown_for(args.platform))
    return 0


def render_markdown_for(platform: str) -> str:
    """Render one platform using the same column contract as the full table."""
    row = CAPABILITIES[platform]
    return "\n".join([
        "| 플랫폼 | 글 | 이미지 | 영상 | 음악/오디오 | 일반 파일 | 현재 코드 |",
        "|---|---|---|---|---|---|---|",
        f"| {platform} | {row['text']} | {row['image']} | {row['video']} | {row['audio']} | {row['file']} | {row['local']} |",
    ])


if __name__ == "__main__":
    raise SystemExit(main())
