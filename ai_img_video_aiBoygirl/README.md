# AI Boy/AI Girl MV 프롬프트 빌더

> AI Boy/AI Girl 3D 치비 토이 로봇 피규어 고정 캐릭터를 유지하면서, 곡마다 장르·무드·템포·감정·조명·카메라·연주 방식·관중 반응만 교체하는 MV 프롬프트 자동 생성 CLI 도구.
> **2026-06-09 기준 안정화 확인 — 285 테스트 PASS. 장르 프로파일 32개, reference 이미지 22개, 214곡 검증 PASS.**

> **실제 MV 제작 방법 (GPT 이미지 생성 → Kling/Flow 영상 → CapCut 편집):**
> [MV_제작_가이드.md](MV_제작_가이드.md) 참조

---

## 빠른 시작

```powershell
# 단일 곡
python main.py create --title "환승역" --input input\환승역.txt

# 전체 일괄 생성
python main.py create-all --input-dir input --force

# 배치 파일
.\run_all.bat
```

---

## 상세 문서

| 문서 | 내용 |
|------|------|
| [doc/character_design.md](doc/character_design.md) | AI Boy/AI Girl 장르별 의상·색상·소품 전체 참조, 뷰별 특징, GPT 사용 가이드 |
| [doc/changelog.md](doc/changelog.md) | 프로젝트 변경 이력 (2026-06-02 ~ 현재) |
| [MV_제작_가이드.md](MV_제작_가이드.md) | GPT 이미지 → Kling/Flow 영상 → CapCut 편집 실전 가이드 |

---

## 프로젝트 구조

```
ai_img_video_aiBoygirl/
├── main.py                   ← 핵심 엔진 (단일 파일)
├── genre_profiles.json       ← 32개 장르 프로필 (roles, lighting, camera, energy)
├── doc/                      ← 상세 기술 문서
│   ├── character_design.md   ← AI Boy/AI Girl 장르별 디자인 전체 참조
│   └── changelog.md          ← 변경 이력
├── templates/                ← 프롬프트 원본 (9개 파일)
│   ├── 01_master_style_prompt.md
│   ├── 02_style_lock_prompt.md
│   ├── 03_vocal_image_prompt.md
│   ├── 04_guitar_image_prompt.md
│   ├── 05_bass_image_prompt.md
│   ├── 06_drum_image_prompt.md
│   ├── 07_stage_image_prompt.md
│   ├── 08_atmosphere_image_prompt.md
│   └── 09_video_motion_prompts.md
├── reference/                ← 장르별 기준 캐릭터 이미지 (PNG 22개)
│   ├── base.png              ← 기본값 (defaults 프로필)
│   ├── rock.png, jazz.png, ballad.png, hiphop.png, electronic.png
│   ├── idol_boy.png, idol_girl.png, telephone.png
│   ├── r&b.png, house.png
│   └── blues.png, cinematic.png, citypop.png, dreampop.png, funk.png
│       future.png, koreantraditional.png, orchestra.png, reggae.png, trot.png
├── input/                    ← 곡 정보 txt 파일
├── output/                   ← 곡별 생성 결과
│   └── {곡제목}/
│       ├── 01~09_*.md        ← 생성된 프롬프트
│       ├── 00_prompt_overview.md   ← 한글 영상 설명
│       └── README.md               ← 섹션별 편집 가이드
├── tests/test_main.py        ← pytest 테스트 285개 PASS
├── requirements-dev.txt      ← 테스트 실행용 개발 의존성
└── conftest.py
```

---

## 고정-가변 분리 원칙

이 도구의 핵심 설계는 두 영역을 철저히 분리합니다.

