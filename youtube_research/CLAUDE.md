# CLAUDE.md — youtube_research

> AI 음악 유튜브 채널 벤치마킹 도구.
> yt-dlp로 채널·검색 메타데이터를 수집하고 마크다운 리포트를 생성한다.
> 아티스트·일반 로파이 채널을 자동 필터링해 순수 AI 음악 유튜버만 분석한다.

---

## 절대 규칙

- **실제 네트워크 호출 금지 (테스트 중)**: 테스트에서 `collect.py`의 `_ytdlp()` 를 직접 호출하지 않는다.
- **channels.json PLACEHOLDER 교체 전 수집 금지**: `PLACEHOLDER` 항목이 남아 있으면 실제 채널 수집을 실행하지 않는다.
- **output/ 파일 삭제 금지**: 수집된 raw JSON 및 생성된 리포트를 임의로 삭제하지 않는다.
- **외부 API 없음**: yt-dlp만 사용. OpenRouter 등 유료 API 호출 없음.

---

## 파일 역할

| 파일 | 역할 | 수정 시 주의사항 |
|---|---|---|
| `collect.py` | yt-dlp 기반 유튜브 메타데이터 수집 | 네트워크 의존. `channels.json` 필수 |
| `analyze.py` | raw JSON → 마크다운 리포트 + URL 목록 생성 | 외부 의존 없음. 순수 함수 위주 |
| `rank_channels.py` | 채널 조회수 랭킹 출력 | `analyze.filter_ai_channels` 재사용 |
| `run.py` | collect → analyze 전체 파이프라인 실행 | |
| `channels.json` | 수집 대상 채널 목록 + AI 필터 키워드 | PLACEHOLDER를 실제 채널로 교체 후 사용 |
| `output/raw/` | 수집된 raw JSON | |
| `output/reports/` | 생성된 마크다운 리포트 + URL 목록 | |
| `tests_unit.py` | pytest 순수 함수 37개 단위 테스트 | 네트워크 호출 없음 |

---

## 검증 명령어

```bash
# 단위 테스트
python -m pytest tests_unit.py -q
# 목표: 37 passed, 0 failed

# 구문 컴파일
python -m py_compile collect.py analyze.py rank_channels.py run.py
```

## 완료 기준

`tests_unit.py` 37개 전체 통과. `channels.json` 교체 후 `python run.py` 실행 시 수집→리포트 파이프라인 정상 동작.

---

*Last Updated: 2026-06-20*
