from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT_DIR = PROJECT_ROOT / "input"
DEFAULT_TEMPLATE_DIR = PROJECT_ROOT / "templates"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
REFERENCE_DIR = PROJECT_ROOT / "reference"
GENRE_PROFILES_PATH = PROJECT_ROOT / "genre_profiles.json"
PERFORMANCE_PROFILES_PATH = PROJECT_ROOT / "performance_profiles.json"
PRODUCTION_CONFIG_PATH = PROJECT_ROOT / "production_config.json"
FILE_RETRY_ATTEMPTS = 40
FILE_RETRY_DELAY_SECONDS = 0.25


def configure_output_streams() -> None:
    """Keep Windows console output from crashing on unsupported filename chars."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors="replace")
        except (OSError, ValueError):
            pass


def _load_genre_data() -> dict:
    try:
        with open(GENRE_PROFILES_PATH, encoding="utf-8") as _f:
            return json.load(_f)
    except FileNotFoundError:
        raise FileNotFoundError(f"genre_profiles.json 파일이 없습니다: {GENRE_PROFILES_PATH}")


try:
    _GENRE_DATA: dict = _load_genre_data()
except FileNotFoundError as _e:
    sys.exit(f"[오류] {_e}")


def _load_performance_data() -> dict:
    try:
        with open(PERFORMANCE_PROFILES_PATH, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"performance_profiles.json 파일이 없습니다: {PERFORMANCE_PROFILES_PATH}"
        )


try:
    _PERFORMANCE_DATA: dict = _load_performance_data()
except FileNotFoundError as _e:
    sys.exit(f"[오류] {_e}")


def _load_production_config() -> dict:
    if not PRODUCTION_CONFIG_PATH.exists():
        return {}
    try:
        with open(PRODUCTION_CONFIG_PATH, encoding="utf-8") as _f:
            return json.load(_f)
    except (json.JSONDecodeError, OSError):
        return {}


_PRODUCTION_CONFIG: dict = _load_production_config()

_PART_CONFIG_KEYS: dict[str, str] = {
    "Vocal": "vocal",
    "Guitar": "guitar",
    "Bass": "bass",
    "Drum": "drum",
    "Stage": "stage",
    "Atmosphere": "atmosphere",
}


def _match_profile(lower: str) -> dict | None:
    for profile in _GENRE_DATA["profiles"]:
        if keyword_present(lower, profile["keywords"]):
            return profile
    return None


def _match_first(entries: list[dict], lower: str, field: str) -> str | None:
    for entry in entries:
        if keyword_present(lower, entry["keywords"]):
            return entry.get(field)
    return None

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

SONG_OVERVIEW_FILE = "00_prompt_overview.md"
ALL_OVERVIEW_FILE = "_ALL_PROMPT_OVERVIEW.md"
PROMPT_AUDIT_FILE = "_PROMPT_AUDIT.md"

# 프롬프트 파일 내 미치환 placeholder 탐지 패턴 — 단일 소스
_PLACEHOLDER_PATTERN = (
    r"\[(SONG_TITLE|GENRE|MOOD|TEMPO|EMOTION|STAGE_ENERGY"
    r"|LIGHTING_STYLE|CAMERA_STYLE|SPECIAL_EFFECTS|REFERENCE_DIR"
    r"|CHARACTER_OUTFIT|CHARACTER_OUTFIT_GIRL|CHARACTER_PROP|CHARACTER_COLOR|CHARACTER_REFERENCE"
    r"|CHARACTER_VOCAL|CHARACTER_VOCAL_ACTION|CHARACTER_GUITAR"
    r"|CHARACTER_BASS|CHARACTER_DRUM|CHARACTER_CROWD|CHARACTER_STAGE)\]"
)

PROMPT_AREA_LABELS = {
    "01_master_style_prompt.md": "master/world",
    "02_style_lock_prompt.md": "fixed identity",
    "03_vocal_image_prompt.md": "vocal close-up",
    "04_guitar_image_prompt.md": "guitar image",
    "05_bass_image_prompt.md": "bass image",
    "06_drum_image_prompt.md": "drum image",
    "07_stage_image_prompt.md": "stage image",
    "08_atmosphere_image_prompt.md": "atmosphere image",
    "09_video_motion_prompts.md": "video motion",
}

SECTION_PATTERN = re.compile(
    r"^\[(?P<label>"
    r"Intro|Verse(?:\s*\d+)?|Pre[- ]?Chorus|Chorus(?:\s*\d+)?|Post[- ]?Chorus|"
    r"Build|Bridge|Final\s+Chorus|Outro|Interlude|Instrumental(?:\s+Break)?|Drop|Hook|Solo|Breakdown"
    r")(?::\s*(?P<note>.*?))?\]$",
    re.IGNORECASE,
)

FIELD_ALIASES = {
    "title": "title",
    "제목": "title",
    "song title": "title",
    "genre": "genre",
    "장르": "genre",
    "style": "genre",
    "스타일": "genre",
    "bpm": "bpm",
    "tempo": "tempo",
    "템포": "tempo",
    "mood": "mood",
    "분위기": "mood",
    "emotion": "emotion",
    "감정": "emotion",
    "energy": "energy",
    "에너지": "energy",
    "instruments": "instruments",
    "악기": "instruments",
    "visual cues": "visual_cues",
    "시각": "visual_cues",
    "weirdness": "weirdness",
    "style influence": "style_influence",
}


@dataclass
class Section:
    label: str
    note: str
    lines: list[str]


@dataclass
class Song:
    title: str
    genre: str
    bpm: str
    mood: str
    emotion: str
    tempo: str
    stage_energy: str
    lighting_style: str
    camera_style: str
    special_effects: str
    instruments: str
    sections: list[Section]
    raw_text: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    def _write() -> None:
        with path.open("w", encoding="utf-8", newline="\n") as file:
            file.write(text)

    run_with_file_retries("write", path, _write)


def run_with_file_retries(action: str, path: Path, callback) -> None:
    last_error: OSError | None = None
    for attempt in range(1, FILE_RETRY_ATTEMPTS + 1):
        try:
            callback()
            return
        except OSError as exc:
            last_error = exc
            if not is_retryable_file_error(exc):
                raise
            if attempt < FILE_RETRY_ATTEMPTS:
                time.sleep(FILE_RETRY_DELAY_SECONDS)
    raise RuntimeError(
        f"Could not {action} because the file is still locked: {path}. "
        "Close editors/previews or any running web server that has this output open, then run again."
    ) from last_error


def is_retryable_file_error(exc: OSError) -> bool:
    return getattr(exc, "winerror", None) in {32, 33} or isinstance(exc, PermissionError)


def normalize_field_key(key: str) -> str | None:
    cleaned = re.sub(r"\s+", " ", key.strip().lstrip("\ufeff").lower())
    return FIELD_ALIASES.get(cleaned)


def strip_noise_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if re.fullmatch(r"\d+[dhms,\s]+ago", stripped, re.IGNORECASE):
            continue
        if stripped.lower().startswith("cover image for "):
            continue
        if re.fullmatch(r"\d+:\d{2}(?::\d{2})?", stripped):
            continue
        lines.append(line)
    return lines


def parse_key_value(line: str) -> tuple[str, str] | None:
    if ":" not in line:
        return None
    key, value = line.split(":", 1)
    normalized = normalize_field_key(key)
    if not normalized:
        return None
    return normalized, value.strip()


def parse_loose_metadata(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    match = re.fullmatch(r"(Weirdness|Style Influence)\s+(.+)", stripped, re.IGNORECASE)
    if not match:
        return None
    key = normalize_field_key(match.group(1))
    if not key:
        return None
    return key, match.group(2).strip()


def infer_title(
    lines: list[str],
    fields: dict[str, str],
    title_override: str | None = None,
    title_fallback: str | None = None,
) -> str:
    if title_override and title_override.strip():
        return title_override.strip()
    if fields.get("title"):
        return fields["title"].strip()
    for index, line in enumerate(lines):
        if "제목" in line and ":" in line:
            candidate = line.split(":", 1)[1].strip()
            if candidate:
                return candidate
        if line.strip().lower().startswith("title:"):
            return line.split(":", 1)[1].strip()
        if line.strip().startswith("["):
            break
        lowered = line.strip().lower()
        if lowered.startswith(("weirdness", "style influence")):
            continue
        if "%" in line or re.search(r"\b\d+\s*bpm\b", line, re.IGNORECASE):
            continue
        if index < 8 and line.strip() and "," not in line and len(line.strip()) <= 40:
            # 한글 없고 단어 하나뿐인 순수 ASCII 줄은 장르/스타일 태그로 간주해 건너뜀
            if not re.search(r"[가-힣]", line) and len(line.strip().split()) == 1:
                continue
            return line.strip()
    if title_fallback and title_fallback.strip():
        return title_fallback.strip()
    raise ValueError("곡 제목을 찾지 못했습니다. --title 옵션을 쓰거나 입력에 'Title:' 또는 '제목:'을 넣어 주세요.")


def parse_sections(lines: list[str]) -> list[Section]:
    sections: list[Section] = []
    current: Section | None = None
    for raw_line in lines:
        line = raw_line.strip()
        match = SECTION_PATTERN.match(line)
        if match:
            if current:
                sections.append(current)
            current = Section(
                label=normalize_section_label(match.group("label")),
                note=(match.group("note") or "").strip(),
                lines=[],
            )
            continue
        if current is not None:
            current.lines.append(raw_line.rstrip())
    if current:
        sections.append(current)
    return sections


def normalize_section_label(label: str) -> str:
    text = re.sub(r"\s+", " ", label.strip().replace("-", " "))
    words = text.split()
    if not words:
        return "Section"
    if words[0].lower() == "pre":
        return "Pre-Chorus"
    if words[0].lower() == "post":
        return "Post-Chorus"
    if text.lower() == "final chorus":
        return "Final Chorus"
    return " ".join(word.capitalize() for word in words)


def is_inline_note_line(line: str) -> bool:
    """가사 안에 삽입된 괄호 제작 주석 줄 판별 — 섹션 헤더는 제외."""
    stripped = line.strip()
    if not (stripped.startswith("[") and stripped.endswith("]")):
        return False
    return SECTION_PATTERN.match(stripped) is None


def strip_inline_notes(text: str) -> str:
    """추론 코퍼스에서 괄호 제작 주석 줄을 제거한다."""
    return "\n".join(ln for ln in text.splitlines() if not is_inline_note_line(ln))


def is_negative_tag(tag: str) -> bool:
    cleaned = tag.strip().lstrip()
    return cleaned.startswith(("-", "‑", "–", "—")) or cleaned.lower().startswith(("no ", "not "))


def positive_tag_text(text: str) -> str:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if "," in line:
            positive = [item.strip() for item in line.split(",") if item.strip() and not is_negative_tag(item)]
            if positive:
                lines.append(", ".join(positive))
            continue
        if line and not is_negative_tag(line):
            lines.append(line)
    return "\n".join(lines)


def clean_genre_text(text: str) -> str:
    return ", ".join(item.strip() for item in text.split(",") if item.strip() and not is_negative_tag(item))


def collect_preamble_tags(lines: list[str]) -> list[str]:
    tags: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("["):
            break
        if parse_key_value(line) or parse_loose_metadata(line):
            continue
        if "," in line:
            tags.extend(item.strip() for item in line.split(",") if item.strip() and not is_negative_tag(item))
        elif len(line) <= 120 and not is_negative_tag(line):
            tags.append(line)
    return tags


def keyword_present(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def stable_index(seed: str, size: int) -> int:
    if size <= 0:
        raise ValueError("size must be greater than zero")
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % size


def bpm_range(bpm_text: str) -> str:
    match = re.search(r"\b(\d{2,3})\b", bpm_text)
    if not match:
        return "medium"
    bpm = int(match.group(1))
    if bpm < 90:
        return "slow"
    if bpm < 120:
        return "medium"
    if bpm < 150:
        return "fast"
    return "very_fast"


def select_performance_profile(song: Song) -> tuple[str, dict]:
    corpus = f"{song.genre} {song.mood} {song.emotion} {song.stage_energy}".lower()
    tempo_range = bpm_range(song.bpm or song.tempo)
    candidates: list[tuple[int, str, dict]] = []

    for profile_key, profile in _PERFORMANCE_DATA["profiles"].items():
        keyword_score = sum(
            4 for keyword in profile.get("keywords", [])
            if keyword.lower() in corpus
        )
        tempo_score = 1 if tempo_range in profile.get("bpm_ranges", []) else 0
        candidates.append((keyword_score + tempo_score, profile_key, profile))

    best_score = max(score for score, _, _ in candidates)
    best = [(key, profile) for score, key, profile in candidates if score == best_score]
    if best_score <= 0:
        available = ", ".join(_PERFORMANCE_DATA["profiles"].keys())
        raise ValueError(
            f"[{song.title}] 퍼포먼스 프로파일 매칭 실패 — Genre/Mood 키워드가 어떤 프로파일과도 일치하지 않습니다.\n"
            f"사용 가능한 퍼포먼스 프로파일: {available}"
        )
    return best[stable_index(song.title, len(best))]


def performance_variant(
    song: Song,
    profile_key: str,
    profile: dict,
    field: str,
    variant_key: str,
) -> str:
    values = profile.get(field, [])
    if not values:
        return ""
    seed = f"{song.title}|{profile_key}|{field}|{variant_key}"
    return values[stable_index(seed, len(values))]


def performance_direction_block(file_name: str, song: Song) -> str:
    profile_key, profile = select_performance_profile(song)
    variant_key = Path(file_name).stem
    lighting = performance_variant(song, profile_key, profile, "lighting", variant_key)
    camera = performance_variant(song, profile_key, profile, "camera", variant_key)
    performance = performance_variant(song, profile_key, profile, "performance", variant_key)
    audience = performance_variant(song, profile_key, profile, "audience", variant_key)
    transition = performance_variant(song, profile_key, profile, "transitions", variant_key)
    safety = _PERFORMANCE_DATA["safety_rule"]

    if file_name == "09_video_motion_prompts.md":
        return f"""

