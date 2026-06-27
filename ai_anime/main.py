#!/usr/bin/env python3
"""
ai_anime — Anime MV Prompt Generator
Input : Suno txt (Title/Genre/BPM + lyrics sections) — same format as ai_img_video_prompt
Output: per-song unique anime character + scene image/video prompts (5 files)
No external API. Pure Python template pipeline.
"""
import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Windows 콘솔 UTF-8 출력
if sys.platform != "_test" and sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf_8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

ROOT = Path(__file__).parent
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
TEMPLATE_DIR = ROOT / "templates"
PROFILES_FILE = ROOT / "anime_profiles.json"
REFERENCE_DIR = ROOT / "reference"

# 장르 프로파일 → reference 이미지 매핑 (성별 중립 우선, idol_pop은 gender로 분기)
REFERENCE_IMAGE_MAP: dict[str, str] = {
    "acoustic_ballad":        "ballad.png",
    "electronic_synth_default": "electronic.png",
    "hip_hop_trap":           "hiphop.png",
    "idol_pop":               None,          # gender-dependent: idol_boy.png / idol_girl.png
    "jazz_soul":              "jazz.png",
    "rock":                   "rock.png",
    "telephone-signal-pop":   "telephone.png",
}

PROMPT_FILES = [
    "00_character_sheet.md",
    "01_image_prompts.md",
    "02_video_prompts.md",
    "03_production_guide.md",
]

# ─── Field aliases (Suno txt format) ─────────────────────────────────────────

FIELD_ALIASES = {
    "title": "title", "제목": "title", "song title": "title",
    "genre": "genre", "장르": "genre",
    "bpm": "bpm",
    "tempo": "tempo", "템포": "tempo",
    "mood": "mood", "분위기": "mood",
    "emotion": "emotion", "감정": "emotion",
    "weirdness": "weirdness",
    "style influence": "style_influence",
    "genre profile": "genre profile",
}

SECTION_PATTERN = re.compile(
    r"^\[(?P<label>"
    r"Intro|Verse(?:\s*\d+)?|Pre[- ]?Chorus|Chorus(?:\s*\d+)?|Post[- ]?Chorus|"
    r"Build|Bridge|Final\s+Chorus|Outro|Interlude|Instrumental|Drop|Hook|Solo|Breakdown"
    r")(?::\s*(?P<note>.*?))?\]$",
    re.IGNORECASE,
)

# ─── Safety ───────────────────────────────────────────────────────────────────

SAFETY_BLOCKLIST = [
    "gore", "graphic violence", "explicit", "nsfw", "nude", "naked",
    "blood", "weapon", "real person", "photorealistic portrait",
    "child", "underage",
]

SAFETY_RISK_MAP = {
    r"\bblood\w*": "energy glow",
    r"\bweapon\w*": "prop",
    r"\bknife\b": "prop",
    r"\bgun\b": "prop",
    r"\bgore\w*": "intense motion",
    r"\bnude\b": "bare shoulder",
    r"\bnaked\b": "bare shoulder",
    r"\bdead\b": "motionless",
    r"\bkill\w*": "overcome",
}

def safety_filter(text: str) -> str:
    # Protect [PLACEHOLDER] tokens from substitution, then restore after filtering
    ph_tokens = re.findall(r"\[[A-Z_]{3,}\]", text)
    escapes = {f"\x00PH{i}\x00": ph for i, ph in enumerate(ph_tokens)}
    for token, ph in escapes.items():
        text = text.replace(ph, token)
    for pattern, replacement in SAFETY_RISK_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    for token, ph in escapes.items():
        text = text.replace(token, ph)
    return text

# ─── Genre → anime profile keyword matching ───────────────────────────────────

PROFILE_KEYWORDS = {
    "acoustic_ballad": [
        "acoustic", "ballad", "piano", "folk", "guitar", "gentle", "soft vocal",
        "heartfelt", "intimate", "strings", "cello", "발라드", "어쿠스틱",
    ],
    "idol_pop": [
        "idol", "k-pop", "kpop", "dance pop", "catchy", "bubbly", "j-pop",
        "bright pop", "아이돌", "팝", "dance",
    ],
    "jazz_soul": [
        "jazz", "soul", "r&b", "neo-soul", "blues", "swing", "groove",
        "sax", "trumpet", "smooth",
    ],
    "hip_hop_trap": [
        "hip hop", "hip-hop", "trap", "rap", "hiphop", "flow", "hook", "drip",
    ],
    "rock": [
        "rock", "metal", "punk", "grunge", "electric guitar", "distort",
        "riff", "anthem", "hard rock",
    ],
    "electronic_synth_default": [
        "electronic", "synth", "edm", "electro", "techno", "house",
        "ambient", "future bass", "chillwave", "digital",
    ],
    "telephone-signal-pop": [
        "telephone", "signal", "pulse", "ajaeng",
    ],
    "dark_trap": [
        "dark industrial trap", "dark trap", "industrial rap", "aggressive trap", "hardcore trap",
    ],
    "trap_soul": [
        "trap soul", "alt r&b", "dark moody r&b", "dark r&b", "dark rhythm",
    ],
}

# ─── Genre → visual identity hints ───────────────────────────────────────────