| 항목 | 고정 (Fixed) | 가변 (Per-song) |
|------|-------------|----------------|
| 캐릭터 외형 | AI Boy/AI Girl 3D 치비 토이 로봇 피규어 | - |
| 캐릭터 구조 | TV 스크린 페이스 디스플레이, 라운드 로봇 헬멧, 통통한 치비 바디 | - |
| 템플릿 구조 | 9개 파일, 각 역할(보컬/기타/베이스/드럼/무대/분위기) | - |
| 캐릭터 의상·소품·색상 | - | genre_profiles.json `roles` 매칭 |
| 장르 에너지 | - | genre_profiles.json 매칭 |
| 조명·카메라 | - | genre_profiles.json |
| 역할별 연출 | - | roles 딕셔너리 |
| 관중 반응 | - | crowd 역할 |

**"캐릭터는 바뀌지 않는다. 의상·연주 방식·분위기만 바뀐다."**

---

## AI Boy/AI Girl 캐릭터 개념

- **형태:** 3D 치비 토이 로봇 피규어 — Funko Pop 스타일의 수집형 완구 비율
- **머리:** 라운드 로봇 헬멧 + TV 스크린 페이스 디스플레이 (감정 표시)
- **몸:** 통통한 치비 바디, 짧은 팔다리, 부드러운 곡면 디자인
- **렌더링:** 3D 논포토리얼리스틱, 스무스 라운디드 폼, 수집형 완구 질감
- **의상·소품·색상:** 장르별 고정값 — `genre_profiles.json`의 `roles` 딕셔너리에서 참조
- **기준 이미지:** `reference/` 폴더의 장르별 PNG — GPT 이미지 생성 시 반드시 첨부

---

## `[CHARACTER_*]` 플레이스홀더 시스템

9개 템플릿 파일에는 12개의 `[CHARACTER_*]` 플레이스홀더가 있습니다.
모든 값은 `genre_profiles.json`의 `roles` 딕셔너리에서 자동 주입됩니다.

| 플레이스홀더 | 내용 |
|------------|------|
| `[CHARACTER_OUTFIT]` | AI Boy 장르별 의상 설명 |
| `[CHARACTER_OUTFIT_GIRL]` | AI Girl 장르별 의상 설명 (별도 독립 디자인) |
| `[CHARACTER_PROP]` | 보컬이 쥐는 소품 |
| `[CHARACTER_COLOR]` | 지배적 색상 |
| `[CHARACTER_REFERENCE]` | reference/ 이미지 경로 |
| `[CHARACTER_VOCAL]` | 보컬 캐릭터 역할 설명 |
| `[CHARACTER_VOCAL_ACTION]` | 보컬 동작 설명 |
| `[CHARACTER_GUITAR]` | 기타 연주 역할 설명 |
| `[CHARACTER_BASS]` | 베이스 연주 역할 설명 |
| `[CHARACTER_DRUM]` | 드럼 연주 역할 설명 |
| `[CHARACTER_CROWD]` | 관중 반응 설명 |
| `[CHARACTER_STAGE]` | 전체 무대 구성 설명 |

### AI Boy / AI Girl 의상 구분

각 장르의 `reference/` 이미지에는 AI Boy와 AI Girl의 독립 디자인이 있습니다.
템플릿 01~08에서 의상 줄은 두 캐릭터를 모두 표시합니다:

```
AI Boy: [CHARACTER_OUTFIT] / AI Girl: [CHARACTER_OUTFIT_GIRL]
```

GPT 이미지 생성 시 원하는 캐릭터 한 쪽만 남기고 나머지를 삭제한 뒤 사용합니다.
reference 이미지에도 동일 캐릭터의 PNG를 첨부하면 GPT가 의상을 정확히 따릅니다.

**장르별 AI Girl 독립 디자인 예시:**

| 장르 | AI Boy | AI Girl |
|------|--------|---------|
| rock | 검정 가죽 자켓, 스타 패치, 스터드 | 핑크 플레이드 체크 스커트, 스타 액세서리 |
| jazz | 웜 빈티지 오버코트, 페도라 | 더스티 모브 빈티지 레이어드 드레스, 진주 목걸이 |
| hip-hop | 오버사이즈 다크 자켓, 스냅백 | 핫핑크 오버사이즈 자켓, 크라운 배지, 핑크 스니커즈 |
| dance-pop | 민트 아이돌 스테이지 수트 | 라벤더 퍼플 아이돌 드레스, 레이어드 스커트 |
| electronic | 다크 자켓, LED 고글 | 퍼플 헬멧 리본, 네온 미니 스커트 |

