"""Report local platform configuration readiness without exposing secret values."""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Mapping, Sequence


REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "threads": ("THREADS_USER_ID", "THREADS_ACCESS_TOKEN"),
    "instagram": ("INSTAGRAM_USER_ID", "INSTAGRAM_ACCESS_TOKEN"),
    "telegram": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
    "tiktok": ("TIKTOK_ACCESS_TOKEN",),
    "x": ("X_USER_ACCESS_TOKEN",),
    "kakao": ("KAKAO_ACCESS_TOKEN",),
    "naver": (),
    "naver_cafe": ("NAVER_ACCESS_TOKEN", "NAVER_CAFE_ID", "NAVER_CAFE_MENU_ID"),
    "facebook_page": ("FACEBOOK_PAGE_ID", "FACEBOOK_PAGE_ACCESS_TOKEN"),
    "linkedin": ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_AUTHOR_URN"),
    "discord": ("DISCORD_WEBHOOK_URL",),
    "reddit": ("REDDIT_ACCESS_TOKEN", "REDDIT_SUBREDDIT"),
    "youtube": ("YOUTUBE_ACCESS_TOKEN",),
}

VALUE_PATTERNS: dict[str, str] = {
    "THREADS_USER_ID": r"^[0-9]+$",
    "INSTAGRAM_USER_ID": r"^[0-9]+$",
    "TELEGRAM_BOT_TOKEN": r"^[0-9]+:[A-Za-z0-9_-]{20,}$",
    "TELEGRAM_CHAT_ID": r"^(?:@[A-Za-z0-9_]{5,}|-?[0-9]+)$",
    "NAVER_CAFE_ID": r"^[0-9]+$",
    "NAVER_CAFE_MENU_ID": r"^[0-9]+$",
    "FACEBOOK_PAGE_ID": r"^[0-9]+$",
    "LINKEDIN_AUTHOR_URN": r"^urn:li:(?:person|organization):[A-Za-z0-9_-]+$",
    "DISCORD_WEBHOOK_URL": r"^https://(?:discord\.com|discordapp\.com)/api/webhooks/[0-9]+/[A-Za-z0-9._-]+$",
    "REDDIT_SUBREDDIT": r"^[A-Za-z0-9_]{3,21}$",
}


def invalid_environment_names(env: Mapping[str, str], keys: Sequence[str]) -> list[str]:
    """Return configured variable names whose values are placeholders or malformed."""
    invalid = []
    for key in keys:
        value = env.get(key, "").strip()
        if not value:
            continue
        pattern = VALUE_PATTERNS.get(key)
        if value.lower().startswith(("your_", "replace_", "example_")) or (pattern and re.fullmatch(pattern, value) is None):
            invalid.append(key)
    return invalid

LIMITATIONS = {
    "tiktok": "앱 감사 전 비공개 제한; 개인/사내 전용 업로더는 현재 공유 지침과 충돌 가능",
    "x": "텍스트/URL만 지원; v2 미디어 업로드 미구현; 실제 호출 전 비용 확인",
    "kakao": "본인 메시지 전송만 지원; 카카오채널 공개 게시가 아님",
    "naver": "사용자 공유 화면 전용; Blog 글쓰기 API 종료",
    "naver_cafe": "텍스트/링크 실행 지원; 공식 multipart 이미지 첨부는 미구현",
    "facebook_page": "Page 관리 권한·Page 토큰 필요; Reels 실물 검증 미완료",
    "linkedin": "텍스트 및 사전 업로드된 미디어 URN만 지원; 자산 업로드 미구현",
    "discord": "텍스트·원격 링크/임베드 지원; 실제 파일 multipart 업로드 미구현",
    "reddit": "텍스트·링크 지원; 이미지/영상 미디어 업로드 미구현",
    "youtube": "영상 업로드만 공식 지원 확인; resumable 파일 업로더 및 Community 글쓰기는 미구현",
}


def inspect_environment(env: Mapping[str, str]) -> dict[str, dict[str, object]]:
    """Return presence-only readiness results for every supported platform."""
    report: dict[str, dict[str, object]] = {}
    for platform, keys in REQUIREMENTS.items():
        missing = [key for key in keys if not env.get(key, "").strip()]
        invalid = invalid_environment_names(env, keys)
        report[platform] = {
            "local_config": "READY" if not missing and not invalid else "INVALID" if invalid else "MISSING",
            "missing": missing,
            "invalid": invalid,
            "limitation": LIMITATIONS.get(platform),
            "live_verified": False,
        }
    return report


def main(argv: Sequence[str] | None = None) -> int:
    """Print a secret-free readiness report and fail when selected configuration is missing."""
    parser = argparse.ArgumentParser(description="커뮤니티 연동 로컬 설정 점검(외부 API 호출 없음)")
    parser.add_argument("--platform", choices=sorted(REQUIREMENTS))
    args = parser.parse_args(argv)
    report = inspect_environment(os.environ)
    selected = {args.platform: report[args.platform]} if args.platform else report
    print(json.dumps(selected, ensure_ascii=False, indent=2))
    return 0 if all(item["local_config"] == "READY" for item in selected.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
