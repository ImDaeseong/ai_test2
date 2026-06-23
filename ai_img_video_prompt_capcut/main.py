#!/usr/bin/env python3
"""
ai_img_video_prompt_capcut
MV CapCut 타임라인 자동 생성

사용법:
    python main.py inspect      --song UPGRADE
    python main.py plan         --song UPGRADE
    python main.py build        --song UPGRADE  [--keep 3]
    python main.py build-all                    [--keep 3]
    python main.py export-draft --song UPGRADE  # CapCut PC 드래프트 자동 생성

입력 폴더 구조:
    input/{곡명}/
    ├─ {곡명}.wav / .mp3
    ├─ *.lrc          (Suno 가사 다운로더 파일)
    ├─ *.srt          (선택)
    └─ clips/
       ├─ vocal_A.mp4
       ├─ vocal_B.mp4
       ├─ vocal_C.mp4
       ├─ guitar_A.mp4
       ├─ guitar_B.mp4
       ├─ bass.mp4
       ├─ drum.mp4
       ├─ stage_A.mp4
       ├─ stage_B.mp4
       ├─ stage_C.mp4
       ├─ atmosphere_A.mp4
       └─ atmosphere_B.mp4
"""

import json
import re
import datetime
import shutil
import sys
from pathlib import Path
from typing import Optional

import click

# Windows 콘솔 UTF-8 출력
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf_8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ─── 경로 설정 ──────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
INPUT_ROOT = ROOT / "input"
OUTPUT_ROOT = ROOT / "output"
CONFIG_PATH = ROOT / "production_config.json"

# ─── 상수 ───────────────────────────────────────────────────────────────────

SECTION_RE = re.compile(
    r"^(intro|verse|pre.?chorus|post.?chorus|chorus|bridge|guitar\s*solo|solo|"
    r"outro|interlude|instrumental|breakdown|drop|hook|final\s*chorus)\s*\d*$",
    re.IGNORECASE,
)

LRC_LINE_RE = re.compile(r"\[(\d+):(\d+\.\d+)\](.*)")
SRT_TIME_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s+-->\s+(\d{2}):(\d{2}):(\d{2}),(\d{3})"
)
RUN_ID_RE = re.compile(r"^\d{8}_\d{6}$")


def _normalize_section_name(name: str) -> str:
    """Suno LRC 장식 섹션명 정규화 — 'explosive chorus' → 'Chorus' 등.
    Suno가 [explosive chorus], [build chorus] 처럼 수식어를 붙여 섹션을 표기할 때
    match_sections()가 인식할 수 있는 표준 섹션명으로 변환한다.
    'breath before chorus', 'build to chorus' 같은 전치사 수식 어노테이션은 건드리지 않는다.
    """
    nl = name.lower()
    if re.search(r"\bchorus\b", nl):
        # 'before/after/for/into/to chorus' 패턴은 퍼포먼스 어노테이션 → 정규화 안 함
        if re.search(r"\b(before|after|for|into|to|of|the)\s+chorus\b", nl):
            return name
        if re.search(r"\bpre\b", nl):
            return "Pre-Chorus"
        if re.search(r"\bpost\b", nl):
            return "Post-Chorus"
        if re.search(r"\bfinal\b", nl):
            return "Final Chorus"
        return "Chorus"
    return name


# ─── 오디오 / 영상 길이 ───────────────────────────────────────────────────────


def get_audio_duration_ms(path: Path) -> Optional[int]:
    # 1. mutagen (length > 0 검증 추가)
    try:
        from mutagen import File as MFile
        audio = MFile(str(path))
        if audio and audio.info and audio.info.length > 0:
            return int(audio.info.length * 1000)
    except ImportError:
        pass
    except Exception:
        pass

    # 2. ffprobe 폴백 (AI 생성 mp4 등 mutagen이 0을 반환할 때)
    try:
        import subprocess
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return int(float(r.stdout.strip()) * 1000)
    except (FileNotFoundError, Exception):
        pass

    # 3. wav 전용 폴백
    if path.suffix.lower() == ".wav":
        try:
            import wave
            with wave.open(str(path), "r") as wf:
                return int(wf.getnframes() / wf.getframerate() * 1000)
        except Exception:
            pass

    return None


def get_clip_durations(song_dir: Path) -> dict:
    """clips/ mp4 파일 실제 길이 → {정규화된_이름: duration_ms}
    mutagen 없으면 빈 dict 반환 (경고 없이 스킵).
    """
    clips_dir = song_dir / "clips"
    if not clips_dir.exists():
        return {}
    result = {}
    for f in sorted(clips_dir.glob("*.mp4")):
        key = f.stem.lower().replace("-", "_").replace(" ", "_")
        dur = get_audio_duration_ms(f)
        if dur is not None:
            result[key] = dur
    return result


# ─── 파일 탐색 ───────────────────────────────────────────────────────────────


def find_audio(song_dir: Path) -> Optional[Path]:
    for ext in ("*.wav", "*.mp3", "*.m4a", "*.flac"):
        found = list(song_dir.glob(ext))
        if found:
            return found[0]
    return None


def find_image(song_dir: Path, song_name: str = "") -> Optional[Path]:
    """배경 이미지 탐색: {name}_bg > {name} > 아무 이미지"""
    for suffix in (".png", ".jpg", ".jpeg"):
        if song_name:
            p = song_dir / f"{song_name}_bg{suffix}"
            if p.exists():
                return p
    for suffix in (".png", ".jpg", ".jpeg"):
        if song_name:
            p = song_dir / f"{song_name}{suffix}"
            if p.exists():
                return p
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        found = list(song_dir.glob(ext))
        if found:
            return found[0]
    return None


def find_lrc(song_dir: Path) -> Optional[Path]:
    found = list(song_dir.glob("*.lrc"))
    return found[0] if found else None


def find_srt(song_dir: Path) -> Optional[Path]:
    """기본 SRT (영어 전용 파일 제외)"""
    found = [f for f in song_dir.glob("*.srt") if "_en." not in f.name.lower()]
    return found[0] if found else None


def find_srt_en(song_dir: Path) -> Optional[Path]:
    """영어 자막 SRT — *_en.srt 패턴"""
    found = list(song_dir.glob("*_en.srt"))
    return found[0] if found else None


def find_motion_prompts(song_dir: Path) -> Optional[Path]:
    """*_video_motion_prompts.md 탐색"""
    found = list(song_dir.glob("*_video_motion_prompts.md"))
    return found[0] if found else None