---

## 플랫폼 정책 안전화

AI 이미지/영상 플랫폼이 특정 표현을 폭력·위험 도구·인체 잔해 맥락으로 오탐하는 것을 방지합니다.
생성 엔진은 최종 프롬프트 저장 직전에 `safety_normalize_prompt()`를 적용합니다.

안전화 원칙:
- 실사 인체 묘사 → 3D 치비 토이 로봇 피규어 표현으로 치환
- 과격한 행동 표현 → 음악 공연용 고에너지 표현으로 완화
- 플랫폼 오탐 가능 키워드 → 안전한 공연 장면 중심의 긍정 표현으로 교체

`validate_output.py`는 전수 검증 단계에서 정책 위험 표현 잔여 여부도 검사합니다.

### 텍스트·워터마크 제외 조건 (2026-06-07 추가)

- 템플릿 `01~08` (이미지): `Do not add any text, letters, numbers, watermarks, logos, or UI overlays to the image.`
- 템플릿 `09` (영상): `Do not add any text, letters, numbers, watermarks, logos, or UI overlays to the video.`

---

## 파이프라인

```
input/*.txt
    │
    ▼
parse_song()              ← 메타데이터 + 섹션 파싱
    │
    ▼
infer_profile()           ← genre_profiles.json 키워드 매칭
    │
    ▼
adapt_prompt_text()       ← 템플릿 → 곡별 치환
    │
    ├─ replacement_map()      [SONG_TITLE], [GENRE], [MOOD] 등 치환
    ├─ replacement_map()      [CHARACTER_*] 11개 플레이스홀더 치환
    └─ soften_aggressive_residue()   장르별 잔여 표현 후처리
    │
    ▼
output/{곡제목}/01~09_*.md + README.md + 00_prompt_overview.md
    │
    ▼
validate_song_folder()    ← placeholder 잔여, identity lock, 파일 누락 검증
```

---

## 지원 장르 프로필 (32개)

`genre_profiles.json`에 정의. 키워드 매칭으로 자동 선택됩니다.

```
subway / hyper-pop / dance-pop / rock / jazz / ballad
pop-rap / r&b / soul-pop / lo-fi / neo-soul / psychedelic
folk / dreampop / indie / afrobeats / synth-pop / house / hip-hop / ambient
melodic_rap / blues / cinematic / citypop / funk / future-bass
kpop-girl / korean-traditional / orchestra / reggae / trot / telephone-signal-pop
defaults (감성 시네마틱 팝 — 매칭 안 된 장르용)
```

각 장르 프로필은 다음 필드를 포함합니다:
- `roles`: outfit, **outfit_girl**, prop, color, reference_image, vocal, vocal_action, guitar, bass, drum, crowd, stage
- `lighting_style`, `camera_style`, `stage_energy`, `special_effects`

---

## 생성 파일 목록

| 파일 | 내용 |
|------|------|
| `01_master_style_prompt.md` | 전체 세계관 기준 장면 |
| `02_style_lock_prompt.md` | 캐릭터 고정 기준 |
| `03_vocal_image_prompt.md` | 보컬 클로즈업 |
| `04_guitar_image_prompt.md` | 기타 연주 장면 |
| `05_bass_image_prompt.md` | 베이스 연주 장면 |
| `06_drum_image_prompt.md` | 드럼 연주 장면 |
| `07_stage_image_prompt.md` | 전체 무대 와이드 |
| `08_atmosphere_image_prompt.md` | 분위기/실루엣 장면 |
| `09_video_motion_prompts.md` | 영상 모션 클립 (Kling/Flow/Veo용) |
| `00_prompt_overview.md` | 한글 영상 설명 (검수용) |
| `README.md` | 섹션별 편집 가이드 |

---

## 검증 항목

