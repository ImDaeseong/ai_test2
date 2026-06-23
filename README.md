# ai-tools

AI-assisted tools for music video production, storytelling, and content research.  
Five independent Python projects — from prompt generation to video editing automation.

---

## Projects

| Project | What it does | Python | API |
|---------|-------------|--------|-----|
| [ai_anime](./ai_anime/) | Per-song anime character + scene prompt generator (7 genre profiles, 6 image platforms) | 3.9+ | None |
| [ai_img_video_aiBoygirl](./ai_img_video_aiBoygirl/) | Fixed AI Boy/AI Girl robot character MV prompt builder (32 genre profiles, 22 reference PNGs) | 3.9+ | None |
| [ai_img_video_prompt_capcut](./ai_img_video_prompt_capcut/) | Auto-generates CapCut editing timeline from Suno LRC + Kling video clips | 3.9+ | None |
| [ai_multi_agent](./ai_multi_agent/) | Prompt runner with 5 web UIs — MV, anime, webtoon, story, scenario | 3.8+ | OpenRouter (required) / OpenAI (optional) |
| [youtube_research](./youtube_research/) | YouTube AI music channel benchmarking — metadata collection, AI-only filtering, markdown reports | 3.8+ | yt-dlp (free) |

---

## How These Tools Connect

Three of the tools form a music video production pipeline:

```
ai_img_video_aiBoygirl
  └─ 09_video_motion_prompts.md  (CapCut Editing Map)
        │
        ▼
ai_img_video_prompt_capcut
  + Suno audio (.wav)
  + Suno lyrics (.lrc)
  + Kling-generated clips (.mp4)
        │
        ▼
  timeline.json + shot_list.md
        │
        ▼
  CapCut PC — auto-created draft project

ai_anime  ──→  anime scene + character prompts
              (can be run through ai_multi_agent web UI)

youtube_research  ──→  benchmark competitor channels independently
```

---

## Project Details

### ai_anime — Anime MV Prompt Generator

Suno `.txt` 파일 하나로 곡당 5개 파일을 자동 생성합니다.

**출력 (곡당 5파일)**

```
output/{곡명}/
├── 00_character_sheet.md    # 캐릭터 턴어라운드 시트 — 6개 이미지 플랫폼
├── 01_image_prompts.md      # 씬 이미지 프롬프트 — 씬별 × 6플랫폼
├── 02_video_prompts.md      # Kling Variant A/B/C + CapCut Editing Map
├── 03_production_guide.md   # 제작 워크플로우 + 메타데이터
└── README.md                # 곡별 요약
```

**주요 기능**
- 7개 장르 프로파일 (`anime_profiles.json`) — 곡 장르에 따라 캐릭터·환경·카메라 자동 선택
- 6개 이미지 플랫폼 지원: GPT Image · Gemini Imagen · Midjourney · Nijijourney · FLUX.1 · Leonardo.Ai
- 영상 제작: Kling AI Image-to-Video → Variant A/B/C 클립 → CapCut 편집
- SAFETY_BLOCKLIST 필터 내장 — 금지 표현 자동 치환

**실행**

```powershell
python main.py create-all --force       # 전체 곡 생성
python main.py create --song "곡이름"   # 단일 곡
python main.py validate                 # 출력 검증
```

---

### ai_img_video_aiBoygirl — AI Boy/AI Girl MV Prompt Builder

AI Boy / AI Girl 3D 치비 토이 로봇 피규어 **고정 캐릭터**를 유지하면서, 곡마다 장르·무드·조명·카메라만 교체하는 MV 프롬프트 빌더.

**출력 (곡당 11파일 + 검증 2파일)**