def parse_srt(srt_path: Path) -> list:
    """SRT → [{start_ms, end_ms, text}, ...]
    Suno SRT는 두 형태가 있다:
      형태 A (2-part): Part1(압축) + [End] 마커 + Part2(실제 가사)
      형태 B (1-part): [End] 없이 처음부터 실제 가사 타임스탬프
    [End] 존재 여부를 먼저 확인해 두 형태 모두 처리한다.
    """
    content = srt_path.read_text(encoding="utf-8", errors="ignore")
    blocks = [b.strip() for b in content.split("\n\n") if b.strip()]

    has_end_marker = bool(re.search(r"^\[End\]$", content, re.IGNORECASE | re.MULTILINE))
    past_end = not has_end_marker  # [End] 없으면 처음부터 수집
    entries = []

    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3:
            continue

        m = SRT_TIME_RE.match(lines[1].strip())
        if not m:
            continue

        text = "\n".join(lines[2:]).strip()

        if re.match(r"^\[End\]$", text, re.IGNORECASE):
            past_end = True
            continue

        if not past_end:
            continue

        if not text or re.match(r"^\[.*\]$", text):
            continue

        g = m.groups()
        start_ms = (int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2])) * 1000 + int(g[3])
        end_ms   = (int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6])) * 1000 + int(g[7])

        if end_ms - start_ms < 100:
            continue

        entries.append({"start_ms": start_ms, "end_ms": end_ms, "text": text})

    return entries


def parse_capcut_map_from_md(md_path: Path) -> Optional[dict]:
    """*_video_motion_prompts.md의 ## CapCut Editing Map 코드블록 파싱
    성공 시 capcut_map dict 반환, 없으면 None
    """
    content = md_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(
        r"##\s+CapCut Editing Map[\s\S]*?```(?:text)?\n([\s\S]*?)```",
        content,
        re.IGNORECASE,
    )
    if not m:
        return None
    capcut_map: dict = {}
    for line in m.group(1).strip().splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, shots_raw = line.split(":", 1)
        key = key.strip()
        shots = []
        for s in shots_raw.split(","):
            s = s.strip()
            if " or " in s:
                parts = s.split(" or ", 1)
                shots.append((parts[0].strip().replace(" ", "_"), parts[1].strip().replace(" ", "_")))
            else:
                shots.append((s.replace(" ", "_"), None))
        if shots:
            capcut_map[key] = shots
    return capcut_map if capcut_map else None


def scan_clips(song_dir: Path) -> dict:
    """clips/ 폴더 스캔 → {정규화된_이름: 파일명} 반환"""
    clips_dir = song_dir / "clips"
    if not clips_dir.exists():
        return {}
    result = {}
    for f in sorted(clips_dir.glob("*.mp4")):
        key = f.stem.lower().replace("-", "_").replace(" ", "_")
        result[key] = f.name
    return result


# ─── LRC 파싱 ────────────────────────────────────────────────────────────────


