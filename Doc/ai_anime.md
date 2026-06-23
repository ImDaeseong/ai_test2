# 설계 문서 — ai_anime

> 애니메이션 MV 이미지·영상 프롬프트 자동 생성 파이프라인
> 외부 AI API 없음. 순수 Python 표준 라이브러리만 사용.

---

## 1. 목적과 범위

Suno에서 내보낸 곡 정보 txt 파일 하나를 입력받아, 애니메이션 뮤직비디오 제작에 필요한 5종 파일을 자동 생성한다.

**입력**: `input/{곡 제목}.txt`
**출력**: `output/{곡 제목}/` 아래 5개 파일

| 파일 | 용도 |
|---|---|
| `00_character_sheet.md` | 캐릭터 턴어라운드 시트 (6개 이미지 플랫폼) |
| `01_image_prompts.md` | 씬 이미지 프롬프트 (씬 수 × 6 플랫폼) |
| `02_video_prompts.md` | Kling 영상 클립 프롬프트 + CapCut 편집 맵 |
| `03_production_guide.md` | 메타데이터 + 제작 워크플로우 |
| `README.md` | 곡별 편집 순서 가이드 |

---

## 2. 아키텍처

```
main.py (CLI)
├── create / create-all    프롬프트 생성 파이프라인
│   ├── parse_song()           txt 파일 파싱 → Song 데이터클래스
│   ├── load_profiles()        anime_profiles.json 로드
│   ├── build_visual_identity()  장르 프로파일 매칭 → VisualIdentity 데이터클래스
│   ├── adapt_template()       템플릿 파일 + 플레이스홀더 치환 + safety_filter
│   │   ├── _build_scene_image_blocks()  씬 × 6플랫폼 이미지 블록 생성
│   │   └── _build_scene_video_blocks()  씬 × CapCut 맵 기준 영상 블록 생성
│   └── create_song_folder()   5개 파일 output/ 에 저장
├── validate               output/ 전체 검증
└── export-draft           CapCut 드래프트 자동 생성 (2026-06-08 추가)
    ├── _parse_lrc_for_export()   LRC 섹션 타임스탬프 파싱
    ├── _normalize_lrc_timestamps()  Suno 압축 타임스탬프 스케일링
    ├── _anime_build_timeline()   섹션 × _required_variants() → timeline dict
    └── capcut_draft.py           CapCut 8.x 드래프트 JSON 생성

capcut_draft.py  (ai_img_video_prompt_capcut에서 복사)
└── build_draft() + write_draft() → CapCut 드래프트 폴더에 직접 쓰기
```

### 핵심 데이터클래스

```python
@dataclass
class Song:
    title: str
    genre: str
    bpm: str
    mood: str
    sections: list          # [SongSection(label, lines), ...]
    raw_text: str

@dataclass
class VisualIdentity:
    profile_key: str        # 장르 프로파일 키
    character: str          # 주인공 설명
    color_main: str
    environments: list      # 10개 배경 (씬별 순서 매핑)
    camera_shots: list      # 10개 카메라 앵글
    motion_language: list   # 씬별 모션 지시어
    avoid: list             # 이 장르에서 피해야 할 표현
    ...
```

---

## 3. 데이터 흐름

```
txt 파일
  └→ parse_song()
       ├→ _strip_noise()      BOM·빈줄 제거
       ├→ _parse_kv()         "Key: Value" 라인 파싱
       ├→ _parse_sections()   [Intro] [Verse] 등 섹션 블록 파싱
       └→ _infer_title()      제목 추론 (명시 없을 때 파일명 사용)

Song
  └→ build_visual_identity()
       ├→ _match_profile_key()  장르 키워드 점수 매핑 (최다 매칭 프로파일 선택)
       ├→ _infer_lighting()     장르에서 조명 스타일 추론
       └→ _infer_gender()       장르/가사에서 주인공 성별 추론

VisualIdentity + Song
  └→ adapt_template(template_text)
       ├→ [SONG_TITLE] 등 단순 치환
       ├→ [SCENE_IMAGE_BLOCKS] → _build_scene_image_blocks()
       │    └→ _scene_image_block() × N씬 × 6플랫폼
       ├→ [SCENE_VIDEO_BLOCKS] → _build_scene_video_blocks()
       │    ├→ _required_variants(section)   CapCut 맵에서 필요 Variant 추출
       │    ├→ _scene_video_block() × N씬   필요 Variant만 생성
       │    └→ _build_capcut_map()           CapCut 편집 맵 생성
       └→ safety_filter()                   위험 표현 치환
```

---

## 4. 핵심 설계 결정

### 4-1. 장르 프로파일 매칭 (점수 기반)

각 프로파일(7개)에 키워드 집합이 정의되어 있고, 곡의 장르+분위기 텍스트에 매칭되는 키워드 수를 세어 최다 점수 프로파일을 선택한다.
동점 또는 미매칭 시 `electronic_synth_default`로 폴백.