```
output/{곡명}/
├── 01_master_style_prompt.md     # 마스터 스타일 (GPT/Midjourney)
├── 02_style_lock_prompt.md       # 캐릭터 고정 프롬프트
├── 03_vocal_image_prompt.md      # 보컬 이미지
├── 04_guitar_image_prompt.md     # 기타리스트 이미지
├── 05_bass_image_prompt.md       # 베이시스트 이미지
├── 06_drum_image_prompt.md       # 드러머 이미지
├── 07_stage_image_prompt.md      # 스테이지 이미지
├── 08_atmosphere_image_prompt.md # 분위기 이미지
├── 09_video_motion_prompts.md    # 영상 모션 + CapCut Editing Map
├── _ALL_PROMPT_OVERVIEW.md       # 전체 프롬프트 요약
└── _PROMPT_AUDIT.md              # 정책 위반 검사 결과
```

**주요 기능**
- 32개 장르 프로파일 (`genre_profiles.json`) + 22개 장르별 reference 이미지
- `[CHARACTER_*]` 플레이스홀더 치환 엔진 — 캐릭터 일관성 유지
- 안전 필터 2단계: `SAFETY_BLOCKLIST` 검출 + `SAFETY_RISK_MAP` 자동 치환
- `09_video_motion_prompts.md`의 `## CapCut Editing Map`을 ai_img_video_prompt_capcut이 직접 사용

**실행**

```powershell
python main.py create --title "환승역" --input input\환승역.txt
python main.py create-all --input-dir input --force
python main.py validate --folder output\환승역
```

---

### ai_img_video_prompt_capcut — CapCut Timeline Generator

Suno 음원 + LRC 파일을 분석해 CapCut MV 편집용 타임라인과 드래프트 프로젝트를 자동 생성하는 CLI 도구.

**입력 구조**

```
input/{곡명}/
├── {곡명}.wav                   # 음원 (mp3·m4a·flac 가능)
├── *.lrc                        # Suno 가사 파일 (섹션 타임스탬프 포함)
├── *.srt                        # 한글 자막 (선택)
├── *_en.srt                     # 영어 자막 (선택)
├── *_video_motion_prompts.md    # ai_img_video_aiBoygirl 생성 파일
└── clips/                       # Kling 생성 영상 클립
```

**주요 기능**
- LRC 섹션 마커(Intro / Verse / Chorus …) 파싱 → 섹션별 시작·종료 시각 계산
- `clips/` 폴더 mp4 자동 매핑, 없으면 placeholder 표시
- `"or"` 구문 지원 (`stage_A or atmosphere_A`) — 첫 클립 없으면 두 번째 자동 사용
- SRT 자막 → CapCut 드래프트에 한글/영어 분리 트랙 자동 삽입
- CapCut 8.x `draft_content.json` + `draft_meta_info.json` 직접 생성 (열어서 바로 편집 가능)

**CLI 명령 (8개)**

```powershell
python main.py inspect --song "곡명"              # 입력 상태 점검
python main.py plan    --song "곡명"              # 섹션 매핑 미리보기
python main.py build   --song "곡명"              # timeline.json + shot_list.md 생성
python main.py build-all                          # 전체 곡 일괄 처리
python main.py sync    --song "곡명"              # ai_lyric_video 오디오·자막 동기화
python main.py export-lyric-draft    --song "곡명" # 가사 영상 CapCut 드래프트 생성
python main.py export-image-lyric-draft --song "곡명" # 이미지+오디오+LRC → CapCut 드래프트
python main.py export-draft  --song "곡명"        # MV CapCut 드래프트 생성
```

---

### ai_multi_agent — Prompt Execution Hub

각 프로젝트에서 생성된 프롬프트를 OpenRouter API로 자동 실행하고 결과를 저장하는 웹 기반 작업 관리자 (v2.1).

**5개 웹 UI**

| 실행 파일 | 포트 | 소스 프로젝트 | 배치 파일 |
|---|---|---|---|
| `web_app_mv.py` | 5200 | ai_img_video_aiBoygirl | `실행_web_mv.bat` |
| `web_app_anime.py` | 5500 | ai_anime | `실행_web_anime.bat` |
| `web_app_story.py` | 5400 | ai_story | 없음 (직접 실행) |
| `web_app_scenario.py` | 5300 | ai_Scenario | 없음 (직접 실행) |
| `web_app_webtoon.py` | 5600 | ai-webtoon | 없음 (직접 실행) |