def parse_lrc(lrc_path: Path) -> list:
    """LRC Part 1(압축 섹션 마커)만 추출 — [End] 이후는 실제 가사라인이므로 무시"""
    sections = []
    with open(lrc_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = LRC_LINE_RE.match(line)
            if not m:
                continue

            minutes = int(m.group(1))
            seconds = float(m.group(2))
            content = m.group(3).strip()
            ms = int((minutes * 60 + seconds) * 1000)

            if re.match(r"^\[End\]$", content, re.IGNORECASE):
                break

            inner = re.match(r"^\[([^\]]+)\]$", content)
            if inner:
                name = _normalize_section_name(inner.group(1).strip())
                if SECTION_RE.match(name):
                    sections.append({"name": name, "start_ms": ms})

    return sections


def parse_lrc_lyrics(lrc_path: Path, total_ms: int) -> list:
    """LRC 실제 가사 라인 → [{text, start_ms, end_ms}, ...]

    두 가지 Suno LRC 포맷 모두 처리:
      - 2-part: [End] 이전=섹션마커, [End] 이후=실제 가사
      - 1-part: [End] 없이 처음부터 타임스탬프+가사 혼재 (최신 Suno 포맷)
    섹션·제작 태그([Intro], [ocean ambience] 등)는 제외.
    """
    tag_re = re.compile(r"^\[([^\]]+)\]$")
    raw = lrc_path.read_text(encoding="utf-8", errors="ignore")

    has_end = bool(re.search(r"^\[End\]$", raw, re.IGNORECASE | re.MULTILINE))
    past_end = not has_end  # [End] 없으면(1-part) 처음부터 수집

    entries = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        m = LRC_LINE_RE.match(line)
        if not m:
            continue
        minutes = int(m.group(1))
        seconds = float(m.group(2))
        text = m.group(3).strip()
        ms = int((minutes * 60 + seconds) * 1000)

        if re.match(r"^\[End\]$", text, re.IGNORECASE):
            past_end = True
            continue

        if not past_end:
            continue

        # 섹션·제작 태그 제외 ([Intro], [ocean ambience] 등)
        if tag_re.match(text):
            continue

        if text:
            entries.append({"text": text, "start_ms": ms, "end_ms": 0})

    # end_ms 채우기
    for i in range(len(entries) - 1):
        entries[i]["end_ms"] = entries[i + 1]["start_ms"]
    if entries:
        entries[-1]["end_ms"] = total_ms

    return entries


# ─── 타임스탬프 정규화 ────────────────────────────────────────────────────────


def normalize_timestamps(sections: list, audio_ms: Optional[int]) -> list:
    """Suno LRC 타임스탬프가 압축된 경우 실제 오디오 길이에 맞게 스케일링"""
    if not sections:
        return sections

    last_start = sections[-1]["start_ms"]

    if audio_ms and last_start > 0 and (audio_ms / last_start) > 5:
        first_start = sections[0]["start_ms"]
        span = last_start - first_start
        avg_dur = span / max(len(sections) - 1, 1)
        lrc_est_total = span + avg_dur
        scale = audio_ms / lrc_est_total
        for s in sections:
            s["start_ms"] = int((s["start_ms"] - first_start) * scale)

    # 첫 섹션이 0ms보다 늦게 시작하면 처음에 빈 영상 구간이 생기므로 0으로 당긴다
    sections[0]["start_ms"] = 0

    for i, s in enumerate(sections):
        if i + 1 < len(sections):
            s["end_ms"] = sections[i + 1]["start_ms"]
        else:
            s["end_ms"] = audio_ms if audio_ms else s["start_ms"] + 30_000

    return sections


# ─── config 로드 ──────────────────────────────────────────────────────────────


def load_config(config_path: Path) -> tuple:
    """production_config.json → (mode: str, capcut_map: dict)
    capcut_map = {섹션키: [(primary, fallback|None), ...]}
    "or" 구문을 파싱해 fallback 클립 정보를 보존한다.
    """
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    mode = config.get("mode", "mvp")
    sections_raw = config["modes"][mode]["capcut_map"]["sections"]

    capcut_map = {}
    for line in sections_raw:
        if ":" not in line:
            continue
        key, shots_raw = line.split(":", 1)
        key = key.strip()
        shots = []
        for s in shots_raw.split(","):
            s = s.strip()
            if " or " in s:
                parts = s.split(" or ", 1)
                primary = parts[0].strip().replace(" ", "_")
                fallback = parts[1].strip().replace(" ", "_")
                shots.append((primary, fallback))
            else:
                shots.append((s.replace(" ", "_"), None))
        capcut_map[key] = shots

    return mode, capcut_map


def load_capcut_map(song_dir: Path) -> tuple:
    """capcut_map 로드: 곡 폴더 내 *_video_motion_prompts.md 우선, 없으면 production_config.json 폴백
    Returns (mode, capcut_map, source_name)
    """
    mode, fallback_map = load_config(CONFIG_PATH)
    mp = find_motion_prompts(song_dir)
    if mp:
        song_map = parse_capcut_map_from_md(mp)
        if song_map:
            return mode, song_map, mp.name
    return mode, fallback_map, CONFIG_PATH.name


# ─── 섹션 → capcut_map 매핑 ──────────────────────────────────────────────────


def match_sections(sections: list, capcut_map: dict) -> list:
    """각 섹션에 capcut_key 추가 (production_config 키와 연결)"""
    chorus_idx = [
        i for i, s in enumerate(sections)
        if re.search(r"chorus", s["name"], re.I)
        and not re.search(r"pre|post|final", s["name"], re.I)
    ]
    total_chorus = len(chorus_idx)
    chorus_rank = {idx: rank for rank, idx in enumerate(chorus_idx, 1)}

    result = []
    for i, s in enumerate(sections):
        name = s["name"]
        nl = name.lower()
        key = None

        if nl == "intro":
            key = "Intro"
        elif re.match(r"^verse\s+1$", nl):
            key = "Verse 1"
        elif re.match(r"^verse\s+2$", nl):
            key = "Verse 2"
        elif re.match(r"^verse", nl):
            key = "Verse 1"
        elif re.search(r"pre", nl) and re.search(r"chorus", nl):
            key = "Pre-Chorus"
        elif re.search(r"post", nl) and re.search(r"chorus", nl):
            key = "Post-Chorus"
        elif re.search(r"chorus", nl) and not re.search(r"pre", nl):
            if re.search(r"final", nl):
                key = "Final Chorus"
            else:
                rank = chorus_rank.get(i, 1)
                key = "Final Chorus" if (rank == total_chorus and total_chorus > 1) else "Chorus 1"
        elif re.search(r"bridge|solo", nl):
            key = "Bridge/Solo"
        elif nl == "outro":
            key = "Outro"

        if key and key not in capcut_map:
            base = re.sub(r"\s+\d+$", "", key)
            key = base if base in capcut_map else None

        result.append({**s, "capcut_key": key})

    return result


# ─── 클립 슬롯 생성 ───────────────────────────────────────────────────────────


def build_slots(sections: list, capcut_map: dict, clips: dict) -> list:
    """섹션 × shot_type → 클립 슬롯 목록 생성
    - slot_id 중복 방지 (동일 섹션명이 2회 이상 등장 시 _2, _3 suffix)
    - duration_ms 필드 포함
    - fallback 클립 자동 사용 ("or" 구문)
    """
    slots = []
    seen_ids: dict = {}

    for s in sections:
        key = s.get("capcut_key")
        shot_pairs = capcut_map.get(key, []) if key else []
        duration_ms = s["end_ms"] - s["start_ms"]

        for primary, fallback in shot_pairs:
            clip_file = clips.get(primary.lower())
            fallback_used = None
            if clip_file is None and fallback:
                fb_file = clips.get(fallback.lower())
                if fb_file:
                    clip_file = fb_file
                    fallback_used = fallback

            base_id = f"{s['name'].lower().replace(' ', '_')}_{primary}"
            n = seen_ids.get(base_id, 0)
            slot_id = base_id if n == 0 else f"{base_id}_{n + 1}"
            seen_ids[base_id] = n + 1

            entry = {
                "slot_id": slot_id,
                "section": s["name"],
                "capcut_key": key,
                "shot_type": primary,
                "start_ms": s["start_ms"],
                "end_ms": s["end_ms"],
                "duration_ms": duration_ms,
                "clip_file": clip_file,
                "source": "assigned" if clip_file else "placeholder",
                "review_required": clip_file is None,
            }
            if fallback_used:
                entry["fallback_used"] = fallback_used
            slots.append(entry)

    return slots


# ─── 히스토리 정리 ────────────────────────────────────────────────────────────


def cleanup_history(song_output_dir: Path, keep: int) -> None:
    """run_id 폴더를 최신 keep개만 유지하고 나머지 삭제"""
    if keep <= 0:
        return
    runs = sorted(
        [d for d in song_output_dir.iterdir()
         if d.is_dir() and RUN_ID_RE.match(d.name)],
        key=lambda d: d.name,
    )
    to_delete = runs[:-keep] if len(runs) > keep else []
    for d in to_delete:
        shutil.rmtree(d)
        click.echo(f"   히스토리 삭제: {d.name}")


# ─── 출력 함수 ────────────────────────────────────────────────────────────────


def ms_to_ts(ms: int) -> str:
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


def write_timeline_json(
    song_title: str,
    audio_ms: Optional[int],
    sections: list,
    slots: list,
    out_dir: Path,
    mode: str = "mvp",
) -> Path:
    data = {
        "schema_version": "1.2",
        "build_info": {
            "generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "mode": mode,
        },
        "song_title": song_title,
        "total_duration_ms": audio_ms,
        "sections": [
            {
                "name": s["name"],
                "capcut_key": s.get("capcut_key"),
                "start_ms": s["start_ms"],
                "end_ms": s["end_ms"],
                "duration_ms": s["end_ms"] - s["start_ms"],
            }
            for s in sections
        ],
        "clips": slots,
    }
    path = out_dir / "timeline.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_shot_list(
    song_title: str,
    audio_ms: Optional[int],
    sections: list,
    slots: list,
    out_dir: Path,
    mode: str = "mvp",
) -> Path:
    total = ms_to_ts(audio_ms) if audio_ms else "?:??"
    assigned = sum(1 for sl in slots if sl["source"] == "assigned")
    placeholder = len(slots) - assigned
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# {song_title} — MV 편집 Shot List",
        "",
        f"> 생성: {now}  |  모드: {mode}",
        "",
        f"총 {total} | 섹션 {len(sections)}개 | 클립 슬롯 {len(slots)}개 "
        f"(할당 {assigned} / 미생성 {placeholder})",
        "",
        "---",
        "",
        "## 섹션별 클립 목록",
        "",
        "| # | 섹션 | Shot Type | 시작 | 종료 | 길이 | 클립 파일 | 상태 |",
        "|---|------|-----------|------|------|------|-----------|------|",
    ]

    for i, sl in enumerate(slots, 1):
        if sl["source"] == "assigned":
            status = f"✅ 대체({sl['fallback_used']})" if sl.get("fallback_used") else "✅ 할당"
        else:
            status = "⚠️ 필요"
        clip = f"`{sl['clip_file']}`" if sl["clip_file"] else "—"
        dur = ms_to_ts(sl["duration_ms"])
        lines.append(
            f"| {i:02d} | {sl['section']} | `{sl['shot_type']}` | "
            f"{ms_to_ts(sl['start_ms'])} | {ms_to_ts(sl['end_ms'])} | {dur} | {clip} | {status} |"
        )

    missing = list(dict.fromkeys(sl["shot_type"] for sl in slots if sl["source"] == "placeholder"))
    if missing:
        lines += ["", "---", "", "## 미생성 클립 (Kling에서 생성 필요)", ""]
        for shot in missing:
            lines.append(f"- `{shot}`")

    lines += [
        "",
        "---",
        "",
        "## CapCut 작업 순서",
        "",
        "1. 음원 import → 기준 트랙 설정",
        "2. 위 표 순서대로 클립 배치 (`start_ms` 기준)",
        "3. ⚠️ 슬롯: 단색 플레이스홀더 클립으로 채운 뒤 Kling 클립으로 교체",
        "4. 클립 재사용 전략 (3분 MV 기준)",
        "   - Kling 클립은 5~10s 이므로 섹션보다 짧은 것이 정상",
        "   - 코러스(30s): 강한 클립(vocal_B, stage_B)을 1~3s 빠른 컷으로 10~15회 반복",
        "   - 버스(30s): 클립을 5~8s씩 홀드 → 4~6회 재사용",
        "   - 인트로/아웃트로(15s): stage/atmosphere 클립 1회 홀드 후 페이드",
        "5. 전환 효과: Chorus는 hard cut, Intro/Outro는 fade 권장",
        "6. 최종 길이 확인 후 내보내기",
    ]

    path = out_dir / "shot_list.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ─── clip 길이 경고 ───────────────────────────────────────────────────────────


