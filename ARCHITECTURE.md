# ai_test2 Architecture

## System Shape

ai_test2는 단일 애플리케이션이 아니라 6개 독립 프로젝트의 monorepo형 작업공간이다. 음악 영상 제작 프로젝트 일부는 파일 산출물로 연결되고, `music_insight_studio`와 `CareerDiff`는 이 파이프라인과 무관한 독립 도구다.

```text
ai_img_video_aiBoygirl / ai_anime
  -> prompt markdown and CapCut editing map
  -> ai_img_video_prompt_capcut
  -> timeline.json, shot_list.md, CapCut draft

youtube_research
  -> independent public metadata reports

music_insight_studio
  -> independent local audio analysis; no file/dependency sharing with any other project

CareerDiff
  -> independent Next.js app; local job/resume comparison with optional OpenAI generation
```

## Current Architectural Risk

현재 구조의 가장 큰 위험은 코드가 기능별 모듈보다 큰 스크립트 중심이라는 점이다.

- `ai_img_video_aiBoygirl/main.py`: parsing, profile selection, template rendering, safety filtering, validation, CLI가 한 파일에 섞임
- `ai_img_video_prompt_capcut/main.py`: LRC/SRT parsing, media discovery, slot mapping, output writing, CLI가 한 파일에 섞임
- `ai_anime/main.py`: prompt generation과 CapCut draft export가 한 진입점에 공존
- `music_insight_studio`: 위 위험에 해당 없음 — `app/{analyzers,scoring,notation,reports,services,web,cli}/` 패키지 구조로 이미 모듈 경계가 분리돼 있어 Phase 4 추출 대상이 아니다.
- `CareerDiff`: 별도 Next.js 경계와 자체 검증 문서를 유지한다. 이력서 원문과 선택적 OpenAI 호출은 다른 프로젝트로 공유하지 않는다.

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
- `youtube_research` owns yt-dlp metadata collection and must not download audio/video content.
- `music_insight_studio` makes no network calls at all — numpy/soundfile/librosa/pyloudnorm/basic-pitch are local packages only.
- `CareerDiff`는 기본 mock 경로를 유지하며, 사용자가 OpenAI를 선택한 요청에서만 채용공고와 이력서 내용을 외부 API로 전송한다.
- Generated output should be written under project output folders only.

## Refactoring Strategy

1. Add root governance documents and verification gate.
2. Create file-contract docs and tests before changing parsing logic.
3. Extract pure functions from large `main.py` files without changing CLI behavior.
4. Move sample data into `examples/` or `tests/fixtures/` while keeping legacy paths temporarily supported.
5. Only after tests and docs stabilize, consider packaging or shared libraries.