_IDENTITY_HINTS = {
    "acoustic_ballad": {
        "silhouette": "round chibi robot figure in cozy knit layers, seated calm posture, compact toy proportions",
        "hair": "smooth round robot helmet with soft cream tones and small musical note antenna accent",
        "outfit": "cream knit sweater vest over soft pastel shirt, gentle scarf wrap, cozy layered toy-figure styling",
        "prop": "a small glowing candle or folded handwritten sheet music held gently",
        "color_main": "warm rose cream",
        "color_base": "soft cream and warm ivory with gentle candlelight amber glow",
        "motif": "candle flame or delicate musical notes dissolving in warm soft light",
        "character_direction": "AI Boy/AI Girl 3D chibi toy robot figure in cozy ballad-genre knit outfit, warm candlelit scene",
    },
    "idol_pop": {
        "silhouette": "upright chibi robot figure in coordinated idol stage outfit, energetic ready-pose, toy figure proportions",
        "hair": "round robot helmet with glittery star sticker decoration and stage-ribbon accent",
        "outfit": "coordinated idol stage suit with metallic trim and bold accessories, performance-ready toy styling",
        "prop": "a glowing light stick or holographic idol card held raised at height",
        "color_main": "vivid mint and electric pink",
        "color_base": "clean white stage with soft pastel purple gradient",
        "motif": "star burst or heart cluster radiating from a performance gesture",
        "character_direction": "AI Boy/AI Girl 3D chibi toy robot figure in K-pop idol stage outfit, bright concert staging",
    },
    "jazz_soul": {
        "silhouette": "relaxed chibi robot figure in vintage layered outfit, casual side-lean, rounded toy proportions",
        "hair": "round robot helmet topped with a soft felt fedora hat in warm brown tone",
        "outfit": "warm vintage patterned coat with textured collar detail, carrying a miniature saxophone",
        "prop": "a miniature saxophone or vintage trumpet resting casually at side",
        "color_main": "warm amber gold",
        "color_base": "dark walnut wood and warm shadow bar atmosphere",
        "motif": "golden music notes or soft smoke rings drifting in warm amber lamplight",
        "character_direction": "AI Boy/AI Girl 3D chibi toy robot figure in vintage jazz fedora-and-coat outfit, warm bar light staging",
    },
    "hip_hop_trap": {
        "silhouette": "grounded wide-stance chibi robot figure in bold streetwear, cool confident lean, solid toy proportions",
        "hair": "round robot helmet with oversized snapback cap tilted sideways",
        "outfit": "oversized dark jacket with logo graphic, gold chain accessory, matching streetwear toy-figure styling",
        "prop": "a wireless mic or boombox held with casual confidence",
        "color_main": "neon pink and gold chain accent",
        "color_base": "dark urban concrete and graffiti-lit neon background",
        "motif": "spray paint burst or neon tag spreading across pavement cracks",
        "character_direction": "AI Boy/AI Girl 3D chibi toy robot figure in street hip-hop cap-and-chain outfit, urban graffiti staging",
    },
    "rock": {
        "silhouette": "energetic chibi robot figure in leather stage outfit, guitar-ready pose, bold toy proportions",
        "hair": "round robot helmet with lightning bolt sticker and star patch decoration",
        "outfit": "dark leather jacket with star patches and studs, instrument strap detail, rock stage toy styling",
        "prop": "a tiny electric guitar or microphone stand held in performance stance",
        "color_main": "hot pink and electric teal",
        "color_base": "dark stage with dramatic spotlight contrast",
        "motif": "lightning bolt or shattered star exploding from the stage impact point",
        "character_direction": "AI Boy/AI Girl 3D chibi toy robot figure in rock concert leather-and-stars outfit, stage performance staging",
    },
    "electronic_synth_default": {
        "silhouette": "sleek upright chibi robot figure in neon-trimmed dark outfit, focused DJ stance, toy proportions",
        "hair": "round robot helmet with neon light strip accent and signal wave display on visor surface",
        "outfit": "dark jacket with neon edge lighting, LED goggle visor accessory, electronic badge patch",
        "prop": "a miniature DJ controller or neon-lit headphones slung over the shoulder",
        "color_main": "neon cyan and electric purple",
        "color_base": "deep dark club atmosphere with neon glow grid",
        "motif": "EQ waveform or neon pulse spreading across a dark signal surface",
        "character_direction": "AI Boy/AI Girl 3D chibi toy robot figure in neon electronic DJ outfit, club staging",
    },
    "telephone-signal-pop": {
        "silhouette": "soft chibi robot figure in signal-decorated space suit, gentle dreamy lean, toy proportions",
        "hair": "round robot helmet with small signal tower antenna and heart display on visor",
        "outfit": "pastel space suit with wifi-signal patches, soft scarf accent, heart badge and antenna accessory",
        "prop": "a signal cable bracelet or retro telephone handset glowing softly",
        "color_main": "soft pink and neon violet",
        "color_base": "night city with signal tower glow and pink-purple sky",
        "motif": "signal wave or heartbeat line pulsing gently through the night sky",
        "character_direction": "AI Boy/AI Girl 3D chibi toy robot figure in signal-pop space suit, neon city night staging",
    },
    "dark_trap": {
        "silhouette": "grounded wide-stance chibi robot figure in all-black streetwear, cold aggressive lean, solid toy proportions",
        "hair": "round robot helmet with minimal silver detail and cold steel visor",
        "outfit": "all-black oversized jacket with minimal silver chain, dark cargo pants, cold urban toy-figure styling",
        "prop": "a wireless mic gripped tightly at low angle or cold steel boombox",
        "color_main": "cold steel grey and deep crimson red",
        "color_base": "dark industrial concrete under harsh single spotlight",
        "motif": "cracked concrete texture or cold red strobe pulse spreading across dark pavement",
        "character_direction": "AI Boy/AI Girl 3D chibi toy robot figure in dark industrial trap all-black outfit, cold concrete stage staging",
    },
    "trap_soul": {
        "silhouette": "relaxed chibi robot figure in dark muted jacket, slow emotional lean, soft toy proportions",
        "hair": "round robot helmet with subtle indigo glow ring and muted display",
        "outfit": "oversized dark muted jacket with subtle gold trim, dark relaxed pants, moody late-night toy-figure styling",
        "prop": "a wireless mic held low or a small glowing cassette tape resting at side",
        "color_main": "deep indigo and muted gold",
        "color_base": "dark indigo late-night atmosphere with soft amber pool",
        "motif": "slow indigo pulse or faint gold note dissolving in cold shadow",
        "character_direction": "AI Boy/AI Girl 3D chibi toy robot figure in dark moody trap-soul outfit, late-night shadow staging",
    },
}

_LIGHTING_RULES = [
    (["ballad", "acoustic", "tender", "heartfelt", "soft", "piano"],
     "warm candlelight glow with soft window rim light and gentle shadow depth"),
    (["jazz", "soul", "r&b", "groove", "late night"],
     "low warm practical lamp clusters with deep amber pools and quiet shadow edges"),
    (["idol", "bright pop", "catchy", "dance"],
     "clean bright stage lighting with soft pastel bloom and crisp fill light"),
    (["hip hop", "trap", "rap", "street"],
     "strong side-key with graphic shadow and one vivid accent color overhead"),
    (["rock", "metal", "punk", "distort"],
     "hard contrast side lighting with silver rim and near-black shadow"),
    (["electronic", "synth", "ambient", "edm"],
     "cool signal-blue glow with luminous depth haze and long fade-in rim"),
]

_DEFAULT_LIGHTING = "cinematic ambient glow with soft rim light and mid-tone shadow balance"

_DEFAULT_SECTIONS = [
    "Intro", "Verse 1", "Pre-Chorus", "Chorus", "Verse 2",
    "Bridge", "Final Chorus", "Outro",
]

# CapCut 편집 맵 — 섹션 유형별 권장 Variant + 클립 지속 시간
_SECTION_CAPCUT = {
    "intro":        ("A",                  "8-10"),
    "verse":        ("base → A",           "5-8"),
    "pre-chorus":   ("B",                  "4-6"),
    "pre chorus":   ("B",                  "4-6"),
    "final chorus": ("C → B → C → B → C", "1-3"),
    "chorus":       ("B → C → B → C",     "1-3"),
    "post-chorus":  ("C",                  "3-5"),
    "post chorus":  ("C",                  "3-5"),
    "bridge":       ("A → B",              "5-7"),
    "outro":        ("A",                  "8-10"),
    "hook":         ("C",                  "2-4"),
    "solo":         ("A → B",              "5-8"),
    "interlude":    ("A",                  "6-8"),
    "breakdown":    ("A → B",              "4-6"),
    "drop":         ("C",                  "2-4"),
    "build":        ("A → B",              "4-6"),
    "instrumental": ("A → B",              "5-8"),
}

