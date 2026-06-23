"""
validate_output.py — 생성된 이미지/영상 프롬프트 전수 검증 스크립트.

run_all.bat에서 create-all 완료 후 자동 실행된다.
수동 실행: python validate_output.py

검증 항목:
  1. 장르 프로파일 매칭 분포 (미매칭 곡 탐지)
  2. 이미지 프롬프트(03~08) 록/메탈 잔여 표현 전수 검사
  3. placeholder 잔여·누락 파일 점검 (summarize-all)
  4. 최종 PASS / FAIL 결과 출력
"""

from __future__ import annotations

import sys
from pathlib import Path

# Windows 콘솔 출력 인코딩 강제 UTF-8 (한글 깨짐 방지)
if sys.platform == "win32":
    for _stream in ("stdout", "stderr"):
        _s = getattr(sys, _stream, None)
        if hasattr(_s, "reconfigure"):
            try:
                _s.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

# ── 경로 설정 ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from main import (
    parse_song,
    song_slug,
    positive_tag_text,
    strip_inline_notes,
    _match_profile,
    summarize_prompt_outputs,
    POLICY_RISK_TERMS,
)

INPUT_DIR  = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

# 이미지 프롬프트 파일 목록 (영상 프롬프트 제외)
IMAGE_FILES = [
    "03_vocal_image_prompt.md",
    "04_guitar_image_prompt.md",
    "05_bass_image_prompt.md",
    "06_drum_image_prompt.md",
    "07_stage_image_prompt.md",
    "08_atmosphere_image_prompt.md",
]

# 이미지 프롬프트 잔여 표현 — 비록 장르에 남아 있으면 안 되는 문자열
IMAGE_METAL_RESIDUES = [
    "dark synthwave metal concert atmosphere",
    "dark synthwave metal atmosphere",
    "fast energetic performance feeling",
    "dynamic low-angle camera shot",
    "smoke, sparks, laser beams, intense stage lighting",
    "powerful low-end concert atmosphere",
    "epic live concert scale",
    "epic festival-scale live performance atmosphere",
    "high contrast dark synthwave metal lighting",
    "powerful rhythm and impact",
    "heavy smoke and sparks around the vocalist",
]

# 영상 프롬프트 잔여 표현 — 비록 장르에 남아 있으면 안 되는 문자열
VIDEO_METAL_RESIDUES = [
    "screams aggressively into the chained microphone",
    "performs an aggressive guitar solo",
    "concert crowd jumping, cheering, and headbanging",
    "headbanging",
    "intense live performance energy",
]

PROMPT_FILES = [
    "01_master_style_prompt.md",
    "02_style_lock_prompt.md",
    "03_vocal_image_prompt.md",
    "04_guitar_image_prompt.md",
    "05_bass_image_prompt.md",
    "06_drum_image_prompt.md",
    "07_stage_image_prompt.md",
    "08_atmosphere_image_prompt.md",
    "09_video_motion_prompts.md",
]

# 영상 프롬프트 필수 구조 — 모든 곡에 반드시 존재해야 하는 섹션
VIDEO_REQUIRED_SECTIONS = [
    "Kling Production Rule",
    "Motion Variants Per Image",
    "CapCut Editing Map",
    "Vocal Variants",
]

# 별칭 유지 (이미지 잔여 체크 함수에서 사용)
METAL_RESIDUES = IMAGE_METAL_RESIDUES

# ── 미적용 장르 감지 정의 ────────────────────────────────────────────────────
# 미적용장르.md에 정의된 장르와 동기화.
# 각 항목: (표시명, 정규식 패턴, 우선순위, 추가 권장 기준 곡 수)
UNAPPLIED_GENRES: list[tuple[str, str, str, int]] = [
    # 우선순위 B — 기존으로 대체 가능하나 부정확
    ("gospel",       r"\bgospel\b",                "B", 10),
    ("dark pop",     r"\bdark\s+pop\b",            "B", 10),
    ("tropical pop", r"\btropical\b(?!\s+house)",  "B", 10),
    # 우선순위 C — 추가 불필요 (감지만, 경고 없음)
    ("uk garage",    r"\buk\s+garage\b",           "C",  0),
    ("jersey club",  r"\bjersey\s+club\b",         "C",  0),
    ("future bass",  r"\bfuture\s+bass\b",         "C",  0),
    ("grunge",       r"\bgrunge\b",                "C",  0),
    ("shoegaze",     r"\bshoegaze\b",              "C",  0),
    ("blues",        r"\bblues\b",                 "C",  0),
    ("drum and bass",r"\bdrum\s+and\s+bass\b|\bdnb\b", "C", 0),
    # 프로파일 추가 완료 — 감지만 (경고 없음)
    ("ambient",      r"\bambient\b",              "C",  0),
    ("neo-soul",     r"\bneo[-\s]?soul\b",         "C",  0),
    ("folk",         r"\bfolk\b",                  "C",  0),
    ("psychedelic",  r"\bpsychedelic\b",            "C",  0),
    ("jazz",         r"\bjazz\b|\bbossa nova\b",   "C",  0),
    ("lo-fi hip hop",r"\blo[-\s]fi\s+hip[-\s]?hop\b", "C", 0),
]

