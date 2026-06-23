# 설계 문서 — ai_multi_agent

> 5개 AI 콘텐츠 프로젝트의 프롬프트를 API로 실행하고 결과를 저장하는 작업 진행 관리 허브 (v2.1)
> 외부 API: OpenRouter (텍스트 생성), OpenAI (이미지 생성, 선택)

---

## 1. 목적과 범위

ai_anime, ai_img_video_aiBoygirl 등 사이드 프로젝트가 "프롬프트 파일 생성"에서 멈추는 반면, 이 프로젝트는 생성된 프롬프트를 API로 실제 실행하여 텍스트·이미지 결과물까지 저장한다.

**5개 소스 프로젝트:**

| 소스 | 내용 | 웹 UI | 포트 |
|---|---|---|---|
| `ai_img_video_prompt` | 스켈레톤 밴드 MV 이미지 프롬프트 | `web_app_mv.py` | 5200 |
| `ai_Scenario` | 시나리오 씬 프롬프트 | `web_app_scenario.py` | 5300 |
| `ai_story` | 소설 챕터 프롬프트 | `web_app_story.py` | 5400 |
| `ai_anime` | 애니 MV 이미지/영상 프롬프트 | `web_app_anime.py` | 5500 |
| `ai-webtoon` | 웹툰 패널 이미지 프롬프트 (v2.1) | `web_app_webtoon.py` | 5600 |

---

## 2. 아키텍처

```
ai_multi_agent/
├── main.py              CLI: story / scenario / mv / animate 서브커맨드
├── config.py            환경변수 로드 (API 키, 소스 프로젝트 루트 경로)
├── image_generator.py   OpenAI Image API 래퍼
├── agents/
│   ├── base.py          OpenRouter API 호출 공통 로직 (재시도·타임아웃)
│   ├── script_agent.py  곡 분석 → 장면 JSON
│   ├── image_agent.py   장면 JSON → 이미지 프롬프트
│   ├── video_agent.py   섹션 → 영상 모션 프롬프트
│   └── reviewer_agent.py 품질·정체성 검수
├── web_app_mv.py        MV 파트 웹 UI (5200)
├── web_app_scenario.py  시나리오 웹 UI (5300)
├── web_app_story.py     소설 웹 UI (5400)
├── web_app_anime.py     애니 웹 UI (5500)
└── web_app_webtoon.py   웹툰 패널 웹 UI (5600, v2.1 신규)
```

---

## 3. 실행 단위 설계

각 프로젝트는 독립된 실행 단위 구조를 가진다. API 호출은 1회에 1건씩 처리된다.

| 프로젝트 | 실행 단위 | 관리 결과 폴더 |
|---|---|---|
| MV | 파트 (01_vocal ~ 06_crowd) | `output/mv/{곡명}/parts/{파트}/` |
| Story | 챕터 (`ch001_GPT_프롬프트.md`) | `output/story/{작품명}/chapters/` |
| Scenario | 씬 (`씬001_GPT_프롬프트.md`) | `output/scenario/{작품명}/scenes/` |
| Anime | 이미지/영상/클립 그룹 | `output/anime/{곡명}/` |
| Webtoon | 패널 (`panel_NNN_*.md`) | `output/webtoon/{곡명}/panels/` |

진행 상태는 `output/` 아래 저장된 결과 파일 수로 계산된다 (소스 `state.json`만 의존하지 않음).

---

## 4. base.py API 호출 공통 로직

```python
def call_api(prompt, model, max_retries=3, timeout=60, retry_delay=5):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={"model": model, "messages": [...]},
                timeout=timeout
            )
            return response.json()["choices"][0]["message"]["content"]
        except (Timeout, RequestException):
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    raise RuntimeError("API 호출 최대 재시도 초과")
```

**설계 원칙:**
- 재시도 3회, 5초 간격, 60초 타임아웃
- 모든 에이전트는 base.py를 통해서만 API 호출 — 직접 requests 사용 금지
- API 키는 `config.py`에서만 로드

---

## 5. config.py 환경변수

```python
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENAI_API_KEY     = os.getenv("OPENAI_API_KEY", "")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

# 소스 프로젝트 루트 (재정의 가능)
HERMES_ROOT    = os.getenv("HERMES_ROOT",    "ai_img_video_prompt")
STORY_ROOT     = os.getenv("STORY_ROOT",     "ai_story")
SCENARIO_ROOT  = os.getenv("SCENARIO_ROOT",  "ai_Scenario")
ANIME_ROOT     = os.getenv("ANIME_ROOT",     "ai_anime")
WEBTOON_ROOT   = os.getenv("WEBTOON_ROOT",   "ai-webtoon")  # v2.1
```

**규칙**: `.env` 직접 생성·수정 금지 — `.env.example`만 수정.

---

## 6. 웹툰 패널 흐름 (v2.1 신규)

```
ai-webtoon/output/{곡명}/panels/panel_NNN_{section}_{type}.md
  각 파일 내 ## GPT Image 블록에서 프롬프트 추출
        ↓
  OpenAI Image API (gpt-image-1)
        ↓
ai_multi_agent/output/webtoon/{곡명}/panels/{panel_stem}/
  image_prompt.md  image.png  manifest.json  status.json
```

패널 1개 = 이미지 1장. 완료/이미지 뱃지로 진행 상태 표시.

---

## 7. 알려진 버그 패턴

| 증상 | 원인 | 해결 |
|---|---|---|
| `OPENROUTER_API_KEY not set` | `.env` 파일 없음 | `.env.example` → `.env` 복사 후 키 입력 |
| API 타임아웃 | OpenRouter 서버 부하 | `base.py` timeout 값 늘리거나 무료 모델 변경 |
| 빈 문자열 응답 | 무료 모델 할당량 초과 | 다른 무료 모델로 교체 또는 대기 |
| 웹 UI 포트 충돌 | 다른 프로세스가 해당 포트 점유 | `netstat -ano \| findstr :5200` 후 종료 |
| 이미지 생성 버튼 오류 | `OPENAI_API_KEY` 미설정 | `.env`에 키 추가 (없으면 프롬프트 복사만 가능) |

---

## 8. 테스트 전략

```powershell
python -m pytest tests_unit.py -q   # 27 passed
```

- 단위 테스트: API 호출 없이 순수 로직만 (파싱, 포맷, 경로 처리, API 모킹)
- 실제 API 검증: 웹 UI에서 직접 프롬프트 실행 후 확인

---

## 9. 확장 시 주의사항

- **6번째 프로젝트 추가**: `config.py`에 ROOT 상수 추가, `web_app_{name}.py` 신규 작성, `requirements.txt` 의존성 확인
- **모델 교체**: `config.py`의 `OPENROUTER_MODEL` 변경. 무료 모델마다 context 길이·응답 포맷이 다름.
- **에이전트 출력 스키마 변경**: 하위 에이전트 입력 파서도 반드시 같이 수정.
- **이미지 생성 없이 사용**: `OPENAI_API_KEY` 없으면 이미지 생성 단계 스킵, 프롬프트 복사는 동작.

---

*Last Updated: 2026-06-23*