## Song-Specific Performance Direction

Use this direction across the motion variants while preserving the uploaded source image.

- Profile: `{profile_key}` — {profile["name_ko"]}
- Stage geography: {profile["stage_layout"]}
- Camera movement: {camera}
- Vocal section performer motion: {performance}
- Guitar / Bass / Drum sections: instrument playing motion only — no singing, no microphone, no vocal gesture
- Stage / Atmosphere sections: full band wide concert shot — no close-up singing motion
- Audience motion: {audience}
- Lighting motion: {lighting}
- Recommended transition: {transition}
- Wardrobe continuity: {profile["wardrobe"]}
- Safety: {safety}

Apply the transition as an editing suggestion for CapCut or between generated clips. Do not ask the
video model to redesign the source image in order to create the transition.
"""

    return f"""

## Song-Specific Performance Direction

- Profile: `{profile_key}` — {profile["name_ko"]}
- Stage layout: {profile["stage_layout"]}
- Lighting composition: {lighting}
- Camera composition: {camera}
- Band performance: {performance}
- Audience treatment: {audience}
- Wardrobe variation: {profile["wardrobe"]}
- Safety: {safety}
"""


def infer_profile(raw_text: str, fields: dict[str, str]) -> dict[str, str]:
    # 가사 내 괄호 제작 주석([subway impact bass] 등)을 제거한 뒤 추론에 사용
    clean_text = strip_inline_notes(raw_text)
    tags = ", ".join(collect_preamble_tags(raw_text.splitlines()))
    positive_raw_text = positive_tag_text(clean_text)
    positive_genre = clean_genre_text(fields.get("genre", ""))
    corpus = " ".join([positive_raw_text, tags, positive_genre, fields.get("mood", "")])
    lower = corpus.lower()

    bpm = fields.get("bpm", "")
    bpm_match = re.search(r"\b(\d{2,3})\s*bpm\b", lower, re.IGNORECASE)
    if not bpm and bpm_match:
        bpm = f"{bpm_match.group(1)} BPM"

    genre = positive_genre or tags or "emotional cinematic pop"
    if bpm and bpm not in genre and re.search(r"\d", bpm):
        genre = f"{bpm} {genre}"

    data = _GENRE_DATA
    defaults = data["defaults"]
    gp = _match_profile(lower)
    if gp is None:
        available = ", ".join(p["name"] for p in _GENRE_DATA["profiles"])
        title = fields.get("title") or fields.get("song title") or "unknown"
        raise ValueError(
            f"[{title}] 장르 프로파일 매칭 실패 — Genre 키워드가 어떤 프로파일과도 일치하지 않습니다.\n"
            f"사용 가능한 장르 프로파일: {available}"
        )

    mood = (
        fields.get("mood")
        or _match_first(data["mood_rules"], lower, "mood")
        or defaults["mood"]
    )
    emotion = (
        fields.get("emotion")
        or _match_first(data["emotion_rules"], lower, "emotion")
        or defaults["emotion"]
    )

    tempo = fields.get("tempo") or (f"{bpm} groove" if bpm else "song-matched tempo and section rhythm")
    instruments = fields.get("instruments") or infer_instruments(lower)
    stage_energy = fields.get("energy") or (gp["stage_energy"] if gp else defaults["stage_energy"])
    lighting_style = gp["lighting_style"] if gp else defaults["lighting_style"]
    camera_style = gp["camera_style"] if gp else defaults["camera_style"]
    special_effects = gp["special_effects"] if gp else defaults["special_effects"]

    return {
        "genre": genre,
        "bpm": bpm,
        "mood": mood,
        "emotion": emotion,
        "tempo": tempo,
        "instruments": instruments,
        "stage_energy": stage_energy,
        "lighting_style": lighting_style,
        "camera_style": camera_style,
        "special_effects": special_effects,
    }


def infer_instruments(lower: str) -> str:
    terms: list[str] = []
    for term in ["guitar", "bass", "drum", "synth", "piano", "soft vocal",
                 "gayageum", "ajaeng", "taepyeongso", "haegeum"]:
        if term in lower:
            terms.append(term)
    if "신스" in lower:
        terms.append("warm synths")
    if "subway ambience" in lower or "열차" in lower or "환승" in lower:
        terms.append("subway ambience")
    return ", ".join(dict.fromkeys(terms)) or "vocal, guitar, bass, drums, cinematic atmosphere"




def parse_song(path: Path, title_override: str | None = None, title_fallback: str | None = None) -> Song:
    raw_text = read_text(path)
    lines = strip_noise_lines(raw_text)
    fields: dict[str, str] = {}
    for line in lines:
        parsed = parse_key_value(line.strip()) or parse_loose_metadata(line.strip())
        if parsed:
            key, value = parsed
            fields[key] = value
    title = infer_title(lines, fields, title_override, title_fallback)
    sections = parse_sections(lines)
    profile = infer_profile("\n".join(lines), fields)
    return Song(
        title=title,
        genre=profile["genre"],
        bpm=profile["bpm"],
        mood=profile["mood"],
        emotion=profile["emotion"],
        tempo=profile["tempo"],
        stage_energy=profile["stage_energy"],
        lighting_style=profile["lighting_style"],
        camera_style=profile["camera_style"],
        special_effects=profile["special_effects"],
        instruments=profile["instruments"],
        sections=sections,
        raw_text="\n".join(lines),
    )


def song_slug(title: str) -> str:
    forbidden = '<>:"/\\|?*'
    slug = "".join("_" if char in forbidden else char for char in title).strip().strip(".")
    if not slug:
        raise ValueError("폴더 이름으로 사용할 수 없는 곡 제목입니다.")
    return slug


def replacement_map(song: Song) -> dict[str, str]:
    roles = role_lines(song)
    ref_img = roles.get("reference_image", "base.png")
    return {
        "[SONG_TITLE]": song.title,
        "[GENRE]": song.genre,
        "[MOOD]": song.mood,
        "[TEMPO]": song.tempo,
        "[EMOTION]": song.emotion,
        "[STAGE_ENERGY]": song.stage_energy,
        "[LIGHTING_STYLE]": song.lighting_style,
        "[CAMERA_STYLE]": song.camera_style,
        "[SPECIAL_EFFECTS]": song.special_effects,
        "[CHARACTER_OUTFIT]": roles.get("outfit", ""),
        "[CHARACTER_OUTFIT_GIRL]": roles.get("outfit_girl", ""),
        "[CHARACTER_PROP]": roles.get("prop", ""),
        "[CHARACTER_COLOR]": roles.get("color", ""),
        "[CHARACTER_REFERENCE]": f"reference/{ref_img}",
        "[CHARACTER_VOCAL]": roles.get("vocal", ""),
        "[CHARACTER_VOCAL_ACTION]": roles.get("vocal_action", ""),
        "[CHARACTER_GUITAR]": roles.get("guitar", ""),
        "[CHARACTER_BASS]": roles.get("bass", ""),
        "[CHARACTER_DRUM]": roles.get("drum", ""),
        "[CHARACTER_CROWD]": roles.get("crowd", ""),
        "[CHARACTER_STAGE]": roles.get("stage", ""),
    }


def apply_reference_path(text: str) -> str:
    text = text.replace("[REFERENCE_DIR]", "reference")
    return text


def role_lines(song: Song) -> dict[str, str]:
    lower = positive_tag_text(strip_inline_notes(song.raw_text)).lower()
    profile = _match_profile(lower)
    return profile["roles"] if profile else _GENRE_DATA["defaults"]["roles"]


def _adapt_guitar(text: str, roles: dict[str, str]) -> str:  # noqa: ARG001
    return text


def _adapt_bass(text: str, roles: dict[str, str]) -> str:  # noqa: ARG001
    return text


def _adapt_drum(text: str, roles: dict[str, str]) -> str:
    """06_drum_image_prompt.md — rock 계열 무드 유지 여부 보정."""
    drum_desc = roles.get("drum", "")
    is_rock = any(kw in drum_desc.lower() for kw in ("rock", "metal", "punk", "aggressive", "powerful impact"))
    if not is_rock:
        text = text.replace("dark synthwave metal concert atmosphere,", "song-matched concert atmosphere,")
        text = text.replace("flying sparks, heavy smoke, flashing concert lights,", "stage atmosphere lighting,")
        text = text.replace("high contrast cinematic backlight,", "genre-matched cinematic backlight,")
    return text


def _adapt_stage(text: str, roles: dict[str, str]) -> str:  # noqa: ARG001
    return text


def _adapt_atmosphere(text: str, _roles: dict[str, str]) -> str:
    return text


def _adapt_video(text: str, roles: dict[str, str]) -> str:  # noqa: ARG001
    return text


# 파일별 전용 어댑터 조회 테이블 — 모두 (text, roles) 시그니처로 통일
_FILE_ADAPTERS: dict[str, object] = {
    "04_guitar_image_prompt.md":  _adapt_guitar,
    "05_bass_image_prompt.md":    _adapt_bass,
    "06_drum_image_prompt.md":    _adapt_drum,
    "07_stage_image_prompt.md":        _adapt_stage,
    "08_atmosphere_image_prompt.md":   _adapt_atmosphere,
    "09_video_motion_prompts.md":      _adapt_video,
}


def adapt_prompt_text(file_name: str, text: str, song: Song) -> str:
    # 1. 레퍼런스 경로 치환
    text = apply_reference_path(text)
    # 2. 전역 메타데이터 치환 ([SONG_TITLE], [GENRE] 등)
    for old, new in replacement_map(song).items():
        text = text.replace(old, new)
    # 2a. 치환 후 단독 쉼표만 남은 줄 제거 (vocal_action 등 선택 필드가 비었을 때)
    text = re.sub(r'^\s*,\s*$', '', text, flags=re.MULTILINE)
    # 3. [CHARACTER_*] 플레이스홀더는 replacement_map()에서 이미 처리됨
    roles = role_lines(song)
    # 4. 파일별 전용 처리 — 모든 어댑터가 (text, roles) 시그니처로 통일됨
    if file_name in _FILE_ADAPTERS:
        text = _FILE_ADAPTERS[file_name](text, roles)
    # 5. 실존 공연 자료에서 일반화한 곡별 무대/카메라/모션 방향 추가
    text += performance_direction_block(file_name, song)
    # 6. 장르별 잔여 표현 교체
    text = soften_aggressive_residue(text, song)
    # 7. 이미지/영상 플랫폼 정책 오탐 방지용 안전화
    text = safety_normalize_prompt(text)
    # 8. production_config.json 기준으로 영상 variant 수 조정
    if file_name == "09_video_motion_prompts.md":
        text = apply_production_mode(text)
    return text


_SAFETY_REPLACEMENTS: dict[str, str] = {
    # 잔여 스켈레톤 표현 안전화 (구 템플릿 호환)
    "same undead cyberpunk skeleton band": "same AI Boy/AI Girl chibi toy robot figures",
    "undead cyberpunk skeleton band": "AI Boy/AI Girl chibi toy robot figures",
    "A fixed undead cyberpunk skeleton band": "Fixed AI Boy/AI Girl chibi toy robot figures",
    "the same undead cyberpunk skeleton band": "the same AI Boy/AI Girl chibi toy robot figures",
    "skeleton vocalist": "AI Boy/AI Girl vocalist",
    "skeleton guitarist": "AI Boy/AI Girl guitarist",
    "skeleton bassist": "AI Boy/AI Girl bassist",
    "skeleton drummer": "AI Boy/AI Girl drummer",
    "skeleton band": "AI Boy/AI Girl toy figure band",
    "chained microphone": "decorative concert microphone",
    "mic chain": "microphone stand",
    "gripping the microphone": "holding the microphone",
    "rib cage": "chest area",
    "skeletal hand": "stylized chibi hand",
    "skeletal fingers": "stylized chibi fingers",
    "skeletal wrist": "stylized chibi wrist",
    "skull mouth": "screen-face display",
    "open skull mouth": "screen-face display singing",
    "skull tilting": "helmet tilting",
    "screams aggressively": "sings with high-energy rock intensity",
    "screaming into": "singing into",
    "aggressive guitar solo": "high-energy guitar solo",
    "aggressive emotional live performance": "high-energy emotional live performance",
    "headbanging": "rhythmic concert movement",
    # AI Boy/Girl 비현실 명시 안전화
    "realistic human": "non-realistic chibi toy figure",
    "photorealistic person": "3D chibi toy figure",
    "real human anatomy": "chibi toy proportions",
}


POLICY_RISK_TERMS: tuple[str, ...] = (
    "human remains",
    "body remains",
    "corpse",
    "blood",
    "gore",
    "weapon",
    "knife",
    "bound",
    "tied up",
    "realistic human anatomy",
    "photorealistic person",
    "live-action realism",
)


def safety_normalize_prompt(text: str) -> str:
    """정책 오탐을 줄이기 위해 공연·장식 맥락의 안전 표현으로 정규화한다."""
    for old, new in _SAFETY_REPLACEMENTS.items():
        text = text.replace(old, new)
    text = text.replace(
        "The visual identity must stay consistent with the reference images:",
        "The visual identity must stay consistent with the reference images. Keep it as a safe, non-violent music performance scene with concert-only props and decorative costume details:",
    )
    return text


_SOFT_RESIDUE_REPLACEMENTS: dict[str, str] = {
    # ── 비디오 템플릿 잔여 (기존) ────────────────────────────────────────────
    "crowd cheering wildly in the background,": "crowd phone lights shimmer quietly in the background,",
    "crowd silhouettes raising hands, headbanging, cheering wildly,": "crowd silhouettes gently swaying with quiet phone lights,",
    "intense live performance energy,": "restrained emotional live performance energy,",
    "dynamic low-angle camera movement,": "slow low-angle cinematic camera movement,",
    "dynamic camera movement,": "gentle cinematic camera movement,",
    "sparks flying,": "subtle glowing particles drifting,",
    "sparks and particles drifting through the air,": "soft particles drifting through the air,",
    "bass drum kick reverberating through the stage floor,": "drum beat settling quietly through the stage floor,",
    "magenta concert lights flashing,": "soft magenta concert lights pulsing,",
    "magenta lasers sweeping across the stage,": "slow magenta lasers drifting across the stage,",
    "slow powerful body movement,": "restrained body movement with the groove,",
    "dramatic front-facing camera push-in,": "slow front-facing camera push-in,",
    "drumsticks moving with powerful rhythm,": "drumsticks moving with restrained rhythm,",
    "cymbals shaking,": "gentle cymbal shimmer,",
    "smoke bursts behind the drum set,": "soft smoke drifts behind the drum set,",
    "magenta backlight flashing from the neon moon,": "magenta backlight pulsing softly from the neon moon,",
    "crowd hands waving,": "crowd hands swaying slowly,",
    "epic concert lighting movement,": "warm restrained concert lighting movement,",
    "massive cyberpunk concert atmosphere,": "bittersweet cyberpunk concert atmosphere,",
    # ── 이미지 템플릿 잔여 (신규) ─────────────────────────────────────────────
    # 03 vocal
    "heavy smoke and sparks around the vocalist,": "soft smoke and gentle particles around the vocalist,",
    # 04 guitar
    "dynamic low-angle camera shot,": "gentle close-up camera shot,",
    "smoke, sparks, laser beams, intense stage lighting,": "soft smoke, gentle particles, warm intimate stage lighting,",
    "fast energetic performance feeling,": "restrained emotional performance feeling,",
    "dark synthwave metal concert atmosphere,": "bittersweet cyberpunk concert atmosphere,",
    "crowd silhouettes cheering below the stage,": "crowd silhouettes gently swaying below the stage,",
    # 05 bass
    "deep bass performance energy,": "gentle bass groove energy,",
    "volumetric smoke, sparks, magenta laser lights,": "subtle smoke, soft particles, warm magenta glow,",
    "powerful low-end concert atmosphere,": "warm intimate low-end concert atmosphere,",
    # 06 drum
    "powerful rhythm and impact,": "restrained rhythmic pulse,",
    # 07 stage
    "epic live concert scale,": "intimate live concert scale,",
    "dark synthwave metal atmosphere,": "bittersweet cyberpunk concert atmosphere,",
    # 08 crowd
    "flashing magenta lights, lasers, smoke, sparks,": "soft magenta glow, gentle haze, warm phone lights,",
    "epic festival-scale live performance atmosphere,": "intimate live performance warmth,",
    "high contrast dark synthwave metal lighting,": "warm soft magenta concert lighting,",
}

_GROOVE_RESIDUE_REPLACEMENTS: dict[str, str] = {
    "crowd cheering wildly in the background,": "crowd dancing with groove energy in the background,",
    "crowd silhouettes raising hands, headbanging, cheering wildly,": "crowd silhouettes dancing with infectious groove energy,",
    "intense live performance energy,": "infectious groove performance energy,",
    "dynamic low-angle camera movement,": "fluid groove-matched camera movement,",
    "dynamic camera movement,": "fluid groove-matched camera movement,",
    "dramatic front-facing camera push-in,": "fluid groove-tracking camera push-in,",
    "sparks flying,": "golden light particles drifting,",
    "sparks and particles drifting through the air,": "golden light particles drifting through the air,",
    "bass drum kick reverberating through the stage floor,": "groove kick pulse rolling through the stage floor,",
    "magenta concert lights flashing,": "warm pulsing rhythm lights,",
    "magenta lasers sweeping across the stage,": "warm neon lasers sweeping the groove stage,",
    "slow powerful body movement,": "rhythmic groove body sway,",
    "drumsticks moving with powerful rhythm,": "drumsticks moving with infectious groove rhythm,",
    "cymbals shaking,": "cymbals catching the groove pulse,",
    "smoke bursts behind the drum set,": "warm haze drifts behind the drum set,",
    "magenta backlight flashing from the neon moon,": "warm neon backlight pulsing with the rhythm,",
    "crowd hands waving,": "crowd hands moving with the groove,",
    "epic concert lighting movement,": "pulsing groove lighting movement,",
    "massive cyberpunk concert atmosphere,": "vibrant groove-driven concert atmosphere,",
    "high contrast cinematic backlight,": "warm ambient groove backlight,",
    # ── 이미지 템플릿 잔여 (신규) ─────────────────────────────────────────────
    "heavy smoke and sparks around the vocalist,": "warm haze and golden particles around the vocalist,",
    "dynamic low-angle camera shot,": "fluid groove-angle camera shot,",
    "smoke, sparks, laser beams, intense stage lighting,": "warm haze, golden particles, groove-lit stage lighting,",
    "fast energetic performance feeling,": "infectious groove performance feeling,",
    "dark synthwave metal concert atmosphere,": "vibrant groove-driven concert atmosphere,",
    "crowd silhouettes cheering below the stage,": "crowd silhouettes dancing with groove below the stage,",
    "deep bass performance energy,": "groove-locked bass energy,",
    "volumetric smoke, sparks, magenta laser lights,": "warm haze, golden light particles, rhythm neon glow,",
    "powerful low-end concert atmosphere,": "groove-locked low-end concert atmosphere,",
    "powerful rhythm and impact,": "infectious groove rhythm and pulse,",
    "epic live concert scale,": "vibrant groove concert scale,",
    "dark synthwave metal atmosphere,": "vibrant groove-driven concert atmosphere,",
    "flashing magenta lights, lasers, smoke, sparks,": "pulsing warm lights, groove neon glow, stage haze,",
    "epic festival-scale live performance atmosphere,": "infectious groove festival atmosphere,",
    "high contrast dark synthwave metal lighting,": "warm groove concert lighting,",
}

_RETRO_RESIDUE_REPLACEMENTS: dict[str, str] = {
    "crowd cheering wildly in the background,": "crowd swaying with dramatic retro energy in the background,",
    "crowd silhouettes raising hands, headbanging, cheering wildly,": "crowd silhouettes dancing with 80s retro energy,",
    "intense live performance energy,": "dramatic retro performance energy,",
    "dynamic low-angle camera movement,": "slow dramatic 80s camera movement,",
    "dramatic front-facing camera push-in,": "slow theatrical retro camera push-in,",
    "sparks flying,": "retro scan-line light bursts,",
    "magenta concert lights flashing,": "cyan-magenta retro concert lights pulsing,",
    "slow powerful body movement,": "theatrical dramatic body movement,",
    "drumsticks moving with powerful rhythm,": "drumsticks moving with synth-driven 80s power,",
    "cymbals shaking,": "cymbals glinting under retro strobe,",
    "smoke bursts behind the drum set,": "analog synth haze drifts behind the drum set,",
    "magenta backlight flashing from the neon moon,": "cyan-magenta neon backlight pulsing from above,",
    "crowd hands waving,": "crowd hands raised with retro concert energy,",
    "epic concert lighting movement,": "dramatic 80s concert lighting sweep,",
    "massive cyberpunk concert atmosphere,": "retro cyberpunk concert atmosphere,",
    "high contrast cinematic backlight,": "retro high-contrast neon backlight,",
    # ── 이미지 템플릿 잔여 (신규) ─────────────────────────────────────────────
    "heavy smoke and sparks around the vocalist,": "analog synth haze and scan-line particles around the vocalist,",
    "dynamic low-angle camera shot,": "dramatic 80s camera shot,",
    "smoke, sparks, laser beams, intense stage lighting,": "analog synth haze, scan-lines, cyan-magenta stage lighting,",
    "fast energetic performance feeling,": "dramatic retro performance feeling,",
    "dark synthwave metal concert atmosphere,": "retro synthwave concert atmosphere,",
    "crowd silhouettes cheering below the stage,": "crowd silhouettes swaying with 80s retro energy below the stage,",
    "deep bass performance energy,": "synth-driven bass energy,",
    "volumetric smoke, sparks, magenta laser lights,": "analog haze, retro scan-lines, cyan-magenta laser glow,",
    "powerful low-end concert atmosphere,": "dramatic retro bass concert atmosphere,",
    "powerful rhythm and impact,": "theatrical drum machine rhythm,",
    "epic live concert scale,": "dramatic 80s concert scale,",
    "dark synthwave metal atmosphere,": "retro synthwave concert atmosphere,",
    "flashing magenta lights, lasers, smoke, sparks,": "cyan-magenta strobes, retro grid lasers, analog haze,",
    "epic festival-scale live performance atmosphere,": "dramatic 80s retro festival atmosphere,",
    "high contrast dark synthwave metal lighting,": "retro high-contrast synth concert lighting,",
}

_HIPHOP_RESIDUE_REPLACEMENTS: dict[str, str] = {
    "crowd cheering wildly in the background,": "crowd hyping with raised fists in the background,",
    "crowd silhouettes raising hands, headbanging, cheering wildly,": "crowd silhouettes throwing up hands with hip-hop energy,",
    "intense live performance energy,": "raw hip-hop cipher performance energy,",
    "dynamic low-angle camera movement,": "power-stance low-angle hip-hop camera movement,",
    "dramatic front-facing camera push-in,": "low-angle hip-hop power camera push-in,",
    "sparks flying,": "camera flash bursts synced to the beat,",
    "magenta concert lights flashing,": "strobing stage lights cutting on the break,",
    "magenta lasers sweeping across the stage,": "beam lights sweeping across the cypher stage,",
    "slow powerful body movement,": "controlled hip-hop body movement,",
    "drumsticks moving with powerful rhythm,": "drumsticks moving with hip-hop precision,",
    "cymbals shaking,": "hi-hat crisp snap on every beat,",
    "smoke bursts behind the drum set,": "low stage haze rolling behind the kit,",
    "magenta backlight flashing from the neon moon,": "hard backlight silhouetting the crowd,",
    "crowd hands waving,": "crowd throwing up hands on the break,",
    "epic concert lighting movement,": "beat-synced lighting cutting through the smoke,",
    "massive cyberpunk concert atmosphere,": "raw underground hip-hop concert atmosphere,",
    "high contrast cinematic backlight,": "gritty high-contrast hip-hop backlight,",
    # ── 이미지 템플릿 잔여 (신규) ─────────────────────────────────────────────
    "heavy smoke and sparks around the vocalist,": "low stage haze and strobe flash around the vocalist,",
    "dynamic low-angle camera shot,": "power-stance hip-hop low-angle camera shot,",
    "smoke, sparks, laser beams, intense stage lighting,": "low haze, strobe flash, beat-synced stage lighting,",
    "fast energetic performance feeling,": "raw hip-hop cipher performance energy,",
    "dark synthwave metal concert atmosphere,": "gritty underground hip-hop concert atmosphere,",
    "crowd silhouettes cheering below the stage,": "crowd silhouettes hyping with fists below the stage,",
    "deep bass performance energy,": "hard-hitting hip-hop bass energy,",
    "volumetric smoke, sparks, magenta laser lights,": "low stage haze, strobe flash, neon cipher glow,",
    "powerful low-end concert atmosphere,": "hard-hitting hip-hop low-end concert atmosphere,",
    "powerful rhythm and impact,": "hard-hitting hip-hop kick and snare impact,",
    "epic live concert scale,": "raw underground hip-hop concert scale,",
    "dark synthwave metal atmosphere,": "gritty urban hip-hop concert atmosphere,",
    "flashing magenta lights, lasers, smoke, sparks,": "hard backlights, strobe cuts, cipher smoke,",
    "epic festival-scale live performance atmosphere,": "raw hip-hop cipher concert atmosphere,",
    "high contrast dark synthwave metal lighting,": "gritty high-contrast hip-hop concert lighting,",
}

_SOFT_GENRE_KEYWORDS = ["subway", "환승", "열차", "역", "indie", "soft", "ballad", "acoustic", "pop rap", "melodic rap", "힘들", "웃어", "lo-fi", "lofi", "jazz ballad", "bossa nova", "swing", "bebop", "smooth jazz", "psychedelic"]
_GROOVE_GENRE_KEYWORDS = ["afrobeats", "afro pop", "afrobeat", "tropical house", "acid house", "groovy house", "nu-disco", "city pop"]
_RETRO_GENRE_KEYWORDS = ["synth-pop", "synthpop", "new wave", "80s retro", "1980s synth", "retro synth"]
_HIPHOP_GENRE_KEYWORDS = ["boom bap", "hip-hop", "hip hop", "industrial trap"]

# 장르 프로파일 이름 → 잔여 교체 유형 매핑.
# genre_profiles.json의 "softening_type" 필드에서 동적으로 로드한다.
# 새 장르 추가 시 genre_profiles.json만 편집하면 됨 — 코드 수정 불필요.
_PROFILE_SOFTENING_MAP: dict[str, str | None] = {
    p["name"]: p.get("softening_type")
    for p in _GENRE_DATA.get("profiles", [])
}


def soften_aggressive_residue(text: str, song: Song) -> str:
    # 1차: 프로파일 기반 (genre_profiles.json 단일 소스)
    # strip_inline_notes 필수: 섹션 헤더([Chorus: Rock feel...] 등)의
    # 키워드가 _match_profile을 오염시키는 것을 방지한다.
    clean_lower = positive_tag_text(strip_inline_notes(song.raw_text)).lower()
    profile = _match_profile(clean_lower)
    softening_type = _PROFILE_SOFTENING_MAP.get(profile["name"]) if profile else None

    if softening_type is not None:
        replacements_map = {
            "soft": _SOFT_RESIDUE_REPLACEMENTS,
            "groove": _GROOVE_RESIDUE_REPLACEMENTS,
            "retro": _RETRO_RESIDUE_REPLACEMENTS,
            "hiphop": _HIPHOP_RESIDUE_REPLACEMENTS,
        }
        replacements = replacements_map.get(softening_type)
        if replacements:
            for old, new in replacements.items():
                text = text.replace(old, new)
        return text

    # 2차: 키워드 기반 폴백 (프로파일에 softening_type 없는 경우)
    lower = positive_tag_text(song.raw_text).lower()
    is_soft   = keyword_present(lower, _SOFT_GENRE_KEYWORDS)
    is_groove = keyword_present(lower, _GROOVE_GENRE_KEYWORDS)
    is_retro  = keyword_present(lower, _RETRO_GENRE_KEYWORDS)
    is_hiphop = keyword_present(lower, _HIPHOP_GENRE_KEYWORDS)
    # lo-fi 우선순위: lo-fi 계열은 hip-hop 잔여 교체 대신 soft 적용
    if is_hiphop and keyword_present(lower, ["lo-fi", "lofi", "lo fi"]):
        is_hiphop = False
        is_soft = True
    if not any([is_soft, is_groove, is_retro, is_hiphop]):
        return text
    if is_soft:
        for old, new in _SOFT_RESIDUE_REPLACEMENTS.items():
            text = text.replace(old, new)
    if is_groove:
        for old, new in _GROOVE_RESIDUE_REPLACEMENTS.items():
            text = text.replace(old, new)
    if is_retro:
        for old, new in _RETRO_RESIDUE_REPLACEMENTS.items():
            text = text.replace(old, new)
    if is_hiphop:
        for old, new in _HIPHOP_RESIDUE_REPLACEMENTS.items():
            text = text.replace(old, new)
    return text


def _filter_variant_sections(text: str, clip_counts: dict[str, int]) -> str:
    for part_name, config_key in _PART_CONFIG_KEYS.items():
        clip_count = clip_counts.get(config_key, 4)
        # clips 수는 기본 프롬프트(1개) 포함. variant 수 = clips - 1
        max_variants = min(max(0, clip_count - 1), 3)

        if max_variants >= 3:
            continue  # A/B/C 전부 유지

        pattern = rf"### {part_name} Variants\n\n```text\n(.*?)\n```"

        if max_variants == 0:
            # 기본 프롬프트만 사용 → variant 섹션 전체 제거
            text = re.sub(pattern + r"\n*", "", text, flags=re.DOTALL)
        else:
            def make_replacer(n: int, pname: str):
                def replacer(match: re.Match) -> str:
                    block = match.group(1)
                    parts = re.split(r"\n\n(?=Variant [A-C] -)", block)
                    kept = "\n\n".join(parts[:n])
                    return f"### {pname} Variants\n\n```text\n{kept}\n```"
                return replacer

            text = re.sub(pattern, make_replacer(max_variants, part_name), text, flags=re.DOTALL)

    return text


def _replace_capcut_map(text: str, capcut_cfg: dict) -> str:
    sections = capcut_cfg.get("sections", [])
    reuse_note = capcut_cfg.get("reuse_note", "")
    if not sections:
        return text
    map_lines = "\n".join(sections)
    note_line = f"\nNote: {reuse_note}" if reuse_note else ""
    new_block = (
        "## CapCut Editing Map\n\n"
        "Use the best generated clips first. Reuse strong chorus clips intentionally; repeated performance shots\n"
        "feel natural if they return on chorus hooks.\n\n"
        f"```text\n{map_lines}\n```"
        f"{note_line}"
    )
    text = re.sub(
        r"## CapCut Editing Map.*?(?=## Song-Specific Performance Direction|\Z)",
        new_block + "\n\n",
        text,
        flags=re.DOTALL,
    )
    return text


def apply_production_mode(text: str) -> str:
    mode_name = _PRODUCTION_CONFIG.get("mode", "")
    mode = _PRODUCTION_CONFIG.get("modes", {}).get(mode_name, {})
    if not mode:
        return text
    clip_counts = mode.get("clips", {})
    capcut_cfg = mode.get("capcut_map", {})
    if clip_counts:
        text = _filter_variant_sections(text, clip_counts)
    if capcut_cfg:
        text = _replace_capcut_map(text, capcut_cfg)
    return text


def ensure_reference_folder(reference_dir: Path) -> None:
    if not reference_dir.exists():
        raise FileNotFoundError(f"기준 이미지 폴더가 없습니다: {reference_dir}")
    if not reference_dir.is_dir():
        raise NotADirectoryError(f"기준 이미지 경로가 폴더가 아닙니다: {reference_dir}")
    if not any(reference_dir.iterdir()):
        raise FileNotFoundError(f"기준 이미지 폴더가 비어 있습니다: {reference_dir}")


def remove_existing_folder(path: Path) -> None:
    for child in path.iterdir():
        if child.is_symlink():
            run_with_file_retries("delete", child, child.unlink)
        elif child.is_dir():
            remove_existing_folder(child)
        else:
            run_with_file_retries("delete", child, child.unlink)
    run_with_file_retries("remove folder", path, path.rmdir)


def create_song_folder(
    song: Song,
    template_dir: Path,
    output_dir: Path,
    force: bool = False,
    reference_dir: Path = REFERENCE_DIR,
) -> Path:
    destination = output_dir / song_slug(song.title)
    if destination.exists():
        if not force:
            raise FileExistsError(f"이미 폴더가 있습니다: {destination}. 덮어쓰려면 --force를 사용하세요.")
        remove_existing_folder(destination)
    destination.mkdir(parents=True, exist_ok=True)
    ensure_reference_folder(reference_dir)
    for file_name in PROMPT_FILES:
        source = template_dir / file_name
        if not source.exists():
            raise FileNotFoundError(f"템플릿 파일이 없습니다: {source}")
        text = adapt_prompt_text(file_name, read_text(source), song)
        write_text(destination / file_name, text)
    write_text(destination / "README.md", build_readme(song))
    return destination


def section_clip_name(section: Section) -> str:
    label = section.label.lower().replace(" ", "_").replace("-", "_")
    if "chorus" in label:
        return "stage_chorus_01, vocal_chorus_01, atmosphere_chorus_01"
    if "bridge" in label or "build" in label:
        return "vocal_bridge_01, bass_song_pulse_01, drum_song_pulse_01"
    if "verse" in label:
        return "vocal_verse_01, guitar_verse_01"
    if "intro" in label or "outro" in label:
        return "stage_intro_01, atmosphere_outro_01"
    return "stage_intro_01, vocal_verse_01"


def is_arrangement_note_line(line: str) -> bool:
    return bool(re.fullmatch(r"\[(Instrumentation|Harmony|Arrangement|Production|Vocal|Backing Vocals):.*\]", line.strip(), re.IGNORECASE))


def section_display_text(section: Section) -> str:
    lyric_lines = [line for line in section.lines if line.strip() and not is_arrangement_note_line(line)]
    lyric = "\n".join(lyric_lines).strip()
    if lyric:
        return lyric
    return section.note or "Instrumental section"


def _section_edit_note(label: str, song: Song, roles: dict) -> str:
    lower = label.lower()
    camera_first = song.camera_style.split(",")[0].strip()
    lighting_first = song.lighting_style.split(",")[0].strip()
    energy_first = song.stage_energy.split(",")[0].strip()
    crowd = roles["crowd"]
    if "chorus" in lower or "final" in lower:
        camera_note = f"넓은 무대 컷 → 보컬 클로즈업 → 분위기 컷 순으로 편집한다. | {camera_first}"
    elif "verse" in lower:
        camera_note = f"보컬 클로즈업 위주, 악기 컷 간간이 삽입 | {camera_first}"
    elif "bridge" in lower or "build" in lower:
        camera_note = f"드라마틱 전환 — 드럼·베이스 샷 혼합 | {camera_first}"
    elif "intro" in lower:
        camera_note = f"와이드 샷으로 시작 → {camera_first} 으로 전환"
    elif "outro" in lower:
        camera_note = f"{camera_first} → 와이드 풀아웃으로 마무리"
    elif "pre" in lower:
        camera_note = f"긴장감 쌓기 | {camera_first}"
    else:
        camera_note = camera_first
    return (
        f"카메라: {camera_note}\n"
        f"조명: {lighting_first}\n"
        f"관중: {crowd}\n"
        f"에너지: {energy_first}\n"
        f"캐릭터와 밴드 정체성은 reference 폴더 이미지를 기준으로 유지한다."
    )


def build_readme(song: Song) -> str:
    roles = role_lines(song)
    ref_img = roles.get("reference_image", "base.png")
    vocal_action = roles.get("vocal_action", "")
    sections = []
    for section in song.sections:
        lyric = section_display_text(section)
        edit_note = _section_edit_note(section.label, song, roles)
        sections.append(
            f"""### {section.label}

