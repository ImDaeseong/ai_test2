# ai-tools

> 최종 수정: 2026-09-06 · 7개 프로젝트: AI 뮤직비디오 프롬프트, 애니메이션, CapCut 자동화, 멀티 에이전트, 유튜브 리서치, 로컬 음악 분석, 채용 적합도 분석(CareerDiff)
> 검증 이력: [`VERIFICATION.md`](./VERIFICATION.md) · 구조 변경 전: [`SPEC.md`](./SPEC.md) → [`ARCHITECTURE.md`](./ARCHITECTURE.md) → [`SECURITY_BOUNDARY.md`](./SECURITY_BOUNDARY.md) → [`HOLD_CONDITIONS.md`](./HOLD_CONDITIONS.md) → [`ROADMAP.md`](./ROADMAP.md)

개인 프로젝트 작업공간(실제 경로는 PC마다 다름)의 요약 인덱스입니다. 각 프로젝트의 상세 기능·명령어는 폴더별 `README.md`/`CLAUDE.md`를 참조하세요.

## 환경 설정

| 프로젝트 | 필수 환경변수 | 발급처 |
|----------|---------------|--------|
| `ai_multi_agent` | `OPENROUTER_API_KEY` (필수), `OPENAI_API_KEY` (선택 — 이미지 생성용) | [OpenRouter](https://openrouter.ai/keys) |
| `CareerDiff` | `OPENAI_API_KEY` (선택 — 미설정 시 mock 분석) | [OpenAI Platform](https://platform.openai.com) |

나머지 5개는 외부 API 없이 로컬 처리만 수행합니다. `.env.example`을 `.env`(CareerDiff는 `.env.local`)로 복사 후 키 입력, `.env*`는 `.gitignore` 처리됨.

## 프로젝트 목록

| # | 폴더명 | 설명 | 스택 | API | 빠른 실행 |
|---|--------|------|------|-----|-----------|
| 1 | [ai_anime](./ai_anime/) | 곡별 애니메 캐릭터+씬 프롬프트 생성기 (9개 장르 프로파일, 6개 이미지 플랫폼) | Python 3.9+ | 없음 | `python main.py create-all --force` |
| 2 | [ai_img_video_aiBoygirl](./ai_img_video_aiBoygirl/) | AI Boy/AI Girl 고정 캐릭터 MV 프롬프트 빌더 (36개 장르 프로파일, 26개 reference PNG) | Python 3.9+ | 없음 | `python main.py create-all --input-dir input --force` |
| 3 | [ai_img_video_prompt_capcut](./ai_img_video_prompt_capcut/) | Suno 음원+LRC+Kling 클립 → CapCut 편집 타임라인+드래프트 자동 생성 | Python | 없음 | `python main.py build --song "곡명"` |
| 4 | [ai_multi_agent](./ai_multi_agent/) | 5개 웹 UI 프롬프트 실행기 — MV, 애니메, 웹툰, 스토리, 시나리오 | Python 3.8+ | OpenRouter(필수)/OpenAI(선택) | `실행_web_mv.bat` → :5200 |
| 5 | [youtube_research](./youtube_research/) | AI 음악 유튜브 채널 벤치마킹 — 메타데이터 수집·AI필터·마크다운 리포트 | Python | yt-dlp(무료) | `python run.py search 30` |
| 6 | [music_insight_studio](./music_insight_studio/) | 로컬 음악 분석 — BPM/Key/LUFS/주파수 밸런스 + 규칙기반 믹싱/마스터링/시장성 평가, 한국어 리포트+MusicXML | Python 3.11+ | 없음 | `.venv\Scripts\python.exe -m app.web.server` → :8765 |
| 7 | [CareerDiff](./CareerDiff/docs/README.md) | 채용공고+이력서 → 요건 매칭·적합도 점수·이력서 제안·면접 준비 플랜 생성 (Job Fit Analyzer) | Next.js + TypeScript | OpenAI(선택, 미설정 시 mock) | `cd CareerDiff/app && npm run dev` |

테스트: `ai_anime` 77개·`ai_img_video_prompt_capcut` 65개·`ai_multi_agent` 40개·`youtube_research` 37개(`pytest tests_unit.py -q`) · `ai_img_video_aiBoygirl` 337개(`pytest -q`) · `music_insight_studio` 34개(`.venv\Scripts\python.exe -m unittest discover -s tests`) · `CareerDiff` 116개(`cd CareerDiff/app && npm test`)

### 프로젝트 간 연결

3개가 MV 제작 파이프라인, 나머지 4개(`ai_anime`·`youtube_research`·`music_insight_studio`·`CareerDiff`)는 독립 실행됩니다.

```
ai_img_video_aiBoygirl → 09_video_motion_prompts.md (CapCut Editing Map)
        ↓
ai_img_video_prompt_capcut + Suno 음원(.wav) + 가사(.lrc) + Kling 클립(.mp4)
        ↓
  timeline.json + shot_list.md → CapCut PC 드래프트 자동 생성
```

`ai_multi_agent`는 이 저장소의 `ai_img_video_aiBoygirl`·`ai_anime` 프롬프트 외에 별도 저장소 `ai_test1`의 `ai_story`/`ai_Scenario`/`ai-webtoon`도 실행합니다(웹 UI 5개 중 3개는 저장소 밖) — 위 7개 프로젝트 범위와 혼동 주의.

### 미완성/HOLD

- **ai_multi_agent**: 5개 웹 UI의 중복 로직 통합 진행 중 — story/scenario는 공유 스캐폴드(`web_app_scaffold.py`)로 추출 완료(2026-07-13), anime/mv/webtoon은 미착수.

전체 검증 이력·이슈는 [`VERIFICATION.md`](./VERIFICATION.md) 참조.

## 공통 특징

- 7개 프로젝트 모두 독립 실행 가능 — 다른 프로젝트 파일을 직접 import하지 않음
- 대부분 **로컬 실행 우선** — 외부 클라우드 API는 `ai_multi_agent`(필수)·`CareerDiff`(선택, mock 대체 가능)만 사용
- `youtube_research`: yt-dlp로 공개 메타데이터만 수집, 음원 다운로드 없음
- `music_insight_studio`: numpy/soundfile/librosa/pyloudnorm/basic-pitch 전부 로컬, 네트워크 호출 없음, 자체 `.venv` 사용
