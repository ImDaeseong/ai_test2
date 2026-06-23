# ai_multi_agent v2.1

`ai_multi_agent`는 5개 사이드 프로젝트에서 생성된 프롬프트를 API로 자동 실행하고 결과를 저장하는 작업 진행 관리자입니다.

| 소스 프로젝트 | 내용 | 웹 UI |
|---|---|---|
| `ai_img_video_prompt` | 스켈레톤 밴드 MV 이미지 프롬프트 | `web_app_mv.py` |
| `ai_story` | 소설 챕터 GPT 프롬프트 | `web_app_story.py` |
| `ai_Scenario` | 시나리오 씬 GPT 프롬프트 | `web_app_scenario.py` |
| `ai_anime` | 애니 MV 이미지/영상 프롬프트 | `web_app_anime.py` |
| `ai-webtoon` | **웹툰 만화 패널 이미지 프롬프트** | `web_app_webtoon.py` |

---

## 빠른 시작

```bash
pip install -r requirements.txt
```

루트 폴더의 `.env`에 API 키 설정:

```env
# 텍스트 생성 (story, scenario, multi-agent)
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-4o-mini

# 이미지 자동 생성 (web_app_mv, web_app_webtoon)
OPENAI_API_KEY=sk-...
OPENAI_IMAGE_MODEL=gpt-image-1
OPENAI_IMAGE_SIZE=1536x1024
```

> `OPENAI_API_KEY` 없어도 웹 UI는 동작합니다. 이미지 생성 버튼 클릭 시 오류 메시지가 표시됩니다.

---

## 웹 실행

### 배치 파일 (권장)

```
실행_web_mv.bat          → http://127.0.0.1:5200  (MV 이미지)
실행_web_scenario.bat    → http://127.0.0.1:5300  (시나리오)
실행_web_story.bat       → http://127.0.0.1:5400  (소설)
실행_web_anime.bat       → http://127.0.0.1:5500  (애니)
실행_web_webtoon.bat     → http://127.0.0.1:5600  (웹툰 패널)
```

### Python 직접 실행

```powershell
python web_app_mv.py         # http://127.0.0.1:5200
python web_app_scenario.py   # http://127.0.0.1:5300
python web_app_story.py      # http://127.0.0.1:5400
python web_app_anime.py      # http://127.0.0.1:5500
python web_app_webtoon.py    # http://127.0.0.1:5600
```

---

## web_app_webtoon.py — 웹툰 패널 이미지 생성 (v2.1 신규)

`ai-webtoon`에서 생성한 패널 프롬프트를 읽어 OpenAI API로 이미지를 자동 생성합니다.

### 동작 흐름

```
실행_web_webtoon.bat (포트 5600)
        ↓
곡 선택 → 패널 카드 클릭
        ↓
[▶ 이미지 생성] 버튼 클릭
        ↓
GPT Image 프롬프트 추출 (panels/panel_NNN_*.md)
        ↓
OpenAI API 호출 (gpt-image-1)
        ↓
image.png 저장 + 브라우저에 즉시 표시
output/webtoon/[곡명]/panels/[패널]/image.png
```

### 사전 조건

```
1. ai-webtoon에서 먼저 실행:
   run_all.bat  (input/ → output/ 패널 프롬프트 생성)

2. .env에 OPENAI_API_KEY 설정 (이미지 자동 생성 시 필요)
   → 없어도 웹 UI 동작, 프롬프트 복사는 가능
```

### 소스 경로

```
ai-webtoon/output/[곡명]/panels/panel_NNN_[section]_[type].md
```

### 결과 저장 경로

```
ai_multi_agent/output/webtoon/[곡명]/panels/[panel_stem]/
  image_prompt.md    ← 추출된 GPT Image 프롬프트
  image.png          ← 생성된 이미지
  manifest.json      ← 생성 메타데이터
  status.json        ← {"done": true/false}
```

### 주요 기능

| 기능 | 설명 |
|------|------|
| 곡 목록 | 완료 패널 수 / 전체 패널 수 / 생성된 이미지 수 표시 |
| 패널 카드 | 섹션·타입·지속 시간, 완료/이미지 뱃지 표시 |
| 이미지 생성 | 클릭 → OpenAI API → 이미지 즉시 표시 |
| 재생성 | 이미지 있는 패널 재생성 가능 |
| 다음 패널 생성 | 미완료 패널 순서대로 자동 실행 |
| 스토리보드 | `01_storyboard.md` 인라인 조회 |
| 완료 표시 | 수동 완료 마킹 가능 |

---

## 포트 배정

| 포트 | 웹앱 | 소스 프로젝트 |
|------|------|---|
| 5200 | `web_app_mv.py` | `ai_img_video_prompt` |
| 5300 | `web_app_scenario.py` | `ai_Scenario` |
| 5400 | `web_app_story.py` | `ai_story` |
| 5500 | `web_app_anime.py` | `ai_anime` |
| **5600** | **`web_app_webtoon.py`** | **`ai-webtoon`** |

> `ai-webtoon` 독립 뷰어는 포트 **5350** (`ai-webtoon/실행_web.bat`)

---

## CLI 전체 명령어

### Story 작업 (소설)