_VARIANT_META = {
    "base": "Kling AI — Base",
    "A":    "Variant A — Quiet Presence",
    "B":    "Variant B — Emotional Arc",
    "C":    "Variant C — Peak Moment",
}

_SAFETY_TAIL = (
    "3D chibi toy robot figure, AI Boy/AI Girl collectible toy aesthetic, "
    "cute screen-face robot with round helmet, non-photorealistic 3D toy rendering, "
    "never realistic human anatomy, never live-action realism. "
    "No text, no watermark, no live action. "
    "Safe music-video performance scene with concert-only props, "
    "decorative costume details, non-violent staging, no realistic harm imagery."
)

_NO_TEXT_NOTE = (
    "Do not add any text, letters, numbers, watermarks, logos, "
    "or UI overlays to the image."
)

# ─── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class Section:
    label: str
    note: str
    lines: list = field(default_factory=list)


@dataclass
class Song:
    title: str
    genre: str
    bpm: str
    mood: str
    genre_profile: str = ""
    sections: list = field(default_factory=list)
    raw_text: str = ""


@dataclass
class VisualIdentity:
    profile_key: str
    genre_world: str
    character: str
    silhouette: str
    hair: str
    outfit: str
    prop: str
    color_main: str
    color_base: str
    color_rule: str
    song_motif: str
    style_keywords: str
    reference_image: str
    lighting_style: str
    narrative_direction: str
    character_direction: str
    transition_language: str
    environments: list = field(default_factory=list)
    camera_shots: list = field(default_factory=list)
    section_intensities: list = field(default_factory=list)
    motion_language: list = field(default_factory=list)
    avoid: list = field(default_factory=list)


# ─── Parsing ──────────────────────────────────────────────────────────────────

def _normalize_key(key: str):
    cleaned = re.sub(r"\s+", " ", key.strip().lstrip("﻿").lower())
    return FIELD_ALIASES.get(cleaned)


def _strip_noise(text: str) -> list:
    lines = []
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if re.fullmatch(r"\d+[dhms,\s]+ago", stripped, re.IGNORECASE):
            continue
        lines.append(line)
    return lines


def _parse_kv(line: str):
    if ":" not in line:
        return None
    key, _, value = line.partition(":")
    normalized = _normalize_key(key)
    if not normalized:
        return None
    return normalized, value.strip()


def _is_inline_note(line: str) -> bool:
    stripped = line.strip()
    if not (stripped.startswith("[") and stripped.endswith("]")):
        return False
    return SECTION_PATTERN.match(stripped) is None


def _normalize_section_label(label: str) -> str:
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
    return " ".join(w.capitalize() for w in words)


def _parse_sections(lines: list) -> list:
    sections = []
    current = None
    for raw_line in lines:
        line = raw_line.strip()
        m = SECTION_PATTERN.match(line)
        if m:
            if current:
                sections.append(current)
            current = Section(
                label=_normalize_section_label(m.group("label")),
                note=(m.group("note") or "").strip(),
            )
            continue
        if current is not None and not _is_inline_note(raw_line):
            current.lines.append(raw_line.rstrip())
    if current:
        sections.append(current)
    return sections


def _infer_title(lines: list, fields: dict, fallback: str) -> str:
    if fields.get("title"):
        return fields["title"].strip()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("["):
            break
        lower = stripped.lower()
        if lower.startswith(("weirdness", "style influence")):
            continue
        if "%" in stripped or re.search(r"\b\d+\s*bpm\b", stripped, re.IGNORECASE):
            continue
        if i < 8 and stripped and "," not in stripped and len(stripped) <= 40:
            if re.search(r"[가-힣]", stripped) or len(stripped.split()) > 1:
                return stripped
    return fallback


def _bpm_from_text(text: str) -> str:
    m = re.search(r"\b(\d{2,3})\s*bpm\b", text, re.IGNORECASE)
    return f"{m.group(1)} BPM" if m else ""


def parse_song(path: Path) -> Song:
    raw = path.read_text(encoding="utf-8-sig")
    lines = _strip_noise(raw)
    fields: dict = {}
    for line in lines:
        parsed = _parse_kv(line.strip())
        if parsed:
            key, value = parsed
            fields[key] = value
    title = _infer_title(lines, fields, fallback=path.stem)
    bpm = fields.get("bpm") or _bpm_from_text(fields.get("genre", "") + " " + raw)
    mood = fields.get("mood") or fields.get("emotion") or ""
    genre_profile = fields.get("genre profile", "")
    return Song(
        title=title,
        genre=fields.get("genre", ""),
        bpm=bpm,
        mood=mood,
        genre_profile=genre_profile,
        sections=_parse_sections(lines),
        raw_text="\n".join(lines),
    )


# ─── Profile matching & visual identity ───────────────────────────────────────

def load_profiles() -> dict:
    with PROFILES_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def _match_profile_key(lower: str) -> Optional[str]:
    best_key = None
    best_score = 0
    for key, keywords in PROFILE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in lower)
        if score > best_score:
            best_score = score
            best_key = key
    return best_key


def _infer_lighting(lower: str) -> str:
    for keywords, lighting in _LIGHTING_RULES:
        if any(kw in lower for kw in keywords):
            return lighting
    return _DEFAULT_LIGHTING


def _infer_gender(lower: str) -> str:
    if any(kw in lower for kw in ["female vocal", "여성", "girl", "여자"]):
        return "female-presenting"
    if any(kw in lower for kw in ["male vocal", "남성", "남자", "male tenor", "male solo"]):
        return "male-presenting"
    return "androgynous"