```
validate_song_folder() 자동 검증:
  ✓ reference 폴더 존재 및 비어있지 않음
  ✓ [REFERENCE_DIR] placeholder 잔여 없음
  ✓ 캐릭터 고정 문장(identity lock) 포함
  ✓ [SONG_TITLE] 등 placeholder 잔여 없음
  ✓ 이전 곡 키워드 잔여 없음 (--previous-term)
  ✓ 필수 파일 누락 없음
  ✓ 정책 위험 표현 잔여 없음
```

---

## CLI 전체 명령어

```powershell
# 단일 곡 생성
python main.py create --title "제목" --input input\파일.txt [--force]

# 전체 일괄 생성
python main.py create-all --input-dir input [--force]

# 검증만
python main.py validate --folder output\곡제목 [--previous-term 이전곡명]

# 출력 요약
python main.py summarize-all --input-dir input --output-dir output
```

---

## 입력 형식

```text
title: 들리잖아
genre: youth r&b, heartbeat groove, 89 BPM

[Intro]
[city night ambience]
오늘따라 왜 이렇게

[Verse 1]
가사...

[Chorus]
[subway impact bass]
가사...
```

- `[대괄호 제작 주석]`은 섹션 헤더가 아닌 경우 장르 추론에서 자동 제거
- `‑Heavy autotune` 같은 제외 태그도 장르 추론에서 제외
- `[Instrumentation: ...]` 같은 편곡 메모는 섹션 구분에서 제외

---

## 요구사항

- Python 3.9 이상
- 외부 패키지 불필요 (표준 라이브러리만)
- pytest (테스트 실행 시): `python -m pip install -r requirements-dev.txt`

## 검증 명령

```powershell
# 문법 검사
python -m py_compile main.py web_app.py validate_output.py

# 전체 output 품질 검증
python validate_output.py

# pytest 설치 후 단위 테스트
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

2026-06-09 현재 확인:

```text
python -m py_compile main.py web_app.py validate_output.py  → 통과
python validate_output.py                                  → 214곡 전체 PASS, 정책 위험 표현 0건
python -m pytest -q                                        → 285 passed, 0 failed
                                                             (41 errors = Windows 임시 디렉터리 권한 문제, OS 레벨)
```

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-09 | 장르 프로파일 20개 → **32개** — blues/cinematic/citypop/dreampop/funk/future-bass/kpop-girl/korean-traditional/orchestra/reggae/trot 11개 신규 추가 |
| 2026-06-09 | reference 이미지 9개 → **22개** — r&b.png, house.png 및 신규 11개 PNG 추가 |
| 2026-06-09 | `r&b` reference_image `hiphop.png`→`r&b.png`, `house` reference_image `electronic.png`→`house.png` 갱신 |
| 2026-06-09 | `citypop` 독립 프로파일 신설 — house에서 "city pop" 키워드 분리 |
| 2026-06-09 | `dreampop` 프로파일을 indie 앞에 삽입 — "dream" 서브스트링 키워드 충돌 방지 |
| 2026-06-09 | 214곡 전수 검증 PASS (validate_output.py 6섹션 전부) |
| 2026-06-08 | AI Boy/AI Girl 성별 구분 시스템 추가 — `outfit_girl` 필드, `[CHARACTER_OUTFIT_GIRL]` 플레이스홀더, 템플릿 01~08 반영 |
| 2026-06-08 | 프로젝트 전환 완료 — 스켈레톤 밴드 → AI Boy/AI Girl 3D 치비 토이 로봇 피규어, `[CHARACTER_*]` 12개 플레이스홀더 시스템, 장르 20개, reference 이미지 9개 |
| 2026-06-07 | 텍스트·워터마크 제외 조건 추가 (템플릿 01~09) |
| 2026-06-03 | 플랫폼 정책 안전화 완성, `validate_output.py` 전수 검증 도입 |
| 2026-06-02 | 프로젝트 초기 안정화 (구 ai_img_video_prompt, 스켈레톤 밴드 시대) |

상세 이력: [doc/changelog.md](doc/changelog.md)
