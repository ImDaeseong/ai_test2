# ai_test2 Architecture

## System Shape

ai_test2는 단일 애플리케이션이 아니라 6개 로컬 도구의 monorepo형 작업공간이다. 각 도구는 독립 실행 가능해야 하지만 음악 영상 제작 파이프라인에서는 파일 산출물을 통해 연결된다. `music_insight_studio`는 이 파이프라인과 무관한 완전 독립 도구다.

```text
ai_img_video_aiBoygirl / ai_anime
  -> prompt markdown and CapCut editing map
  -> ai_img_video_prompt_capcut
  -> timeline.json, shot_list.md, CapCut draft

ai_multi_agent
  -> optional prompt execution and image generation UI

youtube_research
  -> independent public metadata reports

music_insight_studio
  -> independent local audio analysis; no file/dependency sharing with any other project
```

## Current Architectural Risk

현재 구조의 가장 큰 위험은 코드가 기능별 모듈보다 큰 스크립트 중심이라는 점이다.

- `ai_img_video_aiBoygirl/main.py`: parsing, profile selection, template rendering, safety filtering, validation, CLI가 한 파일에 섞임
- `ai_img_video_prompt_capcut/main.py`: LRC/SRT parsing, media discovery, slot mapping, output writing, CLI가 한 파일에 섞임
- `ai_anime/main.py`: prompt generation과 CapCut draft export가 한 진입점에 공존
- `ai_multi_agent`: 웹 UI가 프로젝트별로 복제되어 있고 공통 서비스 경계가 약함 — `web_app_story.py`/`web_app_scenario.py`는 2026-07-13에 `web_app_scaffold.py`(`create_prompt_runner_app` 팩토리)로 추출 완료(각 199줄 → 27줄 래퍼, 라우트/HTML 렌더링을 스캐폴드 12개 테스트로 보호). `web_app_anime.py`/`web_app_mv.py`/`web_app_webtoon.py`는 도메인 모델(패널/파트 vs 프롬프트/챕터)이 달라 아직 미추출 상태.
- `music_insight_studio`: 위 위험에 해당 없음 — `app/{analyzers,scoring,notation,reports,services,web,cli}/` 패키지 구조로 이미 모듈 경계가 분리돼 있어 Phase 4 추출 대상이 아니다.

## Target Module Boundaries

각 하위 프로젝트는 장기적으로 아래 경계를 따른다.

```text
src/
  core/          # dataclass / shared domain models
  parsing/       # txt, lrc, srt, markdown, config parsers
  rendering/     # template rendering and output builders
  safety/        # blocklist, risk map, output safety checks
  validation/    # project-specific validators
  services/      # orchestration without CLI/web details
  cli.py         # command-line adapter only
  web.py         # web adapter only, if needed

tests/
  unit/
  contract/
  fixtures/

docs/
  feature and contract documents
examples/
  small public examples only
```

## Project Contracts

The important cross-project contracts are file based.

- `09_video_motion_prompts.md`: CapCut Editing Map section consumed by `ai_img_video_prompt_capcut`
- LRC section labels: Intro, Verse, Pre-Chorus, Chorus, Post-Chorus, Bridge, Outro and variants
- clip names: role/section based names such as `vocal A.mp4`, `stage B.mp4`
- output reports: `timeline.json`, `shot_list.md`, CapCut `draft_content.json`, `draft_meta_info.json`

These contracts must be protected with contract tests before deep refactoring.

## Dependency Boundary

- Local-only prompt builders should not import API clients.
- `ai_multi_agent` owns OpenRouter/OpenAI runtime calls.
- `youtube_research` owns yt-dlp metadata collection and must not download audio/video content.
- `music_insight_studio` makes no network calls at all — numpy/soundfile/librosa/pyloudnorm/basic-pitch are local packages only.
- Generated output should be written under project output folders only.

## Refactoring Strategy

1. Add root governance documents and verification gate.
2. Create file-contract docs and tests before changing parsing logic.
3. Extract pure functions from large `main.py` files without changing CLI behavior.
4. Move sample data into `examples/` or `tests/fixtures/` while keeping legacy paths temporarily supported.
5. Only after tests and docs stabilize, consider packaging or shared libraries.