def build_visual_identity(song: Song, profiles: dict) -> VisualIdentity:
    lower = (song.genre + " " + song.mood + " " + song.raw_text).lower()
    available = ", ".join(profiles["profiles"].keys())

    if song.genre_profile:
        profile_key = song.genre_profile.strip()
        if profile_key not in profiles["profiles"]:
            raise ValueError(
                f"[{song.title}] 'Genre Profile: {profile_key}'가 anime_profiles.json에 없습니다.\n"
                f"사용 가능한 키: {available}"
            )
        _genre_matched = True
    else:
        profile_key = _match_profile_key(lower)
        if profile_key is None:
            profile_key = "electronic_synth_default"
            _genre_matched = False
        else:
            _genre_matched = True

    profile = profiles["profiles"].get(profile_key)
    if profile is None:
        available = ", ".join(profiles["profiles"].keys())
        raise ValueError(
            f"[{song.title}] 프로파일 키 '{profile_key}'가 anime_profiles.json에 없습니다.\n"
            f"사용 가능한 키: {available}"
        )
    hints = _IDENTITY_HINTS.get(profile_key)
    if hints is None:
        raise ValueError(
            f"[{song.title}] 프로파일 키 '{profile_key}'에 대한 _IDENTITY_HINTS가 없습니다.\n"
            f"main.py의 _IDENTITY_HINTS에 '{profile_key}' 항목을 추가하세요."
        )

    gender = _infer_gender(lower)
    color_main = hints["color_main"]
    color_base = hints["color_base"]
    color_rule = (
        f"limited-color anime palette: {color_main} as dominant accent, "
        f"{color_base}, subtle secondary glow, "
        f"this color identity belongs only to '{song.title}'"
    )

    style_keywords = profile.get("style_keywords", "3D chibi toy robot figure, collectible toy aesthetic")
    gender_label = "AI Girl" if gender == "female-presenting" else "AI Boy"
    character = (
        f"{gender_label} — AI Boy/AI Girl chibi robot toy figure, "
        f"screen-face display, round robot helmet, stubby chibi body, "
        f"{style_keywords}, "
        f"genre-specific outfit: {hints['outfit']}, "
        f"fixed base character design consistent across all scenes"
    )

    # reference 이미지 결정: 장르 매칭 실패 시 base.png, idol_pop은 gender 분기, 나머지는 MAP 조회
    if not _genre_matched:
        ref_filename = "base.png"
    elif profile_key == "idol_pop":
        ref_filename = "idol_girl.png" if gender == "female-presenting" else "idol_boy.png"
    else:
        ref_filename = REFERENCE_IMAGE_MAP.get(profile_key)
    if ref_filename is None or not (REFERENCE_DIR / ref_filename).exists():
        ref_filename = "base.png"
    reference_image = f"reference/{ref_filename}"

    environments = profile.get("environments", ["a cinematic anime scene"] * 10)
    camera_shots = profile.get("camera_shots", ["medium shot"] * 10)
    intensities = profile.get("section_intensities", ["medium"] * 10)

    if not (len(environments) == len(camera_shots) == len(intensities)):
        raise ValueError(
            f"[{profile_key}] 프로파일 배열 길이 불일치: "
            f"environments={len(environments)}, camera_shots={len(camera_shots)}, "
            f"section_intensities={len(intensities)} — 모두 같은 길이여야 합니다."
        )

    return VisualIdentity(
        profile_key=profile_key,
        genre_world=profile.get("genre_world", "dreamy atmospheric anime cinematic world"),
        character=character,
        silhouette=hints["silhouette"],
        hair=hints["hair"],
        outfit=hints["outfit"],
        prop=hints["prop"],
        color_main=color_main,
        color_base=color_base,
        color_rule=color_rule,
        song_motif=hints["motif"],
        style_keywords=style_keywords,
        reference_image=reference_image,
        lighting_style=_infer_lighting(lower),
        narrative_direction=profile.get("narrative_direction", ""),
        character_direction=hints["character_direction"],
        transition_language=profile.get("transition_language", "smooth match cuts"),
        environments=environments,
        camera_shots=camera_shots,
        section_intensities=intensities,
        motion_language=profile.get("motion_language", []),
        avoid=profile.get("avoid", []),
    )


# ─── Section list ─────────────────────────────────────────────────────────────

def _effective_sections(song: Song, identity: VisualIdentity) -> list:
    """Use parsed sections from txt if available, else fall back to profile list."""
    if song.sections:
        return [s.label for s in song.sections]
    return identity.environments and _DEFAULT_SECTIONS or _DEFAULT_SECTIONS


# ─── Scene block builders ─────────────────────────────────────────────────────

def _scene_image_block(idx: int, section: str, env: str, camera: str,
                        intensity: str, song: Song, identity: VisualIdentity) -> str:
    avoid_note = f" Avoid: {', '.join(identity.avoid)}." if identity.avoid else ""
    mj_no_extra = f", {', '.join(identity.avoid)}" if identity.avoid else ""

    identity_lock = (
        f"Character consistency: AI Boy/AI Girl fixed base design — screen-face robot display, "
        f"round robot helmet, chibi toy proportions, stubby arms and body. "
        f"{identity.color_main} remains dominant across all scenes. "
        f"Only the genre outfit changes: {identity.outfit}. "
        "Maintain identical base robot body and screen face in every scene."
    )
    common = (
        f"{camera} of {env}. "
        f"{identity.silhouette} in the scene. "
        f"{identity_lock} "
        f"{identity.lighting_style}. "
        f"Recurring motif: {identity.prop}. "
        f"{identity.genre_world}. "
        f"{identity.style_keywords}. "
        f"{identity.color_rule}. "
        f"{_SAFETY_TAIL}{avoid_note}"
    )
    flux_body = (
        f"{identity.character} moves in {env}, "
        f"keeping {identity.prop} close, intensity: {intensity}. "
        f"{identity.style_keywords}, 2D anime illustration. "
        f"No text, letters, numbers, watermarks, logos, or UI overlays.{avoid_note}"
    )
    return (
        f"## Scene {idx:02d} — {section}\n\n"
        f"### GPT Image (gpt-image-2 / OpenAI)\n"
        f"{common}\n\n{_NO_TEXT_NOTE}\n\n"
        f"**Model:** `gpt-image-2` | **Quality:** `high` | "
        f"**Size:** `1536x1024` (landscape) / `1024x1536` (portrait) / `1024x1024` (square)\n\n"
        f"### Google Gemini (Imagen 3)\n"
        f"{common}\n\n{_NO_TEXT_NOTE}\n\n"
        f"**비율:** `16:9` (가로형 MV 프레임) / `9:16` (세로형/숏폼)\n\n"
        f"### Midjourney v7\n"
        f"> **Character Reference:** `{identity.reference_image}` 업로드 후 `--cref` 사용\n\n"
        f"{common} "
        f"--v 7 --ar 16:9 --s 300 --cw 80 --no watermark, text, letters, numbers, logo, UI overlay, signature{mj_no_extra}\n\n"
        f"> Anime MV 씬은 Nijijourney (--niji 7) 권장. 씬 전체 일관성은 --oref 사용.\n\n"
        f"### Nijijourney (--niji 7)\n"
        f"> **Character Reference:** `{identity.reference_image}` 업로드 후 `--cref` 사용\n\n"
        f"{common} "
        f"--niji 7 --ar 16:9 --s 250 --cw 80 --no watermark, text, letters, numbers, logo, UI overlay, signature{mj_no_extra}\n\n"
        f"**주의:** 배경을 상세히 명시하지 않으면 최소 배경 생성됨 (Niji 7 특성)\n\n"
        f"### FLUX.1 (Black Forest Labs)\n"
        f"> **Character Reference:** `{identity.reference_image}` 를 img2img 또는 ControlNet reference로 업로드\n\n"
        f"{flux_body}\n\n"
        f"**규칙:** 자연어 문장만 사용. 가중치 문법(`(word:1.5)`) 사용 금지. 40-75단어 유지.\n\n"
        f"### Leonardo.Ai Phoenix 2.0\n"
        f"> **Character Reference:** `{identity.reference_image}` 를 Character Reference에 업로드\n\n"
        f"{common}\n\n{_NO_TEXT_NOTE}\n\n"
        f"**Model:** Phoenix 2.0 | **Alchemy:** `on` | **Guidance:** `7` | **Style preset:** `CINEMATIC`"
    )