```text
{lyric}
```

추천 컷:

```text
{section_clip_name(section)}
```

편집:

```text
{edit_note}
```
"""
        )
    no_lyric_note = "```text\n가사 없음 — 장르와 분위기 기반으로 연출한다.\n전체 무대 컷 위주로 편집하고, 장르 에너지에 맞춰 카메라 속도와 조명을 조절한다.\n```\n"
    section_text = "\n".join(sections) if sections else no_lyric_note
    vocal_action_line = f"\n보컬 액션: {vocal_action}" if vocal_action else ""
    return f"""# {song.title} MV 제작 순서

이 문서는 `{song.title}`을 기준으로 GPT 이미지에서 장면 이미지를 만들고, Flow 또는 Kling AI 같은 영상 도구에서 클립으로 변환한 뒤 편집하는 순서다.

## 0. 곡 방향

```text
제목: {song.title}
장르: {song.genre}
템포: {song.tempo}
분위기: {song.mood}
감정: {song.emotion}
무대 에너지: {song.stage_energy}
조명: {song.lighting_style}
카메라: {song.camera_style}
특수효과: {song.special_effects}
```

## 역할별 연출 방향

```text
보컬: {roles["vocal"]}{vocal_action_line}
기타: {roles["guitar"]}
베이스: {roles["bass"]}
드럼: {roles["drum"]}
관중: {roles["crowd"]}
무대: {roles["stage"]}
```

