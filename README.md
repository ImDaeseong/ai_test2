# ai-tools

AI-assisted tools for music video production, storytelling, content research, and local music analysis.
Six independent Python projects — from prompt generation to video editing automation to audio analysis.

각 프로젝트의 출력 파일 구조·기능 상세·CLI 전체 명령은 프로젝트 폴더의 `README.md`/`CLAUDE.md`를 참조하세요. 이 문서는 전체를 훑어보기 위한 요약 인덱스입니다.

---

## Governance Docs

이 저장소는 초기 자동화 실험에서 출발한 6개 도구 모음입니다. 구조 변경이나 리팩터링 전에는 아래 문서를 먼저 확인합니다.

| 문서 | 용도 |
|---|---|
| [SPEC.md](./SPEC.md) | 목적, 범위, 완료 기준 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 현재 구조 위험, 목표 모듈 경계, 프로젝트 간 파일 계약 |
| [SECURITY_BOUNDARY.md](./SECURITY_BOUNDARY.md) | API 키, 미디어, 유튜브 수집, 프롬프트 안전 경계 |
| [HOLD_CONDITIONS.md](./HOLD_CONDITIONS.md) | 중단하고 사람 검토가 필요한 조건 |
| [VERIFICATION.md](./VERIFICATION.md) | 진행률 게이트와 실제 검증 명령·검증 이력 |
| [ROADMAP.md](./ROADMAP.md) | 현대화 순서 |

## Projects

| Project | What it does | Python | API | Quick start |
|---------|-------------|--------|-----|-------------|
| [ai_anime](./ai_anime/) | Per-song anime character + scene prompt generator (7 genre profiles, 6 image platforms) | 3.9+ | None | `python main.py create-all --force` |
| [ai_img_video_aiBoygirl](./ai_img_video_aiBoygirl/) | Fixed AI Boy/AI Girl robot character MV prompt builder (32 genre profiles, 22 reference PNGs) | 3.9+ | None | `python main.py create-all --input-dir input --force` |
| [ai_img_video_prompt_capcut](./ai_img_video_prompt_capcut/) | Auto-generates CapCut editing timeline + draft project from Suno audio + LRC + Kling video clips | 3.9+ | None | `python main.py build --song "곡명"` |
| [ai_multi_agent](./ai_multi_agent/) | Prompt runner with 5 web UIs — MV, anime, webtoon, story, scenario | 3.8+ | OpenRouter (필수) / OpenAI (선택) | `실행_web_mv.bat` → :5200 |
| [youtube_research](./youtube_research/) | YouTube AI music channel benchmarking — metadata collection, AI-only filtering, markdown reports | 3.8+ | yt-dlp (무료) | `python run.py search 30` |
| [music_insight_studio](./music_insight_studio/) | Local-first music analysis — BPM/Key/LUFS/frequency-balance + rule-based mixing/mastering/marketability scoring, Korean reports + MusicXML | 3.9+ | None | `.venv\Scripts\python.exe -m app.web.server` → :8765 |

---

## How These Tools Connect

Three of the tools form a music video production pipeline; the other three run independently.

```
ai_img_video_aiBoygirl
  └─ 09_video_motion_prompts.md  (CapCut Editing Map)
        │
        ▼
ai_img_video_prompt_capcut
  + Suno audio (.wav) + Suno lyrics (.lrc) + Kling-generated clips (.mp4)
        │
        ▼
  timeline.json + shot_list.md → CapCut PC (auto-created draft project)

ai_anime             ──→ anime scene + character prompts (can run through ai_multi_agent web UI)
youtube_research      ──→ benchmark competitor channels, independent
music_insight_studio  ──→ independent local audio analysis, no dependency on any other project
```

`ai_multi_agent`는 이 저장소의 `ai_img_video_aiBoygirl`·`ai_anime` 프롬프트뿐 아니라 별도 저장소 `ai_test1`의 `ai_story`/`ai_Scenario`/`ai-webtoon` 프롬프트도 실행합니다(웹 UI 5개 중 3개는 저장소 밖 프로젝트) — Projects 표의 6개 범위와 혼동 주의.

---

## Quick Start

```powershell
# API 키 불필요 — Anime MV prompts
cd ai_anime && python main.py create-all --force

# API 키 불필요 — AI Boy/AI Girl MV prompts
cd ../ai_img_video_aiBoygirl && python main.py create-all --input-dir input --force

# API 키 불필요 — YouTube AI channel benchmarking
cd ../youtube_research && pip install yt-dlp && python run.py search 30

# API 키 불필요 — Local music analysis (이 체크아웃에 .venv 이미 구성됨)
cd ../music_insight_studio && .venv\Scripts\python.exe -m app.web.server --host 127.0.0.1 --port 8765
# 새 클론이라 .venv가 없으면: python -m venv .venv && .venv\Scripts\pip.exe install -r requirements.txt

# API 키 불필요 — CapCut 편집 자동화 (Kling AI로 클립 먼저 생성해야 함)
cd ../ai_img_video_prompt_capcut && pip install click mutagen
# audio + LRC + clips를 input/{song}/에 배치 후
실행.bat

# OpenRouter API 키 필요 — ai_multi_agent
cd ../ai_multi_agent && pip install -r requirements.txt
copy .env.example .env   # OPENROUTER_API_KEY=sk-or-... 입력 (https://openrouter.ai/keys 무료 발급)
실행_web_mv.bat           # http://127.0.0.1:5200
```

---

## Requirements

- Python 3.9+ (3.8+ for `ai_multi_agent` and `youtube_research`)
- Each project folder contains its own `requirements.txt` or install instructions
- `music_insight_studio` uses its own `.venv` (not the system Python) — see its `README.md`

## Running Tests

```powershell
cd ai_anime                      && python -m pytest tests_unit.py -q   # 77 passed
cd ../ai_img_video_aiBoygirl     && python -m pytest -q                  # 337 passed
cd ../ai_img_video_prompt_capcut && python -m pytest tests_unit.py -q   # 65 passed
cd ../ai_multi_agent             && python -m pytest tests_unit.py -q   # 40 passed
cd ../youtube_research           && python -m pytest tests_unit.py -q   # 37 passed
cd ../music_insight_studio       && .venv\Scripts\python.exe -m unittest discover -s tests   # 34 passed
```

전체 재검증 이력과 발견된 이슈는 [`VERIFICATION.md`](./VERIFICATION.md)를 참조하세요.