def _required_variants(section: str) -> list:
    """Return unique ordered variants this section needs, per _SECTION_CAPCUT."""
    lower = section.lower()
    variants_str = "A → B"
    for key, (vstr, _) in _SECTION_CAPCUT.items():
        if key in lower:
            variants_str = vstr
            break
    seen: set = set()
    result: list = []
    for v in re.split(r"\s*→\s*", variants_str):
        v = v.strip()
        if v and v not in seen:
            seen.add(v)
            result.append(v)
    return result


def _scene_video_block(idx: int, section: str, env: str, camera: str,
                        motion: str, identity: VisualIdentity) -> str:
    required = _required_variants(section)

    def _prompt(variant: str) -> str:
        if variant == "base":
            return (
                f"Animate the uploaded scene image. "
                f"{camera} of {env}. "
                f"{identity.character}. {identity.prop} visible. "
                f"{identity.lighting_style}. {identity.song_motif}. {motion}. "
                f"{identity.style_keywords}. No text, no watermarks."
            )
        if variant == "A":
            return (
                f"Slow ambient camera drift, barely perceptible. {env}. "
                f"{identity.character} stands nearly still, {identity.prop} held close. "
                f"{identity.lighting_style}. Environmental motion only: leaves, mist, or light shift. "
                f"{identity.style_keywords}. No text, no watermarks."
            )
        if variant == "B":
            return (
                f"Gradual {camera} push-in. {env}. "
                f"{identity.character} shifts posture subtly. "
                f"{identity.lighting_style} brightens gently. {identity.song_motif} at frame edges. "
                f"{identity.style_keywords}. No text, no watermarks."
            )
        if variant == "C":
            return (
                f"Dynamic {camera}, motivated movement. {env}. "
                f"{identity.character} moves fully into the moment. "
                f"{identity.color_main} lighting peak. {identity.song_motif} surges across frame. "
                f"{identity.style_keywords}. No text, no watermarks."
            )
        return ""

    header = (
        f"## Scene {idx:02d} — {section}\n\n"
        f"Upload approved image from `01_image_prompts.md`. "
        f"Attach `00_character_sheet.md` as secondary reference."
    )
    parts = [header]
    for v in required:
        if v not in _VARIANT_META:
            continue
        sfx = "base" if v == "base" else v
        parts.append(
            f"\n\n### {_VARIANT_META[v]}\n\n"
            f"```text\n{_prompt(v)}\n```\n\n"
            f"**Save as:** `scene_{idx:02d}_{sfx}.mp4` | Duration: 5–8 sec"
        )
    return "".join(parts)


def _capcut_row(idx: int, section: str) -> str:
    lower = section.lower()
    variants, timing = "A → B", "5-8"
    for key, val in _SECTION_CAPCUT.items():
        if key in lower:
            variants, timing = val
            break
    clips = " → ".join(f"scene_{idx:02d}_{v.strip()}" for v in variants.split("→"))
    return f"{section:<14} ({timing}초): {clips}"


def _build_capcut_map(sections: list) -> str:
    rows = "\n".join(_capcut_row(i, s) for i, s in enumerate(sections, 1))
    return (
        "## CapCut Editing Map\n\n"
        "클립 파일 명칭: `scene_NN_base.mp4` / `scene_NN_A.mp4` / `scene_NN_B.mp4` / `scene_NN_C.mp4`\n\n"
        f"```text\n{rows}\n```\n\n"
        "컷 속도 가이드:\n\n"
        "```text\n"
        "Intro / Outro    : 클립당 8-10초  (분위기 설정)\n"
        "Verse            : 클립당 5-8초   (서사 진행)\n"
        "Pre-Chorus       : 클립당 4-6초   (긴장)\n"
        "Chorus (전체)     : 클립당 1-3초   (에너지 피크 — 빠른 컷)\n"
        "Bridge           : 클립당 5-7초   (감정 전환)\n"
        "```\n\n"
        "트랜지션:\n\n"
        "```text\n"
        "Chorus 진입     : 빠른 하드컷 (트랜지션 없음)\n"
        "섹션 간          : 디졸브 0.3-0.5초\n"
        "Outro 종료       : 페이드 아웃\n"
        "```"
    )


def _build_scene_image_blocks(song: Song, identity: VisualIdentity) -> str:
    sections = _effective_sections(song, identity)
    envs = identity.environments
    cameras = identity.camera_shots
    intensities = identity.section_intensities
    blocks = []
    for i, section in enumerate(sections, 1):
        env = envs[min(i - 1, len(envs) - 1)]
        camera = cameras[min(i - 1, len(cameras) - 1)]
        intensity = intensities[min(i - 1, len(intensities) - 1)]
        blocks.append(_scene_image_block(i, section, env, camera, intensity, song, identity))
    return "\n\n---\n\n".join(blocks)


def _build_scene_video_blocks(song: Song, identity: VisualIdentity) -> str:
    sections = _effective_sections(song, identity)
    n = len(sections)
    envs = identity.environments
    cameras = identity.camera_shots
    motions = identity.motion_language or ["smooth cinematic anime movement"]

    total_clips = sum(len(_required_variants(s)) for s in sections)
    production_rule = (
        f"## Kling Production Rule\n\n"
        f"```text\n"
        f"씬 1개 이미지 → CapCut 맵 기준 필요한 Variant만 생성\n"
        f"'{song.title}': {n}개 씬 → 실제 생성 클립 {total_clips}개\n"
        f"Chorus 반복 구간: 동일 클립 CapCut에서 재사용 (추가 생성 불필요)\n"
        f"```"
    )

    scene_blocks = []
    for i, section in enumerate(sections, 1):
        env = envs[min(i - 1, len(envs) - 1)]
        camera = cameras[min(i - 1, len(cameras) - 1)]
        motion = motions[min(i - 1, len(motions) - 1)]
        scene_blocks.append(_scene_video_block(i, section, env, camera, motion, identity))

    all_blocks = [production_rule] + scene_blocks + [_build_capcut_map(sections)]
    return "\n\n---\n\n".join(all_blocks)


