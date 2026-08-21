# ai-tools

> 작성일: 2026-06-23 / 최종 수정: 2026-08-17
> 총 6개 소스 프로젝트 수록. AI-assisted tools for music video production, storytelling, content research, and local music analysis.
> 검증 이력·테스트 결과: [`VERIFICATION.md`](./VERIFICATION.md)

## 저장소 목표

`ai_test2`는 AI 음악 비디오 프롬프트 생성, 애니메이션, CapCut 편집 자동화, 멀티 에이전트 실행, 유튜브 리서치, 로컬 음악 분석 도구 모음입니다. 실제 경로는 사용 중인 PC에 따라 다릅니다.

각 프로젝트의 상세 기능·CLI 전체 명령·출력 파일 구조는 해당 프로젝트 폴더의 `README.md`/`CLAUDE.md`를 참조하세요. 이 문서는 전체를 훑어보기 위한 요약 인덱스입니다.

구조 변경이나 리팩터링 전에는 루트 governance 문서를 먼저 확인합니다: [`SPEC.md`](./SPEC.md)(목적·범위·완료 기준) → [`ARCHITECTURE.md`](./ARCHITECTURE.md)(구조 위험·모듈 경계·파일 계약) → [`SECURITY_BOUNDARY.md`](./SECURITY_BOUNDARY.md)(API 키·미디어·수집 안전 경계) → [`HOLD_CONDITIONS.md`](./HOLD_CONDITIONS.md)(중단 조건) → [`ROADMAP.md`](./ROADMAP.md)(현대화 순서).

---

## 환경 설정

API 키가 필요한 프로젝트는 `.env.example`을 `.env`로 복사한 뒤 키를 입력하세요.

```powershell
cd ai_multi_agent
copy .env.example .env
```

| 프로젝트 | 필수 환경변수 | 발급처 |
|----------|---------------|--------|
| `ai_multi_agent` | `OPENROUTER_API_KEY` (필수), `OPENAI_API_KEY` (선택 — 이미지 생성용) | [OpenRouter](https://openrouter.ai/keys) |

> 나머지 5개 프로젝트는 외부 API 없이 로컬 파일 처리만 수행합니다. `.env` 파일은 `.gitignore`에 등록되어 있으므로 Git에 커밋되지 않습니다.

---

## 프로젝트 목록

| # | 폴더명 | 한 줄 설명 | 언어/스택 | API | 빠른 실행 |
|---|--------|-----------|-----------|-----|-----------|
| 1 | [ai_anime](./ai_anime/) | 곡별 애니메 캐릭터+씬 프롬프트 생성기 (7개 장르 프로파일, 6개 이미지 플랫폼) | Python 3.9+ | 없음 | `python main.py create-all --force` |
| 2 | [ai_img_video_aiBoygirl](./ai_img_video_aiBoygirl/) | AI Boy/AI Girl 고정 캐릭터 MV 프롬프트 빌더 (32개 장르 프로파일, 22개 reference PNG) | Python 3.9+ | 없음 | `python main.py create-all --input-dir input --force` |
| 3 | [ai_img_video_prompt_capcut](./ai_img_video_prompt_capcut/) | Suno 음원+LRC+Kling 클립 → CapCut 편집 타임라인+드래프트 자동 생성 | Python 3.9+ | 없음 | `python main.py build --song "곡명"` |
| 4 | [ai_multi_agent](./ai_multi_agent/) | 5개 웹 UI 프롬프트 실행기 — MV, 애니메, 웹툰, 스토리, 시나리오 | Python 3.8+ | OpenRouter(필수)/OpenAI(선택) | `실행_web_mv.bat` → :5200 |
| 5 | [youtube_research](./youtube_research/) | AI 음악 유튜브 채널 벤치마킹 — 메타데이터 수집·AI필터·마크다운 리포트 | Python 3.8+ | yt-dlp(무료) | `python run.py search 30` |
| 6 | [music_insight_studio](./music_insight_studio/) | 로컬 음악 분석 — BPM/Key/LUFS/주파수 밸런스 + 규칙기반 믹싱/마스터링/시장성 평가, 한국어 리포트+MusicXML | Python 3.9+ | 없음 | `.venv\Scripts\python.exe -m app.web.server` → :8765 |

각 행의 상세 기능·기술 스택·알려진 제약은 폴더명 링크를 따라가면 확인할 수 있습니다.

### 프로젝트 간 연결

3개 프로젝트가 MV 제작 파이프라인을 이루고, 나머지 3개는 독립 실행됩니다.

```
ai_img_video_aiBoygirl → 09_video_motion_prompts.md (CapCut Editing Map)
        ↓
ai_img_video_prompt_capcut + Suno 음원(.wav) + 가사(.lrc) + Kling 클립(.mp4)
        ↓
  timeline.json + shot_list.md → CapCut PC 드래프트 자동 생성

ai_anime              → 애니메 씬·캐릭터 프롬프트 (ai_multi_agent 웹 UI로 실행 가능)
youtube_research      → 경쟁 채널 벤치마킹, 독립 실행
music_insight_studio  → 독립 로컬 오디오 분석, 다른 프로젝트와 의존성 없음
```

`ai_multi_agent`는 이 저장소의 `ai_img_video_aiBoygirl`·`ai_anime` 프롬프트뿐 아니라 별도 저장소 `ai_test1`의 `ai_story`/`ai_Scenario`/`ai-webtoon` 프롬프트도 실행합니다(웹 UI 5개 중 3개는 저장소 밖 프로젝트) — 위 6개 프로젝트 범위와 혼동 주의.

### 주요 미완성/HOLD 항목

- **ai_multi_agent**: 5개 웹 UI의 중복 로직 통합 작업이 진행 중 — story/scenario는 공유 스캐폴드(`web_app_scaffold.py`)로 추출 완료(2026-07-13), anime/mv/webtoon은 도메인 모델이 달라 규모가 커서 아직 미착수.

검증 이력·테스트 통과 수·발견된 이슈 전체 목록은 [`VERIFICATION.md`](./VERIFICATION.md)를 참조하세요.

---

## 공통 특징

- 6개 프로젝트 모두 독립 실행 가능 — 다른 프로젝트 파일을 직접 import하지 않음
- 대부분 **로컬 실행 우선** 설계 (외부 클라우드 API는 `ai_multi_agent`만 사용)
- `youtube_research`: yt-dlp로 공개 메타데이터만 수집, 음원 다운로드 없음
- `music_insight_studio`: numpy/soundfile/librosa/pyloudnorm/basic-pitch 전부 로컬 패키지, 네트워크 호출 없음, 자체 `.venv` 사용(시스템 Python 아님)
- Python 3.9+ (`ai_multi_agent`·`youtube_research`는 3.8+), 프로젝트별 `requirements.txt` 또는 설치 안내 보유
- 각 프로젝트 테스트 명령: `ai_anime` 77개·`ai_img_video_prompt_capcut` 65개·`ai_multi_agent` 40개·`youtube_research` 37개(모두 `pytest tests_unit.py -q`) · `ai_img_video_aiBoygirl` 337개(`tests/` 디렉토리 구조라 `pytest -q`) · `music_insight_studio` 34개(`.venv\Scripts\python.exe -m unittest discover -s tests`)