이 곡의 기준 이미지: `reference/{ref_img}` — 이미지 생성 시 AI 도구에 이 파일을 첨부한다.
AI Boy/AI Girl 치비 토이 피규어 정체성은 그대로 유지하고, 영상 연출만 이 곡의 장르와 감정에 맞게 바꾼다.

## 1. 사용할 프롬프트

```text
{chr(10).join(PROMPT_FILES)}
```

## 2. 이미지 생성 순서

### 1단계 — 마스터 이미지 생성 (reference 첨부)

```text
첨부 파일: reference/{ref_img}
실행 프롬프트: 01_master_style_prompt.md
저장 파일명: master.png
```

`reference/{ref_img}` 를 AI 도구에 첨부하고 `01_master_style_prompt.md` 를 실행한다.
결과 이미지를 `master.png` 로 저장한다. 이 이미지가 이후 모든 생성의 기준이 된다.

### 2단계 — 역할별 이미지 생성 (master.png 첨부)

```text
첨부 파일: master.png  ← reference 대신 이것을 첨부한다
실행 순서:
1. 07_stage_image_prompt.md   → 무대.png
2. 03_vocal_image_prompt.md   → 보컬.png
3. 04_guitar_image_prompt.md  → 기타.png
4. 05_bass_image_prompt.md    → 베이스.png
5. 06_drum_image_prompt.md    → 드럼.png
6. 08_atmosphere_image_prompt.md → 분위기.png
```