def warn_short_clips(slots: list, clip_durations: dict) -> None:
    """섹션 길이보다 클립 실제 길이가 짧은 경우 안내 출력
    MV 편집에서 Kling 클립(5~10s)이 섹션(30s~)보다 짧은 것은 정상 — 재사용 전략으로 커버한다.
    """
    if not clip_durations:
        return
    warned = set()
    for sl in slots:
        if not sl["clip_file"]:
            continue
        key = Path(sl["clip_file"]).stem.lower().replace("-", "_").replace(" ", "_")
        clip_ms = clip_durations.get(key)
        section_ms = sl["duration_ms"]
        if clip_ms is not None and clip_ms < section_ms and key not in warned:
            reuse = int(section_ms / clip_ms) + 1
            click.echo(
                f"   ℹ️  {sl['clip_file']}  {clip_ms/1000:.0f}s → 섹션 {section_ms/1000:.0f}s"
                f"  (CapCut에서 약 {reuse}회 재사용)"
            )
            warned.add(key)


# ─── 파이프라인 ───────────────────────────────────────────────────────────────


def run_inspect(song_dir: Path) -> None:
    click.echo(f"\n=== {song_dir.name} 점검 ===")

    audio = find_audio(song_dir)
    lrc = find_lrc(song_dir)
    srt = find_srt(song_dir)
    clips = scan_clips(song_dir)

    if audio:
        dur = get_audio_duration_ms(audio)
        dur_str = ms_to_ts(dur) if dur else "길이 측정 불가 (pip install mutagen)"
        click.echo(f"음원   : ✅ {audio.name} ({dur_str})")
    else:
        click.echo("음원   : ❌ WAV/MP3 없음")

    click.echo(f"LRC    : {'✅ ' + lrc.name if lrc else '❌ 없음'}")
    click.echo(f"SRT    : {'✅ ' + srt.name if srt else '없음'}")

    if clips:
        click.echo(f"Clips  : ✅ {len(clips)}개")
        for k, v in clips.items():
            click.echo(f"           {k} → {v}")
    else:
        click.echo("Clips  : ⚠️  clips/ 없음 → 플레이스홀더 모드")

    if not lrc:
        return

    audio_ms = get_audio_duration_ms(audio) if audio else None
    sections = normalize_timestamps(parse_lrc(lrc), audio_ms)
    if not sections:
        click.echo("⚠️  LRC에서 섹션 마커를 찾지 못했습니다")
        return

    click.echo(f"\n섹션 {len(sections)}개:")
    for s in sections:
        click.echo(f"  {s['name']:20s} {ms_to_ts(s['start_ms'])} ~ {ms_to_ts(s['end_ms'])}")

    _, capcut_map, map_src = load_capcut_map(song_dir)
    click.echo(f"CapCut 맵: {map_src}")
    sections_matched = match_sections(sections, capcut_map)

    # ① 누락 클립 체크
    required_primary = set()
    required_with_fallback = set()
    for s in sections_matched:
        key = s.get("capcut_key")
        for primary, fallback in (capcut_map.get(key, []) if key else []):
            required_primary.add(primary.lower())
            if fallback:
                required_with_fallback.add(primary.lower())

    if clips:
        missing_hard = required_primary - set(clips.keys()) - required_with_fallback
        missing_soft = {
            p for p in required_with_fallback
            if p not in clips
        }
        if missing_hard or missing_soft:
            click.echo("\n⚠️  누락 클립:")
            for shot in sorted(missing_hard):
                click.echo(f"   ❌ {shot}  (필수)")
            for shot in sorted(missing_soft):
                click.echo(f"   ⚠️  {shot}  (fallback 있음)")
        else:
            click.echo("\n✅ 필요 클립 모두 준비됨")

        # ② clip 실제 길이 vs 섹션 길이 비교
        clip_durations = get_clip_durations(song_dir)
        if clip_durations:
            slots = build_slots(sections_matched, capcut_map, clips)
            short_clips = []
            seen = set()
            for sl in slots:
                if not sl["clip_file"]:
                    continue
                key = Path(sl["clip_file"]).stem.lower().replace("-", "_").replace(" ", "_")
                if key in seen:
                    continue
                clip_ms = clip_durations.get(key)
                section_ms = sl["duration_ms"]
                if clip_ms is not None and clip_ms < section_ms:
                    short_clips.append((sl["clip_file"], clip_ms, section_ms))
                    seen.add(key)
            if short_clips:
                click.echo("\nℹ️  클립 재사용 안내 (MV 편집 정상):")
                for fname, cms, sms in short_clips:
                    reuse = int(sms / cms) + 1
                    click.echo(f"   {fname}  {cms/1000:.0f}s → 섹션 {sms/1000:.0f}s  (약 {reuse}회 재사용)")
            else:
                click.echo("✅ 모든 클립 길이 충분")