# ─── Template filling ─────────────────────────────────────────────────────────

def _bpm_to_tempo(bpm: str) -> str:
    m = re.search(r"\b(\d+)\b", bpm)
    if not m:
        return "song-matched tempo"
    n = int(m.group(1))
    if n < 70:
        return "slow"
    if n < 90:
        return "slow to mid-tempo"
    if n < 110:
        return "mid-tempo"
    if n < 130:
        return "mid to up-tempo"
    return "up-tempo"


def adapt_template(text: str, song: Song, identity: VisualIdentity) -> str:
    scene_count = len(_effective_sections(song, identity))
    replacements = {
        "[SCENE_RANGE]": f"01–{scene_count:02d}",
        "[SCENE_COUNT]": str(scene_count),
        "[SONG_TITLE]": song.title,
        "[GENRE]": song.genre,
        "[BPM]": song.bpm,
        "[TEMPO]": _bpm_to_tempo(song.bpm),
        "[MOOD]": song.mood,
        "[EMOTION]": song.mood,
        "[STAGE_ENERGY]": identity.character_direction,
        "[GENRE_PROFILE]": identity.profile_key,
        "[SONG_MOTIF]": identity.song_motif,
        "[COLOR_RULE]": identity.color_rule,
        "[COLOR_MAIN]": identity.color_main,
        "[COLOR_BASE]": identity.color_base,
        "[LIGHTING_STYLE]": identity.lighting_style,
        "[CHARACTER]": identity.character,
        "[CHARACTER_SILHOUETTE]": identity.silhouette,
        "[CHARACTER_HAIR]": identity.hair,
        "[CHARACTER_OUTFIT]": identity.outfit,
        "[CHARACTER_PROP]": identity.prop,
        "[CHARACTER_DIRECTION]": identity.character_direction,
        "[CHARACTER_REFERENCE]": identity.reference_image,
        "[NARRATIVE_DIRECTION]": identity.narrative_direction,
        "[GENRE_WORLD]": identity.genre_world,
        "[TRANSITION_LANGUAGE]": identity.transition_language,
    }
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)

    if "[SCENE_IMAGE_BLOCKS]" in text:
        text = text.replace("[SCENE_IMAGE_BLOCKS]", _build_scene_image_blocks(song, identity))
    if "[SCENE_VIDEO_BLOCKS]" in text:
        text = text.replace("[SCENE_VIDEO_BLOCKS]", _build_scene_video_blocks(song, identity))

    return safety_filter(text)


def build_readme(song: Song, identity: VisualIdentity) -> str:
    sections = _effective_sections(song, identity)
    scene_count = len(sections)
    section_list = "\n".join(f"{i:02d}. {s}" for i, s in enumerate(sections, 1))

    edit_sections = []
    for i, s in enumerate(sections, 1):
        # Get lyrics lines for this section if parsed
        lyric_lines = ""
        if song.sections and i <= len(song.sections):
            raw_lines = [ln for ln in song.sections[i - 1].lines if ln.strip()]
            if raw_lines:
                lyric_lines = "\n".join(raw_lines[:4])
        env = identity.environments[min(i - 1, len(identity.environments) - 1)]
        camera = identity.camera_shots[min(i - 1, len(identity.camera_shots) - 1)]
        edit_sections.append(
            f"### {s}\n\n"
            + (f"```text\n{lyric_lines}\n```\n\n" if lyric_lines else "")
            + f"추천 컷:\n\n```text\nscene_{i:02d}\n```\n\n"
            f"연출:\n\n```text\n"
            f"카메라: {camera}\n"
            f"배경: {env}\n"
            f"조명: {identity.lighting_style}\n"
            f"에너지: {identity.character_direction}\n"
            f"캐릭터 정체성은 00_character_sheet.md 기준 이미지를 참조한다.\n"
            f"```"
        )

    return (
        f"# {song.title} — Anime MV 제작 순서\n\n"
        f"이 문서는 `{song.title}`을 기준으로 "
        f"캐릭터 시트를 먼저 만들고, 씬 이미지, 씬 영상 순서로 제작하는 가이드다.\n\n"
        f"## 0. 곡 방향\n\n"
        f"```text\n"
        f"제목: {song.title}\n"
        f"장르: {song.genre}\n"
        f"BPM: {song.bpm}\n"
        f"분위기: {song.mood}\n"
        f"장르 프로파일: {identity.profile_key}\n"
        f"색상 주조: {identity.color_main}\n"
        f"조명: {identity.lighting_style}\n"
        f"전환: {identity.transition_language}\n"
        f"```\n\n"
        f"## 1. 사용할 파일\n\n"
        f"```text\n"
        f"00_character_sheet.md   ← 먼저 생성. 이후 모든 씬에 참조 첨부\n"
        f"01_image_prompts.md     ← 씬 이미지 생성 ({scene_count}개 씬 × 6개 플랫폼)\n"
        f"02_video_prompts.md     ← 씬 영상 클립 ({scene_count}개 씬, 총 {sum(len(_required_variants(s)) for s in sections)}클립) + CapCut 편집 맵\n"
        f"03_production_guide.md  ← 메타데이터 + 제작 워크플로우\n"
        f"```\n\n"
        f"## 2. 씬 목록\n\n"
        f"```text\n{section_list}\n```\n\n"
        f"## 3. 이미지 생성 순서\n\n"
        f"```text\n"
        f"1. 00_character_sheet.md — 캐릭터 턴어라운드 모델 시트 생성 (8-뷰)\n"
        f"2. 01_image_prompts.md — 씬 순서대로 생성, 매번 모델 시트 참조 첨부\n"
        f"```\n\n"
        f"## 4. 가사 기준 편집 순서\n\n"
        + "\n\n".join(edit_sections)
        + f"\n\n## 5. Kling 영상 및 CapCut 편집\n\n"
        f"```text\n"
        f"1. 씬 이미지를 Kling AI에 업로드 (Image to Video)\n"
        f"2. 02_video_prompts.md — 씬별 CapCut 맵 기준 Variant 생성 (총 {sum(len(_required_variants(s)) for s in sections)}클립)\n"
        f"   저장명: scene_NN_A.mp4 / scene_NN_B.mp4 / scene_NN_C.mp4 (씬별 필요 Variant만)\n"
        f"3. 02_video_prompts.md 하단 CapCut Editing Map 참조\n"
        f"4. CapCut: MP3 붙이기 → 씬별 클립 배치 → 트랜지션 → Export\n"
        f"```\n\n"
        f"## 6. 최종 확인\n\n"
        f"```text\n"
        f"캐릭터 정체성이 모든 씬에서 동일한가? (00_character_sheet.md 기준)\n"
        f"씬마다 00_character_sheet.md를 Kling 생성 시 함께 첨부했는가?\n"
        f"곡 장르와 감정에 맞게 씬 연출이 바뀌었는가?\n"
        f"이전 곡의 캐릭터, 색상, 모티프가 남아 있지 않은가?\n"
        f"placeholder가 남아 있지 않은가?\n"
        f"```\n"
    )