`master.png` 를 첨부해야 캐릭터 스타일과 무대 색감이 1단계와 일치한다.

### 3단계 — 영상 클립 생성 (각 역할 이미지 첨부)

```text
09_video_motion_prompts.md 실행 시 각 역할 이미지를 첨부한다:
  보컬 클립  → 보컬.png 첨부
  기타 클립  → 기타.png 첨부
  베이스 클립 → 베이스.png 첨부
  드럼 클립  → 드럼.png 첨부
  무대 클립  → 무대.png 첨부
  분위기 클립 → 분위기.png 첨부
```

## 3. 가사 기준 편집 순서

{section_text}
## 4. 최종 확인

```text
[ 1단계 ] reference/{ref_img} 를 첨부하고 master.png 를 생성했는가?
[ 2단계 ] master.png 를 첨부하고 역할별 이미지(보컬·기타·베이스·드럼·무대·분위기)를 생성했는가?
[ 3단계 ] 각 역할 이미지를 첨부하고 09_video_motion_prompts 로 영상 클립을 생성했는가?
AI Boy/AI Girl 치비 토이 피규어 스타일이 끝까지 동일한가?
곡 장르와 감정에 맞게 보컬, 기타, 베이스, 드럼, 분위기, 전체 무대 연출이 바뀌었는가?
이전 곡 제목, 가사, 장르, 무드가 남아 있지 않은가?
placeholder가 남아 있지 않은가?
```
"""


def truncate_line(text: str, limit: int = 180) -> str:
    compact = re.sub(r"\s+", " ", text.strip())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def extract_purpose(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("purpose:"):
            return truncate_line(stripped.split(":", 1)[1], 120)
    return ""


def extract_prompt_cue(text: str) -> str:
    skip_prefixes = (
        "#",
        "```",
        "Use the attached",
        "The fixed reference",
        "Follow the style lock",
        "same ",
        "16:9",
        "Song title:",
        "Genre:",
        "Mood:",
        "Core emotion:",
        "Stage energy:",
        "Lighting style:",
        "Special effects:",
        "Do not ",
        "Do not change",
        "Do not make",
        "Do not remove",
        "Purpose:",
    )
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("-")
        if not line or line.startswith(skip_prefixes):
            continue
        if any(term in line.lower() for term in ["skeleton", "stage", "crowd", "camera", "lighting", "motion"]):
            return truncate_line(line, 180)
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("-")
        if line and not line.startswith(skip_prefixes):
            return truncate_line(line, 180)
    return ""


def prompt_placeholders(text: str) -> list[str]:
    matches = re.findall(_PLACEHOLDER_PATTERN, text)
    return sorted(set(matches))


def prompt_file_report(folder: Path, file_name: str) -> dict[str, object]:
    path = folder / file_name
    report: dict[str, object] = {
        "file": file_name,
        "area": PROMPT_AREA_LABELS.get(file_name, file_name),
        "exists": path.exists(),
        "chars": 0,
        "purpose": "",
        "cue": "",
        "identity_lock": False,
        "reference": False,
        "placeholders": [],
    }
    if not path.exists():
        return report
    text = read_text(path)
    report["chars"] = len(text)
    report["purpose"] = extract_purpose(text)
    report["cue"] = extract_prompt_cue(text)
    report["identity_lock"] = has_identity_lock(text)
    report["reference"] = "reference" in text
    report["placeholders"] = prompt_placeholders(text)
    return report


def prompt_reports(folder: Path) -> list[dict[str, object]]:
    return [prompt_file_report(folder, file_name) for file_name in PROMPT_FILES]


def status_text(errors: list[str]) -> str:
    return "PASS" if not errors else "CHECK"


def korean_scene_descriptions(song: Song) -> list[tuple[str, str, str]]:
    return [
        (
            "01_master_style_prompt.md",
            "전체 세계관 기준 장면",
            (
                f"AI Boy/AI Girl 치비 토이 로봇 피규어가 장르 무대 위에 서 있는 MV 기준 장면이다. "
                f"곡의 분위기는 '{song.mood}', 핵심 감정은 '{song.emotion}'이며, "
                f"이 장면을 기준으로 캐릭터 외형, 의상, 무대 색감, 3D 치비 토이 스타일이 모든 씬에서 유지되어야 한다."
            ),
        ),
        (
            "02_style_lock_prompt.md",
            "고정 캐릭터/무대 유지 기준",
            (
                "새로운 영상이나 이미지를 만들 때 AI Boy/AI Girl 치비 토이 로봇 피규어, 스크린 페이스, "
                "라운드 헬멧, 장르별 의상, 무대가 다른 디자인으로 바뀌지 않도록 막는 기준 설명이다."
            ),
        ),
        (
            "03_vocal_image_prompt.md",
            "보컬 클로즈업 장면",
            (
                f"AI Boy/AI Girl 보컬이 마이크를 잡고 노래하는 근접 장면이다. '{song.emotion}' 감정이 "
                f"스크린 페이스 디스플레이, 손 제스처, 시선 방향으로 드러나야 한다. "
                "곡의 가장 감정적인 썸네일 또는 후렴 클로즈업으로 쓸 수 있어야 정상이다."
            ),
        ),
        (
            "04_guitar_image_prompt.md",
            "기타 연주 장면",
            (
                f"AI Boy/AI Girl 기타리스트가 장르 '{song.genre}'에 맞는 강도로 연주하는 장면이다. "
                "치비 토이 손이 프렛보드 위에서 움직이고, 몸은 리듬에 맞게 기울어지며, "
                "보컬 감정을 받쳐주는 연주 느낌이 보여야 한다."
            ),
        ),
        (
            "05_bass_image_prompt.md",
            "베이스 연주 장면",
            (
                f"AI Boy/AI Girl 베이시스트가 '{song.tempo}' 흐름에 맞춰 그루브를 만드는 장면이다. "
                "베이스 줄을 튕기는 치비 손, 박자에 맞춘 고개 움직임, 낮은 무대 조명이 보여야 한다."
            ),
        ),
        (
            "06_drum_image_prompt.md",
            "드럼 연주 장면",
            (
                f"AI Boy/AI Girl 드러머가 곡의 에너지 '{song.stage_energy}'에 맞춰 드럼을 치는 장면이다. "
                "스틱 움직임, 심벌 흔들림, 뒤쪽 백라이트가 보여야 한다."
            ),
        ),
        (
            "07_stage_image_prompt.md",
            "전체 무대 와이드 장면",
            (
                f"AI Boy/AI Girl 피규어들이 한 화면에 들어오는 전체 공연 장면이다. "
                f"조명은 '{song.lighting_style}' 방향이고, 카메라는 '{song.camera_style}' 느낌으로 무대 전체를 보여준다. "
                "캐릭터 구성과 세계관이 가장 명확하게 보여야 정상이다."
            ),
        ),
        (
            "08_atmosphere_image_prompt.md",
            "분위기/실루엣 장면",
            (
                "AI Boy/AI Girl 실루엣이 무대 조명 앞에 서 있는 분위기 장면이다. 안개, 연기, 파티클이 "
                "배경을 채우며 MV의 Intro·Bridge·Outro 분위기를 표현한다. "
                "장르 조명과 무드가 자동 반영된다."
            ),
        ),
        (
            "09_video_motion_prompts.md",
            "영상 모션 클립 설명",
            (
                "생성한 보컬, 기타, 베이스, 드럼, 전체 무대, 분위기 이미지를 5~10초짜리 MV 클립으로 움직이는 설명이다. "
                "보컬은 카메라 밀기와 스크린 페이스·손 움직임, 기타/베이스는 치비 손과 몸의 리듬, "
                "드럼은 스틱과 심벌, 분위기 컷은 안개·실루엣 움직임이 보여야 한다."
            ),
        ),
    ]


def build_song_prompt_overview(song: Song, folder: Path, validation_errors: list[str]) -> str:
    performance_key, performance_profile = select_performance_profile(song)
    scene_blocks = []
    for file_name, title, description in korean_scene_descriptions(song):
        exists = "있음" if (folder / file_name).exists() else "없음"
        scene_blocks.append(
            f"""### {title}