**주요 기능**
- 프롬프트 파일을 하나씩 읽어 OpenRouter API로 전송, 결과 `output/`에 저장
- 진행 상태를 `output/` 파일 수로 계산 (완료 뱃지 표시)
- API 재시도 3회 / 60초 타임아웃 / 5초 간격
- `OPENAI_API_KEY` 없으면 텍스트 프롬프트 복사만 동작 (이미지 생성 스킵)

**실행**

```powershell
pip install -r requirements.txt
copy .env.example .env   # OPENROUTER_API_KEY 입력

실행_web_mv.bat          # http://127.0.0.1:5200
실행_web_anime.bat       # http://127.0.0.1:5500
```

---

### youtube_research — AI Channel Benchmarking

AI 음악 유튜버의 메타데이터(제목·조회수·날짜·태그·썸네일)를 수집해 마크다운 리포트를 자동 생성하는 벤치마킹 도구.

**파이프라인 (원클릭)**

```
run.bat 실행
  ↓
[1/3] 수집    — 검색 쿼리 × 최대 N개 메타데이터 수집 + 중복 제거
  ↓
[2/3] 필터    — AI 채널만 통과 (화이트리스트 + 키워드 2단계)
  ↓
[3/3] 리포트  — 조회수 TOP20 / 채널 통계 / 키워드 TOP30 / 월별 트렌드
               output/reports/report_날짜.md
               output/reports/urls_날짜.txt
```

**주요 기능**
- `channels.json` 하나로 채널 목록 + 검색 쿼리 + AI 필터 키워드 관리
- AI 채널 필터 2단계: 화이트리스트(`handle` 일치) → 키워드(`ai_filter_keywords`)
- 아티스트·로파이·비평가 채널 자동 제외
- yt-dlp 경로 자동 탐지 (`shutil.which` + Windows `%APPDATA%` 경로 폴백)
- 음원 다운로드 없음 — 공개 메타데이터만 수집

**실행**

```powershell
pip install yt-dlp
python run.py search 30    # 쿼리당 30개 수집 → 필터 → 썸네일 → 리포트
```

---

## Quick Start

### No API key needed (3 projects)

```powershell
# Anime MV prompts
cd ai_anime
python main.py create-all --force

# AI Boy/AI Girl MV prompts
cd ../ai_img_video_aiBoygirl
python main.py create-all --input-dir input --force

# YouTube AI channel benchmarking
cd ../youtube_research
pip install yt-dlp
python run.py search 30
```

### CapCut automation (after generating clips in Kling AI)

```powershell
cd ai_img_video_prompt_capcut
pip install click mutagen
# place audio + LRC + clips in input/{song}/
실행.bat                               # 자동 탐지 후 build → export-draft
python main.py inspect --song MySong  # 수동 점검
```

### ai_multi_agent (OpenRouter API key required)

```powershell
cd ai_multi_agent
pip install -r requirements.txt
copy .env.example .env
# Edit .env — set OPENROUTER_API_KEY=sk-or-...
실행_web_mv.bat      # http://127.0.0.1:5200
실행_web_anime.bat   # http://127.0.0.1:5500
```

Get a free OpenRouter API key at https://openrouter.ai/keys

---

## Requirements

- Python 3.9+ (3.8+ for `ai_multi_agent` and `youtube_research`)
- Each project folder contains its own `requirements.txt` or install instructions

---

## Running Tests

```powershell
cd ai_anime                      && python -m pytest tests_unit.py -q   # 77 passed
cd ../ai_img_video_aiBoygirl     && python -m pytest -q                  # 326 passed
cd ../ai_img_video_prompt_capcut && python -m pytest tests_unit.py -q   # 65 passed
cd ../ai_multi_agent             && python -m pytest tests_unit.py -q   # 27 passed
cd ../youtube_research           && python -m pytest tests_unit.py -q   # 37 passed
```