SEP = "=" * 60


def _clean_lower(song) -> str:
    """섹션 헤더 제거 후 소문자 텍스트 반환 (profile 매칭용)."""
    return positive_tag_text(strip_inline_notes(song.raw_text)).lower()


def check_genre_profiles(songs: list) -> tuple[dict, list]:
    """장르 프로파일 분포와 미매칭 곡 목록 반환."""
    distribution: dict[str, int] = {}
    no_match: list[str] = []

    for song in songs:
        lower = _clean_lower(song)
        profile = _match_profile(lower)
        name = profile["name"] if profile else "defaults(미매칭)"
        distribution[name] = distribution.get(name, 0) + 1
        if not profile:
            no_match.append(song.title)

    return distribution, no_match


def check_residue(songs: list) -> list[str]:
    """이미지 프롬프트 잔여 표현 전수 검사. 문제 목록 반환."""
    issues: list[str] = []
    seen: set[str] = set()  # 곡 단위 중복 제거

    for song in songs:
        lower = _clean_lower(song)
        profile = _match_profile(lower)
        profile_name = profile["name"] if profile else "defaults"
        is_rock = profile_name == "rock"
        if is_rock:
            continue  # rock은 잔여 표현 유지가 정상

        folder = OUTPUT_DIR / song_slug(song.title)
        if not folder.exists():
            key = f"[MISSING_FOLDER] {song.title}"
            if key not in seen:
                issues.append(key)
                seen.add(key)
            continue

        for img_file in IMAGE_FILES:
            path = folder / img_file
            if not path.exists():
                key = f"[MISSING_FILE] {song.title} / {img_file}"
                if key not in seen:
                    issues.append(key)
                    seen.add(key)
                continue
            text = path.read_text(encoding="utf-8").lower()
            for residue in METAL_RESIDUES:
                if residue in text:
                    key = f"[RESIDUE] {song.title} ({profile_name}) / {img_file[:8]}: {residue[:40]}"
                    if key not in seen:
                        issues.append(key)
                        seen.add(key)

    return issues


def check_video_prompts(songs: list) -> tuple[list[str], list[str]]:
    """09_video_motion_prompts.md 검증.

    Returns:
        residue_issues: 비록 장르 곡에 남은 잔여 표현
        structure_issues: 필수 구조 섹션 누락
    """
    residue_issues: list[str] = []
    structure_issues: list[str] = []
    seen_res: set[str] = set()

    for song in songs:
        lower = _clean_lower(song)
        profile = _match_profile(lower)
        profile_name = profile["name"] if profile else "defaults"
        is_rock = profile_name == "rock"

        folder = OUTPUT_DIR / song_slug(song.title)
        video_path = folder / "09_video_motion_prompts.md"

        if not folder.exists() or not video_path.exists():
            continue  # 폴더·파일 누락은 [3] 섹션에서 처리

        text = video_path.read_text(encoding="utf-8")
        text_lower = text.lower()

        # ── 잔여 표현: 비록 장르에서만 체크 ────────────────────────────────
        if not is_rock:
            for residue in VIDEO_METAL_RESIDUES:
                if residue in text_lower:
                    key = f"[VIDEO_RESIDUE] {song.title} ({profile_name}): {residue[:45]}"
                    if key not in seen_res:
                        residue_issues.append(key)
                        seen_res.add(key)

        # ── 구조 무결성: 모든 곡 체크 ───────────────────────────────────────
        for section in VIDEO_REQUIRED_SECTIONS:
            if section not in text:
                key = f"[VIDEO_MISSING] {song.title}: '{section}' 섹션 없음"
                if key not in seen_res:
                    structure_issues.append(key)
                    seen_res.add(key)

    return residue_issues, structure_issues