- 대상 프롬프트: `{file_name}`
- 파일 존재: {exists}
- 영상 설명: {description}
"""
        )

    section_labels = ", ".join(section.label for section in song.sections) if song.sections else "섹션 정보 없음"
    validation_text = "정상" if not validation_errors else "확인 필요"
    validation_lines = "" if not validation_errors else "\n".join(f"- {error}" for error in validation_errors)
    return f"""# {song.title} 영상 설명

이 파일은 사람이 프롬프트 정상 여부를 빠르게 확인하기 위한 한글 영상 설명 파일이다.
아래 설명과 실제 프롬프트 내용이 같은 방향이면 정상으로 보면 된다.

## 전체 MV 방향

`{song.title}`은 `{song.genre}` 기반의 곡이며, 감정 방향은 `{song.emotion}`이다.
전체 영상은 고정된 AI Boy/AI Girl 치비 토이 로봇 피규어가 장르 콘서트 무대에서 공연하는 MV여야 한다.
곡의 템포는 `{song.tempo}`, 무대 에너지는 `{song.stage_energy}`이고, 조명은 `{song.lighting_style}` 방향이다.
카메라는 `{song.camera_style}` 느낌으로 움직이며, 곡 섹션은 {section_labels} 순서로 이어진다.

## 프롬프트별 영상 설명

