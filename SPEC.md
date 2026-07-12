# ai_test2 SPEC

## One-Sentence Use Case

나는 Suno 음원과 가사, AI 이미지/영상 생성 결과를 이용해 음악 영상 제작을 반복하는 상황에서, ai_test2 도구 모음으로 프롬프트 생성, CapCut 편집 초안 생성, 프롬프트 실행, 유튜브 벤치마킹을 로컬에서 빠르게 수행한다.

## Purpose

ai_test2는 AI 음악 영상 제작을 위한 5개 독립 도구를 모은 작업공간이다.

- `ai_anime`: 곡 텍스트에서 애니메이션 MV 캐릭터/씬/영상 프롬프트 생성
- `ai_img_video_aiBoygirl`: AI Boy/AI Girl 고정 캐릭터 MV 프롬프트 생성
- `ai_img_video_prompt_capcut`: Suno 음원/LRC/클립을 CapCut 드래프트 타임라인으로 변환
- `ai_multi_agent`: 생성된 프롬프트를 OpenRouter/OpenAI 기반 웹 UI에서 실행 관리
- `youtube_research`: AI 음악 유튜브 채널 공개 메타데이터 벤치마킹

## Current State

이 저장소는 초기 자동화 실험에서 출발했기 때문에 기능은 작동하지만 구조가 단일 스크립트와 작업 자산 중심으로 되어 있다. 현재 목표는 동작을 유지하면서 문서, 경계, 테스트 기준, 코드 구조를 단계적으로 현대화하는 것이다.

## MVP Scope To Preserve

- 기존 CLI 명령과 배치 파일 사용 흐름을 깨지 않는다.
- 기존 테스트가 통과하는 기능을 회귀시키지 않는다.
- `input/ -> main.py -> output/` 흐름은 호환성 계층으로 유지한다.
- 외부 API가 필요한 기능은 `ai_multi_agent`에 한정한다.
- 실제 작업 자산은 소스 코드와 구분되도록 점진적으로 분리한다.

## Non-Goals

- 한 번에 5개 프로젝트를 새 프레임워크로 재작성하지 않는다.
- 실제 API 키, 비공개 채널 정보, 개인 데이터, 내부 서버 주소를 저장하지 않는다.
- CapCut, OpenRouter, OpenAI, yt-dlp의 외부 동작을 네트워크 없이 완전 검증했다고 주장하지 않는다.
- 테스트 통과 없이 README의 과거 수치만 근거로 완료 처리하지 않는다.

## Acceptance Criteria

- 루트 문서가 목적, 구조, 보안 경계, HOLD 조건, 검증 명령을 명시한다.
- 각 하위 프로젝트의 현재 테스트가 재현 가능하게 통과한다.
- 프로젝트 간 파일 계약이 문서화된다.
- 대형 `main.py` 파일은 단계적으로 모듈 경계가 정의된다.
- 실제 작업 입력/미디어와 테스트 fixture가 구분된다.

## Modernization Principles

- 문서 먼저, 코드는 그다음.
- 동작 보존을 최우선으로 하며 리팩터링은 작은 단위로 진행한다.
- 계약 파일과 템플릿 포맷은 테스트로 보호한다.
- API 키가 없을 때도 안전하게 실패하거나 mock/copy-only 흐름으로 동작한다.