# ─── Output ───────────────────────────────────────────────────────────────────

def _song_slug(title: str) -> str:
    forbidden = '<>:"/\\|?*'
    slug = "".join("_" if c in forbidden else c for c in title).strip().strip(".")
    return slug or "untitled"


def create_song_folder(song: Song, profiles: dict, force: bool = False) -> bool:
    slug = _song_slug(song.title)
    song_dir = OUTPUT_DIR / slug

    if song_dir.exists() and not force:
        print(f"  [SKIP] {slug} (이미 존재. --force 로 덮어쓰기)")
        return True

    song_dir.mkdir(parents=True, exist_ok=True)
    identity = build_visual_identity(song, profiles)

    for tmpl_name in PROMPT_FILES:
        tmpl_path = TEMPLATE_DIR / tmpl_name
        if not tmpl_path.exists():
            print(f"  [WARN] 템플릿 없음: {tmpl_name}")
            continue
        content = tmpl_path.read_text(encoding="utf-8")
        content = adapt_template(content, song, identity)
        (song_dir / tmpl_name).write_text(content, encoding="utf-8")

    readme = safety_filter(build_readme(song, identity))
    (song_dir / "README.md").write_text(readme, encoding="utf-8")

    print(f"  [OK] {slug} - {len(PROMPT_FILES) + 1}개 파일")
    return True


# ─── Validation ───────────────────────────────────────────────────────────────

def _unresolved_placeholders(text: str) -> list:
    return list(set(re.findall(r"\[([A-Z_]{3,})\]", text)))


def validate_song_folder(folder: Path) -> bool:
    ok = True
    expected = PROMPT_FILES + ["README.md"]
    for fname in expected:
        p = folder / fname
        if not p.exists():
            print(f"    [FAIL] 파일 없음: {fname}")
            ok = False
            continue
        content = p.read_text(encoding="utf-8")
        unresolved = _unresolved_placeholders(content)
        if unresolved:
            print(f"    [FAIL] 미치환 플레이스홀더 in {fname}: {unresolved}")
            ok = False
        for term in SAFETY_BLOCKLIST:
            if term.lower() in content.lower():
                print(f"    [FAIL] 안전 위반 '{term}' in {fname}")
                ok = False
    return ok


# ─── CLI ──────────────────────────────────────────────────────────────────────

def cmd_create(args):
    profiles = load_profiles()
    txt_files = sorted(INPUT_DIR.glob("*.txt"))
    if args.song:
        txt_files = [f for f in txt_files if args.song in f.stem]
    if not txt_files:
        print("input/ 에서 매칭되는 txt 파일 없음")
        return
    for txt in txt_files:
        print(f"생성 중: {txt.stem}")
        song = parse_song(txt)
        create_song_folder(song, profiles, force=args.force)


def cmd_create_all(args):
    profiles = load_profiles()
    txt_files = sorted(INPUT_DIR.glob("*.txt"))
    if not txt_files:
        print("input/ 에 txt 파일 없음")
        return
    for txt in txt_files:
        print(f"생성 중: {txt.stem}")
        song = parse_song(txt)
        create_song_folder(song, profiles, force=args.force)
    print(f"완료: {len(txt_files)}곡")


def cmd_validate():
    if not OUTPUT_DIR.exists():
        print("output/ 폴더 없음")
        return
    song_dirs = [d for d in sorted(OUTPUT_DIR.iterdir()) if d.is_dir()]
    if not song_dirs:
        print("검증할 output 폴더 없음")
        return
    all_ok = True
    for d in song_dirs:
        ok = validate_song_folder(d)
        print(f"  [{'PASS' if ok else 'FAIL'}] {d.name}")
        if not ok:
            all_ok = False
    if all_ok:
        print("전체 PASS")
    else:
        print("일부 FAIL")
        sys.exit(1)


# ─── CapCut Export ────────────────────────────────────────────────────────────

_LRC_LINE_RE = re.compile(r"\[(\d+):(\d+\.\d+)\](.*)")
_CAPCUT_SECTION_RE = re.compile(
    r"^(intro|verse|pre.?chorus|chorus|bridge|guitar\s*solo|solo|"
    r"outro|interlude|instrumental|breakdown|drop|hook|final\s*chorus)\s*\d*$",
    re.IGNORECASE,
)


def _get_audio_duration_ms(path: Path) -> Optional[int]:
    try:
        from mutagen import File as MFile
        audio = MFile(str(path))
        if audio and audio.info:
            return int(audio.info.length * 1000)
    except (ImportError, Exception):
        pass
    if path.suffix.lower() == ".wav":
        try:
            import wave
            with wave.open(str(path), "r") as wf:
                return int(wf.getnframes() / wf.getframerate() * 1000)
        except Exception:
            pass
    return None


def _find_audio_for_export(song_name: str) -> Optional[Path]:
    """input/{곡명}/ 서브폴더 → input/{곡명}.mp3 순서로 탐색"""
    sub = INPUT_DIR / song_name
    for ext in ("*.wav", "*.mp3", "*.m4a", "*.flac"):
        found = list(sub.glob(ext))
        if found:
            return found[0]
    for ext in (".wav", ".mp3", ".m4a", ".flac"):
        p = INPUT_DIR / f"{song_name}{ext}"
        if p.exists():
            return p
    return None


def _find_lrc_for_export(song_name: str) -> Optional[Path]:
    """input/{곡명}/ 서브폴더 → input/{곡명}.lrc 순서로 탐색"""
    sub = INPUT_DIR / song_name
    found = list(sub.glob("*.lrc"))
    if found:
        return found[0]
    p = INPUT_DIR / f"{song_name}.lrc"
    return p if p.exists() else None


def _scan_clips_for_export(song_name: str) -> dict:
    """input/{곡명}/clips/ → {정규화된_stem: 파일명}"""
    clips_dir = INPUT_DIR / song_name / "clips"
    if not clips_dir.exists():
        return {}
    result = {}
    for f in sorted(clips_dir.glob("*.mp4")):
        key = f.stem.lower().replace("-", "_").replace(" ", "_")
        result[key] = f.name
    return result


def _get_clip_durations_for_export(song_name: str) -> dict:
    clips_dir = INPUT_DIR / song_name / "clips"
    if not clips_dir.exists():
        return {}
    result = {}
    for f in sorted(clips_dir.glob("*.mp4")):
        key = f.stem.lower().replace("-", "_").replace(" ", "_")
        dur = _get_audio_duration_ms(f)
        if dur is not None:
            result[key] = dur
    return result


