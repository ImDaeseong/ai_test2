# ai_anime — Anime MV Prompt Generator

애니메이션 뮤직비디오 이미지·영상 프롬프트 자동 생성 파이프라인.
Suno txt 파일 하나로 캐릭터 시트·씬 이미지·Kling 영상 클립·CapCut 편집 맵·제작가이드 5개 파일을 자동 생성합니다.
외부 API 없음. 순수 Python 템플릿 치환 엔진.

---

## 출력 구조 (곡당 5파일)

```
output/{곡 제목}/
├── 00_character_sheet.md    # 캐릭터 턴어라운드 시트 — 6개 이미지 플랫폼
├── 01_image_prompts.md      # 씬 이미지 프롬프트 — 씬별 × 6플랫폼
├── 02_video_prompts.md      # Kling Variant A/B/C + CapCut Editing Map
├── 03_production_guide.md   # 제작 워크플로우 + 메타데이터
└── README.md                # 곡별 요약 + Kling/CapCut 편집 순서
```

## 이미지 플랫폼 (6종)
GPT Image (gpt-image-2) · Google Gemini (Imagen 3) · Midjourney v7 · Nijijourney (--niji 7) · FLUX.1 · Leonardo.Ai Phoenix 2.0

## 영상 제작 방식
**Kling AI (Image to Video)** — 씬 이미지 1장 → Variant A/B/C 클립 생성 → **CapCut 편집** → 완성 MV

---

## 빠른 시작

```powershell
cd ai_anime

# 전체 곡 생성
python main.py create-all --force

# 특정 곡만 생성
python main.py create --song "곡이름"

# 출력 검증
python main.py validate

# 배치 실행
run_all.bat
```

---

## 입력 파일 형식 (`input/*.txt`)

Suno 음악 생성 프롬프트 형식을 그대로 사용합니다.

```
10년 후에도
Genre: K-pop, Emotional Ballad, Male Tenor, Warm Husky Tone, 75 BPM, ...
BPM: 75 BPM

[Intro:]
...

[Verse 1:]
바람 같은 내 맘이
하루에도 몇 번씩 변해도
...

[Chorus:]
Oh, 너를 사랑해, 지금처럼 영원히
...
```

`title`, `genre`, `bpm` 필드를 자동 파싱합니다.
섹션 헤더(`[Intro:]`, `[Verse 1:]`, `[Chorus:]` 등)를 인식해 씬을 자동 분리합니다.

---

## 제작 워크플로우

### 1단계: 프롬프트 자동 생성
```powershell
python main.py create-all --force
```

### 2단계: 캐릭터 시트 생성
`00_character_sheet.md` → Nijijourney 또는 GPT Image로 8-뷰 시트 생성

### 3단계: 씬 이미지 생성
`01_image_prompts.md` → 씬별 이미지 생성 (캐릭터 시트 첨부 필수)

### 4단계: Kling 영상 클립 생성
`02_video_prompts.md` → 씬 이미지 1장당 Variant A/B/C 클립 생성

```
씬 7개 × 3클립 = 21클립 → 3분 MV 커버 가능
```

| Variant | 특성 | 사용 구간 |
|---------|------|---------|
| A — Quiet Presence | 정적, 주변 환경 모션 | Intro / Verse / Outro |
| B — Emotional Arc | 느린 push-in, 자세 변화 | Pre-Chorus / Bridge |
| C — Peak Moment | 다이나믹 카메라, 조명 피크 | Chorus / Final Chorus |

### 5단계: CapCut 편집
`02_video_prompts.md` 하단 **CapCut Editing Map** 참조 → 섹션별 클립 배치 → MP3 오디오 붙이기 → Export

상세: [MV_제작_가이드.md](MV_제작_가이드.md)

---

## 지원 장르 프로파일 (`anime_profiles.json`)

| 키 | 장르 계열 |
|---|---|
| `telephone-signal-pop` | electronic synth pop (telephone 테마) |
| `electronic_synth_default` | electronic synth (기본 폴백) |
| `rock` | rock anime noir |
| `acoustic_ballad` | folk memory anime |
| `hip_hop_trap` | rhythmic trap-pop anime |
| `idol_pop` | bright idol anime pop |
| `jazz_soul` | late-night jazz soul anime |

장르 키워드 자동 매칭 — 별도 지정 불필요.

---

## 프로젝트 구조

```
ai_anime/
├── main.py                  # 파이프라인 진입점
├── anime_profiles.json      # 7개 장르 프로파일
├── MV_제작_가이드.md         # 전체 제작 단계별 가이드
├── run_all.bat              # Windows 배치 실행
├── templates/               # 4개 프롬프트 템플릿
│   ├── 00_character_sheet.md
│   ├── 01_image_prompts.md
│   ├── 02_video_prompts.md
│   └── 03_production_guide.md
├── input/                   # 곡 정보 txt (1곡 1파일, Suno 형식)
├── output/                  # 자동 생성 결과 (직접 편집 금지)
├── tests_unit.py            # pytest 단위 테스트
├── conftest.py              # Windows stdout UTF-8 픽스
└── .env.example             # 외부 API 없음
```

---

## 테스트

```powershell
python -m pytest tests_unit.py -v
```

---

## ai_img_video_prompt와의 차이

| 항목 | ai_img_video_prompt | ai_anime |
|------|---------------------|---------|
| 캐릭터 | 고정 (스켈레톤 밴드 Hermes) | 곡마다 고유 캐릭터 자동 생성 |
| 씬 구성 | 역할별 고정 6씬 (vocal/guitar/bass/drum/stage/crowd) | 가사 섹션 기반 가변 씬 |
| 장르 프로파일 | 19개 | 7개 |
| 영상 플랫폼 | 다중 플랫폼 | Kling AI 집중 (Variant A/B/C) |
| CapCut 맵 | 09_video_motion_prompts.md 하단 | 02_video_prompts.md 하단 |