```python
PROFILE_KEYWORDS = {
    "acoustic_ballad": ["ballad", "acoustic", "piano", "gentle", "slow", ...],
    "rock":            ["rock", "guitar", "metal", "punk", "distortion", ...],
    ...
}
```

**주의**: 새 장르 키워드 추가 시 다른 프로파일과 중복 키워드가 없는지 확인. 중복이 많으면 원하지 않는 프로파일이 선택될 수 있다.

### 4-2. CapCut 맵 기반 선택적 Variant 생성

`_SECTION_CAPCUT`이 섹션 유형별 필요 Variant를 정의한다. `_required_variants(section)` 함수가 중복 제거 후 반환.

```python
_SECTION_CAPCUT = {
    "intro":        ("A",            "8-10"),   # A만 생성
    "verse":        ("base → A",     "5-8"),    # base + A 생성
    "pre-chorus":   ("B",            "4-6"),    # B만 생성
    "chorus":       ("B → C → B → C","1-3"),   # B + C 생성 (중복 제거)
    "bridge":       ("A → B",        "5-7"),   # A + B 생성
    "outro":        ("A",            "8-10"),   # A만 생성
    ...
}
```

**효과**: "10년 후에도" (7섹션) 기준 28클립(7×4) → 11클립으로 축소.

### 4-3. 안전 필터 이중 구조

1. `SAFETY_BLOCKLIST` — 출력에 남아 있으면 validate가 실패함 (검출용)
2. `SAFETY_RISK_MAP` — 위험 표현을 안전 표현으로 치환 (정규식, 생성 시 적용)

`safety_filter()`가 두 번째를 처리하고, `validate` 명령이 첫 번째로 최종 검증한다.

**중요**: `"minor"`는 SAFETY_BLOCKLIST에 넣지 않는다 → "D minor", "minor key" 등 음악 용어 오탐 발생.

---

## 5. anime_profiles.json 스키마

```json
{
  "schema_version": 1,
  "profiles": {
    "acoustic_ballad": {
      "environments": ["...", ...],     // 10개 — 씬별 순서 매핑
      "camera_shots":  ["...", ...],    // 10개
      "section_intensities": [...],    // 10개
      "motion_language": [...],        // 씬별 모션 지시어
      "transition_language": "...",
      "narrative_direction": "...",
      "character_direction": "...",
      "avoid": ["...", ...]            // 이 장르에서 금지할 표현
    },
    ...
  }
}
```

**environments는 반드시 10개** — 씬 인덱스로 직접 접근하므로 부족하면 마지막 값이 반복됨.
**avoid 필드 필수** — VisualIdentity.avoid로 연결됨. 누락 시 KeyError.

---

## 6. 플레이스홀더 목록

| 플레이스홀더 | 치환값 |
|---|---|
| `[SONG_TITLE]` | song.title |
| `[GENRE]` | song.genre |
| `[BPM]` | song.bpm |
| `[TEMPO]` | slow / mid-tempo / up-tempo |
| `[MOOD]` | song.mood |
| `[SCENE_RANGE]` | 01–07 (씬 수 기준) |
| `[SCENE_COUNT]` | 7 (씬 수) |
| `[SCENE_IMAGE_BLOCKS]` | _build_scene_image_blocks() 전체 출력 |
| `[SCENE_VIDEO_BLOCKS]` | _build_scene_video_blocks() 전체 출력 |
| `[COLOR_MAIN]` | identity.color_main |
| `[LIGHTING_STYLE]` | identity.lighting_style |
| `[CHARACTER]` | identity.character |
| `[CHARACTER_PROP]` | identity.prop |
| `[NARRATIVE_DIRECTION]` | identity.narrative_direction |
| `[TRANSITION_LANGUAGE]` | identity.transition_language |

---

## 7. 알려진 버그 패턴

| 증상 | 원인 | 해결 |
|---|---|---|
| 제목이 "Genre: pop" 같은 메타데이터로 추론됨 | `_infer_title()`이 2단어 이상 라인을 제목 후보로 취급 | BPM 라인, %-포함 라인은 건너뜀. 그 외 이상 추론 시 txt에 `Song Title:` 명시 |
| rock 프로파일에 crowd/audience 표현 등장 | environments 직접 편집 실수 | anime_profiles.json 수정 후 `test_profiles_rock_no_crowd_in_environments` 실행 |
| `[SCENE_RANGE]` 미치환 | 템플릿 파일에서 다른 대괄호 패턴 사용 | 반드시 `[UPPER_SNAKE]` 형식 — 중괄호 `{}` 사용 불가 |
| 동일 곡 재생성 시 이전 내용 남음 | `force=False`가 기본값 | `create --force` 또는 `create-all --force` 사용 |
| _infer_title이 BPM 라인을 제목으로 반환 | 정규식 범위 문제 | `r"\b\d+\s*bpm\b"` 패턴이 BPM 라인을 필터링함. txt에 이상한 첫 줄 없는지 확인 |

---