```powershell
python main.py story list
python main.py story status "작품명"
python main.py story next "작품명" [--show]
python main.py story run "작품명" [--dry-run]
python main.py story save-output "작품명" [--chapter 3]
```

### Scenario 작업 (시나리오)

```powershell
python main.py scenario list
python main.py scenario status "작품명"
python main.py scenario next "작품명" [--show]
python main.py scenario run "작품명" [--dry-run]
python main.py scenario save-output "작품명" [--scene 5]
```

### MV 작업 (스켈레톤 밴드 MV)

```powershell
python main.py mv songs
python main.py mv prepare "곡명"
python main.py mv next "곡명" [--show]
python main.py mv attach "곡명" 01_vocal image.png
python main.py mv status "곡명"
```

---

## 결과 파일 저장 위치

| 종류 | 저장 경로 |
|------|----------|
| 소설 GPT 출력 | `output/story/작품명/chapters/chNNN_GPT_출력.md` |
| 시나리오 GPT 출력 | `output/scenario/작품명/scenes/씬NNN_GPT_출력.md` |
| MV 파트 폴더 | `output/mv/곡명/parts/파트키/` |
| Anime 결과 | `output/anime/곡명/` |
| **웹툰 패널 이미지** | **`output/webtoon/곡명/panels/패널명/image.png`** |

---

## 프로젝트 구조

```
ai_multi_agent/
├── main.py                  ← CLI 핵심 엔진
├── config.py                ← API 키 및 경로 설정
├── image_generator.py       ← OpenAI 이미지 생성
├── requirements.txt
├── agents/
│   ├── base.py              ← OpenRouter API 호출
│   ├── script_agent.py
│   ├── image_agent.py
│   ├── video_agent.py
│   └── reviewer_agent.py
├── web_app_mv.py            ← MV 웹 UI (port 5200)
├── web_app_scenario.py      ← 시나리오 웹 UI (port 5300)
├── web_app_story.py         ← 소설 웹 UI (port 5400)
├── web_app_anime.py         ← Anime 웹 UI (port 5500)
├── web_app_webtoon.py       ← 웹툰 패널 웹 UI (port 5600) ← v2.1 신규
├── 실행_web_mv.bat
├── 실행_web_scenario.bat
├── 실행_web_story.bat
├── 실행_web_anime.bat
├── 실행_web_webtoon.bat     ← v2.1 신규
├── docs/
│   ├── AI_MULTI_AGENT_PURPOSE.md
│   └── OUTPUT_PROMPT_STRUCTURES.md   ← webtoon 섹션 추가됨
└── output/
    ├── story/
    ├── scenario/
    ├── mv/
    ├── anime/
    └── webtoon/             ← v2.1 신규
```

---

## config.py 경로 설정

```python
# 소스 프로젝트 루트 (환경변수로 재정의 가능)
HERMES_ROOT      → ai_img_video_prompt/
STORY_ROOT       → ai_story/
SCENARIO_ROOT    → ai_Scenario/
ANIME_ROOT       → ai_anime/
WEBTOON_ROOT     → ai-webtoon/        ← v2.1 신규
```

`.env`에서 재정의:
```env
WEBTOON_ROOT=C:\custom\path\ai-webtoon
```

---

## 요구사항

- Python 3.8 이상
- `pip install -r requirements.txt`
- 루트 `.env`에 `OPENROUTER_API_KEY` 설정 (텍스트 생성)
- 이미지 자동 생성 시 `OPENAI_API_KEY` 추가 필요

---

## 변경 이력

### v2.1 — ai-webtoon 연동 (2026-06-04)

| 항목 | 변경 내용 |
|------|----------|
| `web_app_webtoon.py` 신규 | ai-webtoon 패널 프롬프트 → OpenAI API → 이미지 자동 생성 (포트 5600) |
| `실행_web_webtoon.bat` 신규 | 웹툰 웹 UI 실행 배치 |
| `config.py` 업데이트 | `WEBTOON_ROOT`, `WEBTOON_OUTPUT_DIR`, `WEBTOON_REFERENCE_DIR` 추가 |
| `OUTPUT_PROMPT_STRUCTURES.md` 업데이트 | 섹션 5 (Webtoon) 추가 |
| `.env.example` 업데이트 | `OPENAI_API_KEY`, `OPENAI_IMAGE_MODEL`, `OPENAI_IMAGE_SIZE` 추가 |

### v2.0 — OpenRouter API 연동 완성 (2026-06-04)

| 항목 | 변경 내용 |
|------|----------|
| 기본 모델 수정 | `openai/gpt-oss-120b:free` → `openai/gpt-4o-mini` |
| `story save-output` | GPT 출력 저장 후 ai_story state.json 자동 갱신 + 롤링 요약 치환 |
| `scenario save-output` | GPT 출력 저장 후 ai_Scenario state.json 자동 갱신 + 롤링 요약 치환 |
| `mv songs/prepare/next/attach/status` | MV 파트별 이미지 관리 |

### v1.0 — 초기 구현 (2026-06-01)

- story / scenario list, status, next, run CLI
- OpenRouter API 연동 (base.py)
- 웹 UI 4개 (story/scenario/mv/anime)
- 상태 관리 시스템 (managed output 기반)