def check_policy_safety(songs: list) -> list[str]:
    """플랫폼 정책 오탐 가능성이 큰 표현이 출력 프롬프트에 남았는지 검사."""
    issues: list[str] = []
    seen: set[str] = set()
    for song in songs:
        folder = OUTPUT_DIR / song_slug(song.title)
        if not folder.exists():
            continue
        for file_name in PROMPT_FILES:
            path = folder / file_name
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for term in POLICY_RISK_TERMS:
                if term in text:
                    key = f"[POLICY_RISK] {song.title} / {file_name}: {term}"
                    if key not in seen:
                        issues.append(key)
                        seen.add(key)
    return issues


def check_unapplied_genres(songs: list) -> list[str]:
    """미적용 장르 감지: input 폴더에서 미적용장르.md의 장르를 스캔.

    우선순위 A/B 장르가 추가 기준 곡 수를 초과하면 경고를 반환한다.
    우선순위 C 는 참고 정보로만 출력 (warnings에 포함하지 않음).
    """
    import re as _re

    # 장르별 발견 곡 목록 수집
    detected: dict[str, list[str]] = {name: [] for name, *_ in UNAPPLIED_GENRES}

    for song in songs:
        genre_lower = song.genre.lower()
        for name, pattern, priority, threshold in UNAPPLIED_GENRES:
            if _re.search(pattern, genre_lower, _re.I):
                detected[name].append(song.title)

    warnings: list[str] = []
    info_lines: list[str] = []

    for name, pattern, priority, threshold in UNAPPLIED_GENRES:
        count = len(detected[name])
        if count == 0:
            continue

        examples = ", ".join(detected[name][:3])
        if len(detected[name]) > 3:
            examples += f" 외 {count - 3}곡"

        if priority == "C":
            info_lines.append(f"  [정보] {name}: {count}곡 — 기존 프로파일로 처리 충분")
        elif count >= threshold:
            warnings.append(
                f"  [권고] {name} (우선순위 {priority}): {count}곡 발견 "
                f"(기준 {threshold}곡 초과) → genre_profiles.json 추가 고려\n"
                f"         예: {examples}"
            )
        else:
            info_lines.append(
                f"  [참고] {name} (우선순위 {priority}): {count}곡 "
                f"(기준 {threshold}곡 미만, 아직 추가 불필요) — {examples}"
            )

    return warnings + (["  " + "-" * 50] + info_lines if info_lines else [])


def check_placeholder_and_lock() -> list[str]:
    """summarize-all을 이용한 placeholder·identity lock 검사."""
    rows, _ = summarize_prompt_outputs(INPUT_DIR, OUTPUT_DIR)
    failed = [f"[VALIDATION] {row['title']}: {row['errors']}"
              for row in rows if row.get("errors")]
    return failed