def _parse_lrc_for_export(lrc_path: Path) -> list:
    sections = []
    with open(lrc_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = _LRC_LINE_RE.match(line)
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
                name = inner.group(1).strip()
                if _CAPCUT_SECTION_RE.match(name):
                    sections.append({"name": name, "start_ms": ms})
    return sections


def _normalize_lrc_timestamps(sections: list, audio_ms: Optional[int]) -> list:
    if not sections:
        return sections
    last_start = sections[-1]["start_ms"]
    if audio_ms and last_start > 0 and (audio_ms / last_start) > 5:
        avg_dur = last_start / max(len(sections) - 1, 1)
        scale = audio_ms / (last_start + avg_dur)
        for s in sections:
            s["start_ms"] = int(s["start_ms"] * scale)
    for i, s in enumerate(sections):
        if i + 1 < len(sections):
            s["end_ms"] = sections[i + 1]["start_ms"]
        else:
            s["end_ms"] = audio_ms if audio_ms else s["start_ms"] + 30_000
    return sections


def _anime_build_timeline(song_title: str, sections: list, clips: dict, audio_ms: Optional[int]) -> dict:
    """LRC 섹션 × _required_variants() → capcut_draft.build_draft() 입력 timeline dict"""
    slot_list = []
    seen_ids: dict = {}
    for i, s in enumerate(sections, 1):
        variants = _required_variants(s["name"])
        duration_ms = s["end_ms"] - s["start_ms"]
        for variant in variants:
            clip_key = f"scene_{i:02d}_{variant.lower()}"
            clip_file = clips.get(clip_key)
            n = seen_ids.get(clip_key, 0)
            slot_id = clip_key if n == 0 else f"{clip_key}_{n + 1}"
            seen_ids[clip_key] = n + 1
            slot_list.append({
                "slot_id": slot_id,
                "section": s["name"],
                "capcut_key": s["name"].lower(),
                "shot_type": clip_key,
                "start_ms": s["start_ms"],
                "end_ms": s["end_ms"],
                "duration_ms": duration_ms,
                "clip_file": clip_file,
                "source": "assigned" if clip_file else "placeholder",
                "review_required": clip_file is None,
            })
    total_ms = audio_ms or (sections[-1]["end_ms"] if sections else 0)
    return {
        "schema_version": "1.2",
        "build_info": {
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "mode": "anime",
        },
        "song_title": song_title,
        "total_duration_ms": total_ms,
        "sections": [
            {"name": s["name"], "start_ms": s["start_ms"],
             "end_ms": s["end_ms"], "duration_ms": s["end_ms"] - s["start_ms"]}
            for s in sections
        ],
        "clips": slot_list,
    }


def cmd_export_draft(args):
    """LRC + clips/ → CapCut 드래프트 자동 생성"""
    try:
        from capcut_draft import CAPCUT_DRAFT_ROOT, build_draft, write_draft
    except ImportError:
        print("❌ capcut_draft.py 없음 — ai_anime/ 폴더에 capcut_draft.py 필요")
        sys.exit(1)

    song_name = args.song
    song_sub = INPUT_DIR / song_name

    if not song_sub.exists():
        print(f"❌ 폴더 없음: {song_sub}")
        print(f"   input/{song_name}/ 폴더에 LRC와 clips/ 폴더를 만드세요.")
        sys.exit(1)

    lrc = _find_lrc_for_export(song_name)
    if not lrc:
        print(f"❌ LRC 없음: input/{song_name}/*.lrc")
        sys.exit(1)

    audio = _find_audio_for_export(song_name)
    audio_ms = _get_audio_duration_ms(audio) if audio else None
    clips = _scan_clips_for_export(song_name)
    clip_durations = _get_clip_durations_for_export(song_name)

    sections = _parse_lrc_for_export(lrc)
    if not sections:
        print("❌ LRC 섹션 파싱 실패 — [Intro], [Verse 1] 형식의 섹션 마커 필요")
        sys.exit(1)

    sections = _normalize_lrc_timestamps(sections, audio_ms)
    timeline = _anime_build_timeline(song_name, sections, clips, audio_ms)

    assigned = sum(1 for c in timeline["clips"] if c["source"] == "assigned")
    total = len(timeline["clips"])

    print(f"\n[{song_name}] CapCut 드래프트 생성...")
    print(f"   섹션  : {len(sections)}개")
    print(f"   클립  : {total}개 슬롯 (할당 {assigned} / 플레이스홀더 {total - assigned})")
    if audio:
        print(f"   음원  : {audio.name}")
    else:
        print("   ⚠️  음원 없음 — CapCut에서 수동으로 추가 필요")

    if not CAPCUT_DRAFT_ROOT.exists():
        print(f"❌ CapCut 드래프트 폴더 없음: {CAPCUT_DRAFT_ROOT}")
        print("   CapCut이 설치되어 있는지 확인하세요.")
        sys.exit(1)

    if audio is None:
        print("❌ 음원 파일 없음 — CapCut 드래프트 생성에 음원이 필요합니다.")
        sys.exit(1)

    draft_content, draft_meta, draft_id = build_draft(
        timeline, audio, INPUT_DIR / song_name / "clips", clip_durations
    )
    folder = write_draft(draft_content, draft_meta, draft_id, CAPCUT_DRAFT_ROOT)

    print(f"\n✅ 드래프트 생성 완료")
    print(f"   위치  : {folder}")
    print(f"   이름  : {song_name}_MV")
    print(f"   영상  : {assigned}개 세그먼트")
    print(f"\n   CapCut 실행 → 프로젝트 목록에서 '{song_name}_MV' 확인")


def main():
    parser = argparse.ArgumentParser(description="ai_anime — Anime MV Prompt Generator")
    sub = parser.add_subparsers(dest="command")

    p_create = sub.add_parser("create", help="input/ 의 곡 프롬프트 생성")
    p_create.add_argument("--song", help="곡 이름 부분 문자열로 필터")
    p_create.add_argument("--force", action="store_true", help="기존 output 덮어쓰기")

    p_all = sub.add_parser("create-all", help="input/ 의 모든 곡 프롬프트 생성")
    p_all.add_argument("--force", action="store_true", help="기존 output 덮어쓰기")

    sub.add_parser("validate", help="output/ 전체 검증")

    p_export = sub.add_parser("export-draft", help="CapCut 드래프트 자동 생성")
    p_export.add_argument("--song", required=True, help="곡 이름 (input/{곡명}/ 폴더명과 일치)")

    args = parser.parse_args()
    if args.command == "create":
        cmd_create(args)
    elif args.command == "create-all":
        cmd_create_all(args)
    elif args.command == "validate":
        cmd_validate()
    elif args.command == "export-draft":
        cmd_export_draft(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
