# CLAUDE.md — ai_img_video_prompt_capcut

## 절대 규칙

- `production_config.json`을 삭제하지 않는다 — 모든 CLI 명령의 진입점
- `load_config()` 구조 변경 시 `Doc/ai_img_video_prompt_capcut.md` Section 6 동시 수정
- 시간 단위 혼동 금지: `timeline.json`은 **ms**, CapCut 드래프트는 **μs**
- `crowd_A`, `crowd_B` 클립명 사용 금지 — 2026-06-08 이후 `atmosphere_A`, `atmosphere_B`로 전환됨

## 파일 역할

| 파일 | 역할 | 수정 시 주의사항 |
|---|---|---|
| `main.py` | CLI 전체 (inspect/plan/build/build-all/export-draft) | `load_config()`, `match_sections()`, `build_slots()` 연쇄 의존 |
| `capcut_draft.py` | CapCut 8.x 드래프트 JSON 생성 | μs 단위 필수, CapCut 버전 변경 시 `_NEW_VERSION` 업데이트 |
| `production_config.json` | 모드 설정 + 섹션별 클립 매핑 | 구조: `{"modes": {"mvp": {"capcut_map": {"sections": [...]}}}}` |
| `tests_unit.py` | 순수 함수 단위 테스트 | 파일 I/O 없이 tempfile 사용 |

## production_config.json 섹션 키 규칙

`match_sections()`가 생성하는 키와 반드시 일치해야 한다:

| LRC 섹션명 | capcut_map 키 |
|---|---|
| intro | `Intro` |
| verse 1 / verse | `Verse 1` |
| verse 2 | `Verse 2` |
| pre-chorus | `Pre-Chorus` |
| chorus (마지막 제외) | `Chorus 1` |
| chorus (마지막, 2회 이상) | `Final Chorus` |
| bridge / solo | `Bridge/Solo` |
| outro | `Outro` |

## 검증 명령어

```powershell
python -m py_compile main.py capcut_draft.py    # 문법 검사
python -m pytest tests_unit.py -q               # 단위 테스트
python main.py inspect --song {곡명}             # 실제 입력 상태 확인
python main.py plan    --song {곡명}             # 섹션 매핑 미리보기
```

## 완료 기준

- `tests_unit.py` 전체 통과
- `python main.py inspect --song {곡명}` — LRC 파싱 정상 출력
- `python main.py plan --song {곡명}` — 섹션 매핑 미리보기 정상 출력
- `python main.py build --song {곡명}` — `output/{곡명}/latest/timeline.json` 생성
