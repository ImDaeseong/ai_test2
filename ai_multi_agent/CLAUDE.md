# CLAUDE.md — ai_multi_agent

> LLM Agent 기반 뮤직비디오 프롬프트 자동 생성 프로젝트

---

## 프로젝트 개요

OpenRouter API를 통해 4개 Agent가 순차 협업하여 곡 분석 → MV 프롬프트를 생성합니다.

```
곡 txt
  → [1] ScriptAgent   곡 분석 → 장면 구성 JSON
  → [2] ImageAgent    이미지 프롬프트 8개 생성
  → [3] VideoAgent    섹션별 영상 모션 프롬프트 생성
  → [4] ReviewerAgent 밴드 정체성 + 품질 검수
  → output/{곡제목}/
```

---

## 절대 규칙

- **API Key 절대 금지**: `OPENROUTER_API_KEY`를 `config.py`, `main.py`, `agents/*.py` 어디에도 직접 쓰지 않는다.
- **`.env` 파일 보호**: `.env` 파일을 생성하거나 수정하지 않는다. `.env.example`만 수정한다.
- **Agent 구조 유지**: 4개 Agent의 순서와 입출력 계약을 임의로 변경하지 않는다.

---

## 파일 역할

| 파일 | 역할 | 수정 시 주의사항 |
|---|---|---|
| `base.py` | OpenRouter API 호출 공통 로직 | API 호출 재시도·타임아웃 로직 변경 시 전체 Agent에 영향 |
| `config.py` | 환경변수 로드 (API key, model) | 새 설정 추가 시 `.env.example`에 키 이름도 추가 |
| `main.py` | 4-Agent 파이프라인 조율 + story/scenario/mv 관리 CLI | Agent 호출 순서, 중간 결과 저장 경로 변경 금지 |
| `agents/script_agent.py` | 곡 정보 → 장면 JSON 생성 | 출력 JSON 스키마 변경 시 하위 Agent에 영향 |
| `agents/image_agent.py` | 장면 → 8개 이미지 프롬프트 | 프롬프트 수 변경 시 output 구조도 함께 변경 |
| `agents/video_agent.py` | 섹션별 영상 프롬프트 생성 | 섹션 파싱 방식이 script_agent 출력에 의존 |
| `agents/reviewer_agent.py` | 밴드 정체성 & 품질 검수 | 검수 기준 변경 시 다른 Agent 결과에 영향 |
| `tests_unit.py` | pytest 기반 27개 단위 테스트 | API 호출 없는 순수 함수 검증 |

---

## 검증 명령어

```bash
# 단위 테스트
python -m pytest tests_unit.py -q
# 목표: 27 passed, 0 failed

# 구문 오류 확인
python -m py_compile main.py config.py agents/base.py agents/script_agent.py agents/image_agent.py agents/video_agent.py agents/reviewer_agent.py

# story/scenario 프로젝트 목록 확인
python main.py story list
python main.py scenario list

# MV 파이프라인 출력 검증 (output/ 에 생성된 곡이 있을 때)
python main.py validate

# 단일 곡 실행 (API 키 필요)
python main.py create --input "경로/곡제목.txt"

# API 키 확인 (값 노출 없이)
python -c "import config; print('Key loaded:', bool(config.OPENROUTER_API_KEY))"
```

**완료 기준**: 27 passed, `story list` / `scenario list` 정상 출력, MV 실행 시 `validate` PASS

---

## 자주 발생하는 문제

| 문제 | 원인 | 해결 |
|---|---|---|
| `OPENROUTER_API_KEY not set` | `.env` 파일 없음 | `.env.example`을 복사하여 `.env` 생성 후 키 입력 |
| Reviewer 품질 검수 실패 | 이전 Agent 출력 JSON 스키마 불일치 | `script_agent.py` 출력 필드 확인 |
| API 타임아웃 | OpenRouter 서버 부하 | `base.py`의 timeout/retry 설정 확인 |

---

*Last Updated: 2026-06-10*