## Performance Profile

- Profile: `{performance_key}` — {performance_profile["name_ko"]}
- Stage layout: {performance_profile["stage_layout"]}
- Selection basis: genre, BPM, mood, emotion, and stage energy
- Rights boundary: transformed concert-production attributes only; no real artist imitation

{chr(10).join(scene_blocks)}
## 정상 여부 확인

- 검증 상태: {validation_text}
- 확인 기준: 각 프롬프트가 위 영상 설명처럼 보컬, 기타, 베이스, 드럼, 전체 무대, 관객, 영상 모션 역할을 분명히 가지면 정상이다.
- 주의 기준: 곡 감정과 맞지 않는 과격한 연출, 다른 곡 제목이나 분위기 잔여물, 고정 밴드 디자인 변경, 인간 캐릭터 변환이 보이면 비정상이다.
{validation_lines}
"""


def write_song_prompt_overview(song: Song, folder: Path, validation_errors: list[str]) -> Path:
    path = folder / SONG_OVERVIEW_FILE
    write_text(path, build_song_prompt_overview(song, folder, validation_errors))
    return path


def display_path(path: Path, base: Path | None = None) -> str:
    base_dir = (base or PROJECT_ROOT.parent).resolve()
    try:
        return str(path.resolve().relative_to(base_dir))
    except ValueError:
        return str(path)


def build_all_prompt_overview(rows: list[dict[str, object]]) -> str:
    table_rows = []
    for row in rows:
        table_rows.append(
            "| {title} | {status} | {files} | {genre} | {emotion} | {folder} |".format(
                title=row["title"],
                status=row["status"],
                files=row["file_count"],
                genre=truncate_line(str(row["genre"]), 80),
                emotion=truncate_line(str(row["emotion"]), 80),
                folder=display_path(Path(row["folder"])),
            )
        )
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return f"""# All Prompt Overview

Input-based generated prompt overview. Deleted or missing input files are intentionally ignored.

```text
Input songs: {len(rows)}
Passed: {pass_count}
Check needed: {len(rows) - pass_count}
```

