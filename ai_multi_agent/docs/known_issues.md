# Known Issues — ai_multi_agent

> Last reviewed: 2026-06-09 | Version: v2.1 | Tests: 27/27 passed

## Open Issues

### P1 — `CLAUDE.md` v2.1 변경사항 미반영

`web_app_webtoon.py` (port 5600), `WEBTOON_ROOT` 환경변수, webtoon 전용 엔드포인트가 코드에 존재하나
`CLAUDE.md` 파일 역할 표에 누락.

**수정:** `CLAUDE.md`의 파일 역할 표에 아래 항목 추가 필요
- `web_app_webtoon.py` — 웹툰 패널 이미지 생성 (port 5600)
- `WEBTOON_ROOT` 환경변수
- `실행_web_webtoon.bat`

---

### P2 — `requirements.txt` webtoon 의존성 누락

`web_app_webtoon.py` 실행에 필요한 패키지가 `requirements.txt`에 명시되어 있지 않다.
`requirements.txt` 또는 별도 `requirements_webtoon.txt`에 추가 필요.

---

### P3 — `base.py` OpenRouter 호출 timeout 미설정

장시간 실행 모델 호출 시 응답 없이 무한 대기 가능.
API 연결 오류와 모델 처리 지연을 구분할 수 없다.

**수정:** `requests.post(..., timeout=60)` — 최소 60초 타임아웃 권장

---

### P4 — 웹 앱 헬스체크 엔드포인트 미존재

다중 서버 운영 시 각 웹 앱의 실행 상태를 확인할 방법이 없다.

**제안:** 각 `web_app_*.py`에 `/health` 또는 `/ping` 엔드포인트 추가

---

## 웹 UI 포트 배정

| 포트 | 웹앱 | 소스 프로젝트 |
|------|------|---|
| 5200 | `web_app_mv.py` | `ai_img_video_prompt` |
| 5300 | `web_app_scenario.py` | `ai_Scenario` |
| 5400 | `web_app_story.py` | `ai_story` |
| 5500 | `web_app_anime.py` | `ai_anime` |
| 5600 | `web_app_webtoon.py` | `ai-webtoon` (v2.1) |