## 8. 테스트 전략

```
tests_unit.py  →  77 passed (2026-06-23 기준)
```

| 테스트 그룹 | 대상 | 수량 |
|---|---|---|
| Song 데이터클래스 | 기본값, 필드 | 2 |
| parse_song | 파싱, 폴백, 섹션, genre_profile 필드 | 7 |
| load_profiles | JSON 스키마 | 5 |
| build_visual_identity | 프로파일 매칭, avoid, genre_profile 오버라이드 | 10 |
| SAFETY_BLOCKLIST | 금지어 포함 여부 | 3 |
| safety_filter | 치환 동작 | 6 |
| _unresolved_placeholders | 미치환 검출 | 3 |
| _DEFAULT_SECTIONS | 기본 섹션 구조 | 3 |
| _build_scene_image_blocks | 씬 수, 플랫폼 | 4 |
| _build_scene_video_blocks | 씬 수, Variant, 클립 수 | 5 |
| _required_variants | 섹션별 Variant | 7 |
| adapt_template | 치환, 안전화 | 4 |
| build_readme | 제목, 파일목록 | 3 |
| PROMPT_FILES | 파일 수, 이름 | 3 |
| templates 존재 | 파일 실재 여부 | 1 |
| anime_profiles.json | 스키마, crowd 없음, avoid | 5 |
| style_keywords | 프로파일 style_keywords 필드, 출력 포함 여부 | 2 |
| reference_image | identity 필드, 파일 실재, fallback, 출력 포함 | 4 |

**핵심 불변식**: `_build_scene_image_blocks` 출력에 미치환 플레이스홀더 없어야 함.

---

## 9. 신규 장르 추가 시 체크리스트

1. `anime_profiles.json`에 새 프로파일 키 추가
2. `environments`, `camera_shots`, `section_intensities` 각 10개 항목 확인
3. `motion_language`, `transition_language`, `narrative_direction`, `character_direction` 추가
4. `avoid` 필드 추가 (빈 리스트 `[]`라도 반드시)
5. `PROFILE_KEYWORDS` 딕셔너리에 키워드 집합 추가
6. `_IDENTITY_HINTS`에 색상·소품·실루엣 힌트 추가
7. `python -m pytest tests_unit.py -v` 전체 통과 확인
8. `python main.py create-all --force` → `python main.py validate`

---

## 10. 확장 시 주의사항

- **이미지 플랫폼 추가**: `_scene_image_block()` 안에 `### 플랫폼명` 섹션 추가. `_SAFETY_TAIL` 반드시 포함.
- **새 Variant(D 등) 추가**: `_VARIANT_META`에 등록, `_SECTION_CAPCUT` 값 업데이트, `_prompt()` 안에 케이스 추가.
- **섹션 유형 추가**: `_SECTION_CAPCUT`에 키-값 추가. 키는 소문자, 부분 매칭(`in lower`)으로 동작.
- **Windows stdout 문제**: `main.py` 상단의 `sys.stdout.reconfigure(encoding="utf-8")` 블록이 처리. `conftest.py`는 테스트 환경 전용.

---

## 11. CapCut Export 설계 (2026-06-08 추가)

### 입력 폴더 구조 (export-draft 전용)

```
ai_anime/input/{곡명}/        ← 기존 {곡명}.txt와 별개의 서브폴더
├── {곡명}.lrc                ← Suno LRC (섹션 타임스탬프)
└── clips/
    ├── scene_01_A.mp4        ← Intro → Variant A
    ├── scene_02_base.mp4     ← Verse 1 → base
    ├── scene_02_A.mp4        ← Verse 1 → A
    ├── scene_03_B.mp4        ← Pre-Chorus → B
    └── ...
```

기존 `input/{곡명}.txt`, `input/{곡명}.mp3`는 그대로 유지. 오디오는 서브폴더 → 플랫 경로 순서로 자동 탐색.

### 씬-클립 매핑 규칙

```
LRC 섹션 순서 → 씬 번호
  섹션 1 (Intro)     → scene_01_*.mp4
  섹션 2 (Verse 1)   → scene_02_*.mp4
  섹션 3 (Chorus)    → scene_03_*.mp4

_required_variants("Chorus") → ["B", "C"]
  → clip_key: "scene_03_b", "scene_03_c"
  → 파일명: scene_03_B.mp4, scene_03_C.mp4 (대소문자 무시)
```

### 실행

```powershell
python main.py export-draft --song "10년 후에도"
# CapCut 재시작 → 프로젝트 목록에서 '10년 후에도_MV' 확인
```

### 주의사항

- LRC 파싱 실패 시 `[Intro]`, `[Verse 1]` 형식의 섹션 마커가 LRC에 있는지 확인
- 오디오 파일 없으면 CapCut 드래프트 생성 불가 (종료 코드 1)
- CapCut 실행 중 `export-draft` 실행 시 충돌 가능 → 종료 후 실행 권장

---

*Last Updated: 2026-06-08*