| Song | Status | Prompt files | Genre | Emotion | Output folder |
| --- | --- | ---: | --- | --- | --- |
{chr(10).join(table_rows)}
"""


def build_prompt_audit(rows: list[dict[str, object]]) -> str:
    lines = ["# Prompt Audit", "", "Input-based audit for generated prompt folders.", ""]
    issues_found = False
    for row in rows:
        errors = row["errors"]
        if not errors:
            continue
        issues_found = True
        lines.append(f"## {row['title']}")
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    if not issues_found:
        lines.append("No validation issues found.")
        lines.append("")
    lines.append("## Audit Scope")
    lines.append("")
    lines.append("- Missing generated prompt files")
    lines.append("- Fixed identity lock in prompt files")
    lines.append("- Reference folder/path usage")
    lines.append("- Placeholder residue")
    lines.append("- Previous-term residue when provided")
    return "\n".join(lines) + "\n"


def summarize_prompt_outputs(
    input_dir: Path,
    output_dir: Path,
    previous_terms: list[str] | None = None,
) -> tuple[list[dict[str, object]], list[Path]]:
    files = input_text_files(input_dir)
    rows: list[dict[str, object]] = []
    written: list[Path] = []
    for input_file in files:
        try:
            song = parse_song(input_file, title_fallback=input_file.stem)
            folder = output_dir / song_slug(song.title)
            errors = validate_song_folder(folder, previous_terms or [])
            if folder.exists():
                written.append(write_song_prompt_overview(song, folder, errors))
            reports = prompt_reports(folder) if folder.exists() else []
            rows.append(
                {
                    "title": song.title,
                    "status": status_text(errors),
                    "file_count": sum(1 for report in reports if report["exists"]),
                    "genre": song.genre,
                    "emotion": song.emotion,
                    "folder": folder,
                    "errors": errors,
                }
            )
        except Exception as exc:
            rows.append(
                {
                    "title": input_file.stem,
                    "status": "CHECK",
                    "file_count": 0,
                    "genre": "",
                    "emotion": "",
                    "folder": output_dir / input_file.stem,
                    "errors": [str(exc)],
                }
            )
    write_text(output_dir / ALL_OVERVIEW_FILE, build_all_prompt_overview(rows))
    write_text(output_dir / PROMPT_AUDIT_FILE, build_prompt_audit(rows))
    written.extend([output_dir / ALL_OVERVIEW_FILE, output_dir / PROMPT_AUDIT_FILE])
    return rows, written


def validate_song_folder(
    folder: Path,
    previous_terms: list[str] | None = None,
    reference_dir: Path = REFERENCE_DIR,
) -> list[str]:
    errors: list[str] = []
    if not folder.exists():
        return [f"폴더가 없습니다: {folder}"]
    try:
        ensure_reference_folder(reference_dir)
    except Exception as exc:
        errors.append(str(exc))
    for file_name in [*PROMPT_FILES, "README.md"]:
        path = folder / file_name
        if not path.exists():
            errors.append(f"누락 파일: {path}")
            continue
        text = read_text(path)
        if "[REFERENCE_DIR]" in text:
            errors.append(f"기준 이미지 placeholder가 남아 있음: {path.name}")
        if file_name in PROMPT_FILES:
            if not has_identity_lock(text):
                errors.append(f"캐릭터/세계관 고정 문장 부족: {path.name}")
        placeholders = re.findall(_PLACEHOLDER_PATTERN, text)
        if placeholders:
            errors.append(f"placeholder 잔여: {path.name} -> {', '.join(sorted(set(placeholders)))}")
        for term in previous_terms or []:
            if term and term in text:
                errors.append(f"이전 곡 정보 잔여 가능성: {path.name} -> {term}")
        lowered = text.lower()
        for term in POLICY_RISK_TERMS:
            if term in lowered:
                errors.append(f"정책 위험 표현 잔여: {path.name} -> {term}")
    return errors


def has_identity_lock(text: str) -> bool:
    lock_terms = [
        "AI Boy/AI Girl",
        "chibi toy robot figure",
        "screen-face",
        "Do not redesign",
        "Do not change",
        "Keep the same",
        "character consistency",
        "fixed base character",
    ]
    return any(term in text for term in lock_terms)


def command_create(args: argparse.Namespace) -> int:
    song = parse_song(Path(args.input), args.title, title_fallback=Path(args.input).stem)
    destination = create_song_folder(
        song=song,
        template_dir=Path(args.template_dir),
        output_dir=Path(args.output_dir),
        force=args.force,
    )
    errors = validate_song_folder(destination, args.previous_term or [])
    write_song_prompt_overview(song, destination, errors)
    print(f"생성 완료: {destination}")
    if errors:
        print("검증 실패:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("검증 통과")
    return 0


def input_text_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"입력 폴더가 없습니다: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"입력 경로가 폴더가 아닙니다: {input_dir}")
    return sorted(path for path in input_dir.glob("*.txt") if path.is_file())


def command_create_all(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir)
    files = input_text_files(input_dir)
    if not files:
        print(f"처리할 txt 파일이 없습니다: {input_dir}")
        return 1

    print(f"입력 파일 {len(files)}개 처리 시작: {input_dir}")
    failed: list[tuple[Path, str]] = []
    for index, input_file in enumerate(files, start=1):
        print(f"\n[{index}/{len(files)}] {input_file.name}")
        try:
            song = parse_song(input_file, title_fallback=input_file.stem)
            destination = create_song_folder(
                song=song,
                template_dir=Path(args.template_dir),
                output_dir=Path(args.output_dir),
                force=args.force,
            )
            errors = validate_song_folder(destination, args.previous_term or [])
            write_song_prompt_overview(song, destination, errors)
            print(f"생성 완료: {destination}")
            if errors:
                print("검증 실패:")
                for error in errors:
                    print(f"- {error}")
                failed.append((input_file, "검증 실패"))
            else:
                print("검증 통과")
        except Exception as exc:
            print(f"오류: {exc}")
            failed.append((input_file, str(exc)))

    summarize_prompt_outputs(input_dir, Path(args.output_dir), args.previous_term or [])
    print(f"\n처리 완료: 성공 {len(files) - len(failed)}개, 실패 {len(failed)}개")
    if failed:
        print("실패 목록:")
        for input_file, reason in failed:
            print(f"- {input_file.name}: {reason}")
        return 1
    return 0


def command_validate(args: argparse.Namespace) -> int:
    folder = Path(args.folder)
    errors = validate_song_folder(folder, args.previous_term or [])
    if errors:
        print("검증 실패:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("검증 통과")
    return 0


def command_summarize_all(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    rows, written = summarize_prompt_outputs(input_dir, output_dir, args.previous_term or [])
    failed = [row for row in rows if row["status"] != "PASS"]
    print(f"summary files written: {len(written)}")
    print(f"input songs: {len(rows)}")
    print(f"passed: {len(rows) - len(failed)}")
    print(f"check needed: {len(failed)}")
    if failed:
        print("check list:")
        for row in failed:
            print(f"- {row['title']}: {display_path(Path(row['folder']))}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="고정 밴드 이미지/영상 프롬프트 생성기")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="입력 txt로 곡별 프롬프트 폴더 생성")
    create.add_argument("--input", required=True, help="곡 정보와 가사가 들어 있는 txt 파일")
    create.add_argument("--title", help="곡 제목. 입력 txt에 제목이 없을 때 사용")
    create.add_argument("--template-dir", default=str(DEFAULT_TEMPLATE_DIR), help="공통 템플릿 폴더")
    create.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="곡별 폴더를 생성할 위치")
    create.add_argument("--previous-term", action="append", help="남아 있으면 안 되는 이전 곡 키워드")
    create.add_argument("--force", action="store_true", help="기존 곡 폴더를 삭제하고 다시 생성")
    create.set_defaults(func=command_create)

    create_all = subparsers.add_parser("create-all", help="input 폴더의 모든 txt로 곡별 프롬프트 폴더 생성")
    create_all.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR), help="곡 정보 txt 파일들이 들어 있는 폴더")
    create_all.add_argument("--template-dir", default=str(DEFAULT_TEMPLATE_DIR), help="공통 템플릿 폴더")
    create_all.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="곡별 폴더를 생성할 위치")
    create_all.add_argument("--previous-term", action="append", help="남아 있으면 안 되는 이전 곡 키워드")
    create_all.add_argument("--force", action="store_true", help="기존 곡 폴더를 삭제하고 다시 생성")
    create_all.set_defaults(func=command_create_all)

    validate = subparsers.add_parser("validate", help="생성된 곡별 프롬프트 폴더 검증")
    validate.add_argument("--folder", required=True, help="검증할 곡별 폴더")
    validate.add_argument("--previous-term", action="append", help="남아 있으면 안 되는 이전 곡 키워드")
    validate.set_defaults(func=command_validate)
    summarize_all = subparsers.add_parser("summarize-all", help="input 기준으로 output 프롬프트 설명 파일 생성")
    summarize_all.add_argument("--input-dir", default=str(DEFAULT_INPUT_DIR), help="기준 input txt 폴더")
    summarize_all.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="생성된 output 폴더")
    summarize_all.add_argument("--previous-term", action="append", help="남아 있으면 안 되는 이전 곡 키워드")
    summarize_all.set_defaults(func=command_summarize_all)
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_output_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