def check_orphan_outputs(songs: list) -> list[str]:
    """input에 대응하는 txt가 없는 output 폴더 탐지."""
    input_slugs = {song_slug(song.title) for song in songs}
    orphans: list[str] = []
    for folder in sorted(OUTPUT_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if folder.name.startswith("_"):  # _ALL_PROMPT_OVERVIEW.md 등 전역 파일 제외
            continue
        if folder.name not in input_slugs:
            orphans.append(f"[ORPHAN] {folder.name}")
    return orphans


def main() -> int:
    print(SEP)
    print("  AI Image/Video Prompt — 전수 품질 검증")
    print(SEP)

    # ── 입력 파일 로드 ─────────────────────────────────────────────────────
    input_files = sorted(INPUT_DIR.glob("*.txt"))
    if not input_files:
        print("input/ 폴더에 .txt 파일이 없습니다.")
        return 1

    songs = []
    load_errors = []
    for f in input_files:
        try:
            songs.append(parse_song(f, title_fallback=f.stem))
        except Exception as e:
            load_errors.append(f"{f.stem}: {e}")

    print(f"\n입력 곡 수: {len(songs)}개")
    if load_errors:
        print(f"로드 오류 {len(load_errors)}건:")
        for e in load_errors:
            print(f"  ✗ {e}")

    total_failures = 0

    # ── 1. 장르 프로파일 분포 ────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  [1] 장르 프로파일 분포")
    print(SEP)
    distribution, no_match = check_genre_profiles(songs)
    for name, count in sorted(distribution.items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 40)
        print(f"  {name:<22} {count:3d}곡  {bar}")

    if no_match:
        print(f"\n  ⚠ 미매칭 곡 {len(no_match)}개 (defaults 프로파일 사용):")
        for title in no_match:
            print(f"    - {title}")
        total_failures += len(no_match)
    else:
        print("\n  ✓ 전곡 프로파일 매칭 완료")

    # ── 2. 잔여 표현 전수 검사 ───────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  [2] 이미지 프롬프트 록/메탈 잔여 표현 검사 (03~08번)")
    print(SEP)
    residue_issues = check_residue(songs)
    if residue_issues:
        print(f"  ✗ 잔여 표현 발견: {len(residue_issues)}건")
        for issue in residue_issues[:20]:
            print(f"    {issue}")
        if len(residue_issues) > 20:
            print(f"    ... 외 {len(residue_issues) - 20}건")
        total_failures += len(residue_issues)
    else:
        print(f"  ✓ 전 {len(songs)}곡 잔여 표현 없음")

    # ── 3. 영상 프롬프트 잔여 표현 + 구조 무결성 ────────────────────────────
    print(f"\n{SEP}")
    print("  [3] 영상 프롬프트 검사 (09번) — 잔여 표현 + 필수 구조")
    print(SEP)
    video_residue, video_structure = check_video_prompts(songs)
    if video_residue:
        print(f"  ✗ 영상 잔여 표현 {len(video_residue)}건:")
        for issue in video_residue[:15]:
            print(f"    {issue}")
        if len(video_residue) > 15:
            print(f"    ... 외 {len(video_residue) - 15}건")
        total_failures += len(video_residue)
    else:
        print(f"  ✓ 전 {len(songs)}곡 영상 잔여 표현 없음")

    if video_structure:
        print(f"  ✗ 필수 구조 누락 {len(video_structure)}건:")
        for issue in video_structure[:15]:
            print(f"    {issue}")
        total_failures += len(video_structure)
    else:
        print(f"  ✓ 전 {len(songs)}곡 영상 구조 무결성 확인")

    # ── 4. placeholder · identity lock 검사 ─────────────────────────────────
    print(f"\n{SEP}")
    print("  [4] placeholder 잔여 · 캐릭터 고정 문장 검사")
    print(SEP)
    validation_issues = check_placeholder_and_lock()
    if validation_issues:
        print(f"  ✗ 검증 실패: {len(validation_issues)}건")
        for issue in validation_issues[:10]:
            print(f"    {issue}")
        total_failures += len(validation_issues)
    else:
        print(f"  ✓ 전 {len(songs)}곡 검증 통과")

    # ── 5. 정책 안전 표현 검사 ───────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  [5] 정책 안전 표현 검사")
    print(SEP)
    policy_issues = check_policy_safety(songs)
    if policy_issues:
        print(f"  ✗ 정책 위험 표현 발견: {len(policy_issues)}건")
        for issue in policy_issues[:20]:
            print(f"    {issue}")
        if len(policy_issues) > 20:
            print(f"    ... 외 {len(policy_issues) - 20}건")
        total_failures += len(policy_issues)
    else:
        print(f"  ✓ 전 {len(songs)}곡 정책 위험 표현 없음")

    # ── 6. 미적용 장르 감지 ──────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  [6] 미적용 장르 감지 (미적용장르.md 기준)")
    print(SEP)
    genre_lines = check_unapplied_genres(songs)
    warnings_only = [l for l in genre_lines if "[권고]" in l]
    if not genre_lines:
        print("  ✓ 미적용 장르 해당 곡 없음")
    else:
        for line in genre_lines:
            print(line)
    # 권고 건수를 failures에는 포함시키지 않음 (오류가 아닌 정보)
    if warnings_only:
        print(f"\n  → 위 권고 항목을 확인하고 필요하면 genre_profiles.json에 추가하세요.")

    # ── 7. orphan output 탐지 ────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  [7] orphan output 탐지 (input 없는 output 폴더)")
    print(SEP)
    orphan_issues = check_orphan_outputs(songs)
    if orphan_issues:
        print(f"  ⚠ orphan 폴더 {len(orphan_issues)}개 (input .txt 없음):")
        for issue in orphan_issues:
            print(f"    {issue}")
        # orphan은 경고(warning)이지 오류가 아님 — total_failures에 포함 안 함
        print("  → 해당 폴더를 삭제하거나 input .txt를 복원하세요.")
    else:
        print(f"  ✓ orphan output 없음 (input {len(songs)}곡 = output 폴더 수 일치)")

    # ── 최종 결과 ────────────────────────────────────────────────────────────
    print(f"\n{SEP}")
    if total_failures == 0:
        print(f"  최종 결과: PASS  ✓  ({len(songs)}곡 전체 이상 없음)")
        print(f"  검증 항목: [1]프로파일 [2]이미지잔여 [3]영상잔여+구조 [4]placeholder [5]정책안전 [6]미적용장르 [7]orphan")
    else:
        print(f"  최종 결과: FAIL  ✗  (문제 {total_failures}건 발견)")
    print(SEP)

    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