def run_build(song_dir: Path, output_root: Path, keep: int = 0) -> Optional[dict]:
    """빌드 실행 → 성공 시 통계 dict 반환, 실패 시 None"""
    song_title = song_dir.name
    click.echo(f"\n[{song_title}] 빌드 시작...")

    audio = find_audio(song_dir)
    lrc = find_lrc(song_dir)

    if not lrc:
        click.echo("❌ LRC 없음. 종료.")
        return None

    audio_ms = get_audio_duration_ms(audio) if audio else None
    sections = parse_lrc(lrc)

    if not sections:
        click.echo("❌ 섹션 마커 없음. LRC 포맷 확인 필요.")
        return None

    sections = normalize_timestamps(sections, audio_ms)
    mode, capcut_map, map_src = load_capcut_map(song_dir)
    click.echo(f"   CapCut 맵: {map_src}")
    sections = match_sections(sections, capcut_map)
    clips = scan_clips(song_dir)
    slots = build_slots(sections, capcut_map, clips)

    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = output_root / song_title / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    write_timeline_json(song_title, audio_ms, sections, slots, out_dir, mode)
    write_shot_list(song_title, audio_ms, sections, slots, out_dir, mode)

    # latest/ 항상 최신 빌드로 갱신
    latest_dir = output_root / song_title / "latest"
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    shutil.copytree(out_dir, latest_dir)

    assigned = sum(1 for s in slots if s["source"] == "assigned")
    fallback_count = sum(1 for s in slots if s.get("fallback_used"))
    placeholder = len(slots) - assigned

    click.echo(f"✅ 완료 → {out_dir.relative_to(ROOT)}")
    click.echo(f"   슬롯 {len(slots)}개 (할당 {assigned} / 플레이스홀더 {placeholder})")
    if fallback_count:
        click.echo(f"   대체 클립 사용: {fallback_count}개")

    # ② clip 실제 길이 경고
    clip_durations = get_clip_durations(song_dir)
    warn_short_clips(slots, clip_durations)

    click.echo(f"   latest/ 갱신 완료  (mode: {mode})")

    # ③ 히스토리 정리
    if keep > 0:
        cleanup_history(output_root / song_title, keep)

    return {
        "out_dir": out_dir,
        "total": len(slots),
        "assigned": assigned,
        "placeholder": placeholder,
        "fallback": fallback_count,
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────


@click.group()
def cli():
    """ai_img_video_prompt_capcut — MV CapCut 타임라인 생성"""


@cli.command()
@click.option("--song", required=True, help="곡 폴더명 (input/ 기준)")
@click.option("--input-root", default=None, type=click.Path())
def inspect(song, input_root):
    """입력 폴더 상태 점검 + 누락 클립 경고 + 클립 길이 비교"""
    root = Path(input_root) if input_root else INPUT_ROOT
    song_dir = root / song
    if not song_dir.exists():
        click.echo(f"❌ 폴더 없음: {song_dir}")
        return
    run_inspect(song_dir)


@cli.command()
@click.option("--song", required=True, help="곡 폴더명")
@click.option("--input-root", default=None, type=click.Path())
def plan(song, input_root):
    """섹션 매핑 미리보기 — 클립 가용 여부 + 전체 가용률 요약"""
    root = Path(input_root) if input_root else INPUT_ROOT
    song_dir = root / song
    if not song_dir.exists():
        click.echo(f"❌ 폴더 없음: {song_dir}")
        return

    audio = find_audio(song_dir)
    lrc = find_lrc(song_dir)
    if not lrc:
        click.echo("❌ LRC 없음")
        return

    audio_ms = get_audio_duration_ms(audio) if audio else None
    sections = normalize_timestamps(parse_lrc(lrc), audio_ms)
    _, capcut_map, map_src = load_capcut_map(song_dir)
    clips = scan_clips(song_dir)
    sections = match_sections(sections, capcut_map)

    click.echo(f"\n=== {song} 섹션 매핑 === ({map_src})")
    total_slots = 0
    ready_slots = 0

    for s in sections:
        key = s.get("capcut_key") or "매핑 없음"
        shot_pairs = capcut_map.get(key, [])
        shots_display = []
        for primary, fallback in shot_pairs:
            total_slots += 1
            if clips.get(primary.lower()):
                marker, label = "✅", primary
                ready_slots += 1
            elif fallback and clips.get(fallback.lower()):
                marker, label = "✅", f"{primary}→{fallback}"
                ready_slots += 1
            else:
                marker, label = "⚠️", primary
            shots_display.append(f"{marker}{label}")
        shots_str = ", ".join(shots_display) or "—"
        click.echo(
            f"  {s['name']:20s} "
            f"{ms_to_ts(s['start_ms'])} ~ {ms_to_ts(s['end_ms'])}"
            f"  →  [{key}]  {shots_str}"
        )

    # ④ 전체 가용률 요약
    if total_slots:
        pct = int(ready_slots / total_slots * 100)
        status = "✅" if ready_slots == total_slots else "⚠️"
        click.echo(f"\n{status} 준비 완료: {ready_slots}/{total_slots} 슬롯 ({pct}%)")
        if ready_slots < total_slots:
            click.echo(f"   미준비: {total_slots - ready_slots}개 → Kling 클립 생성 후 clips/ 에 추가")


@cli.command()
@click.option("--song", required=True, help="곡 폴더명")
@click.option("--input-root", default=None, type=click.Path())
@click.option("--output-root", default=None, type=click.Path())
@click.option("--keep", default=0, type=int, help="유지할 히스토리 수 (0=전체 유지)")
def build(song, input_root, output_root, keep):
    """timeline.json + shot_list.md 생성, latest/ 자동 갱신"""
    in_root = Path(input_root) if input_root else INPUT_ROOT
    out_root = Path(output_root) if output_root else OUTPUT_ROOT
    song_dir = in_root / song
    if not song_dir.exists():
        click.echo(f"❌ 폴더 없음: {song_dir}")
        return
    run_build(song_dir, out_root, keep=keep)


@cli.command("build-all")
@click.option("--input-root", default=None, type=click.Path())
@click.option("--output-root", default=None, type=click.Path())
@click.option("--keep", default=0, type=int, help="곡별 유지할 히스토리 수 (0=전체 유지)")
def build_all(input_root, output_root, keep):
    """input/ 내 모든 곡 배치 처리 + 집계 통계"""
    in_root = Path(input_root) if input_root else INPUT_ROOT
    out_root = Path(output_root) if output_root else OUTPUT_ROOT

    songs = sorted(d for d in in_root.iterdir() if d.is_dir())
    if not songs:
        click.echo("input/ 폴더가 비어있습니다.")
        return

    click.echo(f"총 {len(songs)}개 곡 처리...")
    ok = fail = 0
    agg = {"total": 0, "assigned": 0, "placeholder": 0, "fallback": 0}

    for song_dir in songs:
        result = run_build(song_dir, out_root, keep=keep)
        if result:
            ok += 1
            for k in agg:
                agg[k] += result[k]
        else:
            fail += 1

    # ⑤ 집계 통계
    click.echo(f"\n{'='*40}")
    click.echo(f"완료: ✅ {ok}곡 / ❌ {fail}곡")
    if ok:
        click.echo(f"전체 슬롯  : {agg['total']}개")
        click.echo(f"  ✅ 할당   : {agg['assigned']}개")
        click.echo(f"  ⚠️  미생성 : {agg['placeholder']}개")
        if agg["fallback"]:
            click.echo(f"  대체 사용 : {agg['fallback']}개")


@cli.command("sync")
@click.option("--song", required=True, help="곡 폴더명 (ai_lyric_video/input/ 기준)")
@click.option("--build", "do_build", is_flag=True, default=False,
              help="파일 복사 후 timeline.json 자동 빌드")
def sync_from_lyric(song, do_build):
    """ai_lyric_video/input/{곡}의 오디오·자막 파일을 input/{곡}으로 복사 + clips/ 생성

    \b
    export-draft 실행 전 이 명령으로 입력 파일을 먼저 준비하세요.
    준비 순서:
      1. python main.py sync --song {곡명}          ← 오디오/자막 복사
      2. clips/ 에 Kling 생성 영상 추가
      3. python main.py build --song {곡명}          ← timeline.json 생성
      4. python main.py export-draft --song {곡명}   ← CapCut 드래프트 생성
    """
    lyric_input = ROOT.parent / "ai_lyric_video" / "input" / song
    song_dir    = INPUT_ROOT / song

    if not lyric_input.exists():
        click.echo(f"❌ ai_lyric_video/input/{song}/ 폴더 없음")
        click.echo(f"   ai_lyric_video/input/ 에 먼저 곡 폴더를 만들어 주세요.")
        return

    song_dir.mkdir(parents=True, exist_ok=True)
    clips_dir = song_dir / "clips"
    clips_dir.mkdir(exist_ok=True)

    copied, skipped = [], []
    for pattern in ["*.wav", "*.mp3", "*.m4a", "*.flac", "*.lrc", "*.srt"]:
        for src in lyric_input.glob(pattern):
            dest = song_dir / src.name
            if dest.exists():
                skipped.append(src.name)
            else:
                shutil.copy2(src, dest)
                copied.append(src.name)

    click.echo(f"\n=== {song} 파일 동기화 ===")
    if copied:
        click.echo(f"✅ 복사 ({len(copied)}개):")
        for fname in copied:
            click.echo(f"   + {fname}")
    if skipped:
        click.echo(f"⏭  이미 존재: {', '.join(skipped)}")
    click.echo(f"✅ {clips_dir} 준비됨")

    # motion prompts 안내
    motion_src = ROOT.parent / "ai_img_video_aiBoygirl" / "output" / song
    if motion_src.exists():
        for md in motion_src.glob("*_video_motion_prompts.md"):
            dest = song_dir / md.name
            if not dest.exists():
                shutil.copy2(md, dest)
                click.echo(f"✅ {md.name} 복사됨 (ai_img_video_aiBoygirl 결과)")
    else:
        click.echo(f"ℹ️  *_video_motion_prompts.md 없음 — production_config.json 기본값 사용")

    click.echo(f"\n다음 단계:")
    click.echo(f"  1. clips/ 에 Kling 생성 영상 추가 ({clips_dir})")
    click.echo(f"  2. python main.py build --song \"{song}\"")
    click.echo(f"  3. python main.py export-draft --song \"{song}\"")

    if do_build:
        click.echo("")
        run_build(song_dir, OUTPUT_ROOT)


@cli.command("export-lyric-draft")
@click.option("--song", required=True, help="곡명 (ai_lyric_video/output/{곡}.mp4 기준)")
@click.option("--capcut-root", default=None, type=click.Path(),
              help="CapCut 드래프트 루트 폴더 (기본: 자동 감지)")
def export_lyric_draft(song, capcut_root):
    """완성된 가사 영상 → CapCut 드래프트 생성 (오디오·자막 분리)

    \b
    트랙 구성:
      [비디오] ai_lyric_video/output/{곡}.mp4   — 볼륨 0 (비주얼 전용)
      [오디오] ai_lyric_video/input/{곡}/*.wav  — Wave 파동 시각화 지원
      [텍스트] LRC 가사 세그먼트                — 드래그로 싱크 수동 조정

    CapCut을 닫은 상태에서 실행 후 CapCut을 재시작하면 프로젝트 목록에 나타납니다.
    """
    try:
        from capcut_draft import build_lyric_draft, write_draft, CAPCUT_DRAFT_ROOT
    except ImportError:
        click.echo("❌ capcut_draft.py 를 찾을 수 없습니다.")
        return

    lyric_out = ROOT.parent / "ai_lyric_video" / "output" / f"{song}.mp4"
    if not lyric_out.exists():
        click.echo(f"❌ 가사 영상 없음: {lyric_out}")
        click.echo(f"   먼저 ai_lyric_video 에서 영상을 생성하세요.")
        return

    lyric_in = ROOT.parent / "ai_lyric_video" / "input" / song
    audio = find_audio(lyric_in) if lyric_in.exists() else find_audio(INPUT_ROOT / song)
    if not audio:
        click.echo(f"❌ 오디오 파일 없음 — ai_lyric_video/input/{song}/ 또는 input/{song}/ 확인")
        return

    total_ms = get_audio_duration_ms(audio)
    if not total_ms:
        total_ms = get_audio_duration_ms(lyric_out)
    if not total_ms:
        click.echo("❌ 오디오 길이를 측정할 수 없습니다 (ffprobe 설치 확인)")
        return

    # LRC 가사 파싱 (싱크 수동 조정용 텍스트 트랙)
    lrc = find_lrc(lyric_in) if lyric_in.exists() else find_lrc(INPUT_ROOT / song)
    captions = parse_lrc_lyrics(lrc, total_ms) if lrc else []

    cc_root = Path(capcut_root) if capcut_root else CAPCUT_DRAFT_ROOT
    if not cc_root.exists():
        click.echo(f"❌ CapCut 드래프트 폴더 없음: {cc_root}")
        click.echo("  --capcut-root 로 수동 지정하거나 CapCut 설치를 확인하세요.")
        return

    click.echo(f"\n[{song}] 가사 영상 CapCut 드래프트 생성...")
    click.echo(f"  영상: {lyric_out.name}  ({total_ms/1000:.1f}s)")
    click.echo(f"  오디오: {audio.name}")
    click.echo(f"  자막: {len(captions)}개 라인" if captions else "  자막: LRC 없음 (텍스트 트랙 생략)")

    draft_content, draft_meta, draft_id = build_lyric_draft(
        lyric_video_path=lyric_out,
        audio_path=audio,
        song_title=song,
        total_ms=total_ms,
        caption_entries=captions,
    )

    folder = write_draft(draft_content, draft_meta, draft_id, cc_root)
    click.echo(f"\n✅ 드래프트 생성 완료: {folder}")
    click.echo(f"   CapCut 재시작 후 '{song}_Lyric' 프로젝트를 열어주세요.")
    if captions:
        click.echo(f"\n   ※ '가사 싱크' 텍스트 트랙에서 각 라인을 드래그해 싱크를 조정하세요.")
        click.echo(f"   ※ 싱크 수정 후 LRC 파일을 업데이트하면 영상을 재생성할 수 있습니다.")


@cli.command("export-image-lyric-draft")
@click.option("--song", required=True, help="곡명 (ai_lyric_video/input/{곡}/ 기준)")
@click.option("--capcut-root", default=None, type=click.Path(),
              help="CapCut 드래프트 루트 폴더 (기본: 자동 감지)")
def export_image_lyric_draft(song, capcut_root):
    """이미지 + 오디오 + LRC → CapCut 드래프트 직접 생성 (Python 렌더링 없음)

    \b
    트랙 구성:
      [비디오] 원본 배경 이미지 (전체 길이) — CapCut에서 필터·자막 스타일 적용
      [오디오] 원본 음원 (wav/mp3)
      [텍스트] LRC 가사 세그먼트 — CapCut에서 자막 스타일 및 싱크 수동 조정

    ai_lyric_video/input/{곡}/ 폴더에서 이미지·오디오·LRC를 직접 읽습니다.
    CapCut을 닫은 상태에서 실행 후 재시작하면 프로젝트 목록에 나타납니다.
    """
    try:
        from capcut_draft import build_image_lyric_draft, write_draft, CAPCUT_DRAFT_ROOT
    except ImportError:
        click.echo("❌ capcut_draft.py 를 찾을 수 없습니다.")
        return

    lyric_in = ROOT.parent / "ai_lyric_video" / "input" / song
    if not lyric_in.exists():
        click.echo(f"❌ 폴더 없음: {lyric_in}")
        click.echo(f"   ai_lyric_video/input/{song}/ 에 이미지·오디오·LRC 파일을 준비하세요.")
        return

    image = find_image(lyric_in, song)
    if not image:
        click.echo(f"❌ 이미지 없음 (png/jpg) — {lyric_in}")
        return

    audio = find_audio(lyric_in)
    if not audio:
        click.echo(f"❌ 오디오 없음 (wav/mp3) — {lyric_in}")
        return

    total_ms = get_audio_duration_ms(audio)
    if not total_ms:
        click.echo("❌ 오디오 길이를 측정할 수 없습니다 (ffprobe 또는 mutagen 설치 확인)")
        return

    lrc = find_lrc(lyric_in)
    captions = parse_lrc_lyrics(lrc, total_ms) if lrc else []

    cc_root = Path(capcut_root) if capcut_root else CAPCUT_DRAFT_ROOT
    if not cc_root.exists():
        click.echo(f"❌ CapCut 드래프트 폴더 없음: {cc_root}")
        click.echo("   --capcut-root 로 수동 지정하거나 CapCut 설치를 확인하세요.")
        return

    click.echo(f"\n[{song}] 이미지 기반 CapCut 드래프트 생성...")
    click.echo(f"  이미지: {image.name}")
    click.echo(f"  오디오: {audio.name}  ({total_ms/1000:.1f}s)")
    if captions:
        click.echo(f"  자막  : {len(captions)}개 라인 ({lrc.name})")
    else:
        click.echo("  자막  : LRC 없음 (텍스트 트랙 생략)")

    draft_content, draft_meta, draft_id = build_image_lyric_draft(
        image_path=image,
        audio_path=audio,
        song_title=song,
        total_ms=total_ms,
        caption_entries=captions,
    )

    folder = write_draft(draft_content, draft_meta, draft_id, cc_root)
    click.echo(f"\n✅ 드래프트 생성 완료: {folder}")
    click.echo(f"   CapCut 재시작 후 '{song}_Lyric' 프로젝트를 열어주세요.")
    if captions:
        click.echo(f"\n   ※ '가사' 텍스트 트랙에서 각 라인 스타일·싱크를 조정하세요.")
        click.echo(f"   ※ CapCut 내보내기 전 이미지 필터·효과를 자유롭게 적용하세요.")


@cli.command("export-draft")
@click.option("--song", required=True, help="곡 폴더명 (input/ 기준)")
@click.option("--input-root", default=None, type=click.Path())
@click.option("--output-root", default=None, type=click.Path())
@click.option("--capcut-root", default=None, type=click.Path(),
              help="CapCut 드래프트 루트 폴더 (기본: 자동 감지)")
def export_draft(song, input_root, output_root, capcut_root):
    """CapCut PC 드래프트 자동 생성 — CapCut 프로젝트 목록에서 바로 열 수 있음

    \b
    1. output/{곡}/latest/timeline.json 읽기
    2. clips/ + 음원 파일 참조
    3. draft_content.json + draft_meta_info.json 생성
    4. CapCut 드래프트 폴더에 바로 저장

    CapCut을 닫은 상태에서 실행 후 CapCut을 재시작하면 프로젝트 목록에 나타납니다.
    """
    try:
        from capcut_draft import build_draft, write_draft, CAPCUT_DRAFT_ROOT
    except ImportError:
        click.echo("❌ capcut_draft.py 를 찾을 수 없습니다. main.py 와 같은 폴더에 있는지 확인하세요.")
        return

    in_root = Path(input_root) if input_root else INPUT_ROOT
    out_root = Path(output_root) if output_root else OUTPUT_ROOT
    song_dir = in_root / song

    if not song_dir.exists():
        click.echo(f"❌ 폴더 없음: {song_dir}")
        return

    # latest/ timeline.json
    timeline_path = out_root / song / "latest" / "timeline.json"
    if not timeline_path.exists():
        click.echo(f"❌ timeline.json 없음. 먼저 build 실행:")
        click.echo(f"   python main.py build --song {song}")
        return

    with open(timeline_path, encoding="utf-8") as f:
        timeline = json.load(f)

    audio = find_audio(song_dir)
    if not audio:
        click.echo("❌ 음원 없음 (wav/mp3/m4a/flac)")
        return

    clips_dir = song_dir / "clips"
    if not clips_dir.exists():
        click.echo("⚠️  clips/ 폴더 없음 — 할당된 클립 없이 진행합니다")

    clip_durations = get_clip_durations(song_dir)

    srt = find_srt(song_dir)
    srt_entries = parse_srt(srt) if srt else []
    srt_en = find_srt_en(song_dir)
    srt_entries_en = parse_srt(srt_en) if srt_en else []

    # ai_lyric_video 결과 자동 감지
    lyric_video_path = ROOT.parent / "ai_lyric_video" / "output" / f"{song}.mp4"
    lyric_video_dur_ms = None
    if lyric_video_path.exists():
        lyric_video_dur_ms = get_audio_duration_ms(lyric_video_path)
        click.echo(f"   가사 영상: {lyric_video_path.name} → 2번 트랙 추가")
    else:
        lyric_video_path = None
        click.echo(f"   가사 영상: 없음 (ai_lyric_video/output/{song}.mp4 생성 후 재실행)")

    cc_root = Path(capcut_root) if capcut_root else CAPCUT_DRAFT_ROOT
    if not cc_root.exists():
        click.echo(f"❌ CapCut 드래프트 폴더를 찾을 수 없습니다: {cc_root}")
        click.echo("  CapCut 설치 여부를 확인하거나 --capcut-root 로 수동 지정하세요.")
        return

    song_title = timeline["song_title"]
    assigned_clips = sum(1 for c in timeline["clips"] if c["source"] == "assigned")
    click.echo(f"\n[{song_title}] CapCut 드래프트 생성...")
    click.echo(f"   타임라인: {timeline['schema_version']} / {len(timeline['clips'])}슬롯 ({assigned_clips} 할당)")
    click.echo(f"   음원: {audio.name}  ({timeline['total_duration_ms']/1000:.1f}s)")
    if srt_entries:
        click.echo(f"   자막(KR): {srt.name} → {len(srt_entries)}개 항목")
    else:
        click.echo("   자막(KR): SRT 없음 — 한글 자막 트랙 생략")
    if srt_entries_en:
        click.echo(f"   자막(EN): {srt_en.name} → {len(srt_entries_en)}개 항목")
    else:
        click.echo("   자막(EN): *_en.srt 없음 — 영어 자막 트랙 생략")

    draft_content, draft_meta, draft_id = build_draft(
        timeline, audio, clips_dir if clips_dir.exists() else song_dir,
        clip_durations, srt_entries=srt_entries, srt_entries_en=srt_entries_en,
        lyric_video_path=lyric_video_path, lyric_video_dur_ms=lyric_video_dur_ms,
    )

    folder = write_draft(draft_content, draft_meta, draft_id, cc_root)

    video_tracks = [t for t in draft_content["tracks"] if t["type"] == "video"]
    video_segs = len(video_tracks[0]["segments"]) if video_tracks else 0
    lyric_track = next((t for t in video_tracks if t.get("name") == "Lyric Video"), None)
    subtitle_segs = sum(
        len(t["segments"]) for t in draft_content["tracks"] if t["type"] == "text"
    )
    click.echo(f"\n✅ 드래프트 생성 완료")
    click.echo(f"   위치  : {folder}")
    click.echo(f"   이름  : {song_title}_MV")
    click.echo(f"   영상  : {video_segs}개 세그먼트 (MV 클립)")
    if lyric_track:
        click.echo(f"   가사  : Lyric Video 트랙 1개 (CapCut에서 레이어 조정 가능)")
    if subtitle_segs:
        click.echo(f"   자막  : {subtitle_segs}개 세그먼트")
    click.echo(f"\n   CapCut 실행 → 프로젝트 목록에서 '{song_title}_MV' 확인")
    click.echo(f"   (CapCut이 실행 중이면 재시작 필요)")


if __name__ == "__main__":
    cli()
