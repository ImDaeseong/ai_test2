# CLAUDE.md — ai_img_video_aiBoygirl

> AI Boy/AI Girl 3D 치비 토이 로봇 피규어 고정 캐릭터 MV 이미지·영상 프롬프트 자동 생성 프로젝트

---

## 프로젝트 개요

외부 AI API 없이 순수 Python 템플릿 치환 엔진으로 동작합니다.
곡 정보 txt → 9종 프롬프트 자동 출력, 36개 장르 프로파일 지원, 337개 테스트 PASS.

---

## 절대 규칙

- **외부 API 호출 금지**: 이 프로젝트는 외부 AI API를 사용하지 않는다. API 호출 코드를 추가하지 않는다.
- **하드코딩 금지**: 특정 색상·스타일 값을 코드에 직접 쓰지 않는다. 모든 값은 `genre_profiles.json` 또는 `templates/`에서 참조한다.
- **output/ 직접 편집 금지**: `output/` 폴더의 파일은 `main.py`로만 생성한다.
- **플랫폼 정책 안전화 우회 금지**: 정책 위험 표현 필터를 제거하거나 우회하지 않는다.

---

## 파일 역할

| 파일 | 역할 | 수정 시 주의사항 |
|---|---|---|
| `main.py` | 파이프라인 실행 진입점 | `create`, `create-all`, `validate` 명령 처리 |
| `genre_profiles.json` | 20개 장르별 프로파일 | 색상·스타일·캐릭터 값의 유일한 출처 |
| `templates/` | 9개 프롬프트 템플릿 | `{변수}` 플레이스홀더 형식 — 직접 값 입력 금지 |
| `validate_output.py` | 214곡 전체 정책 안전화 검증 | 수정 후 반드시 실행 |
| `tests/` | pytest 기반 336개 테스트 | 수정 후 전체 통과 확인 필수 |
| `input/` | 곡 정보 txt 파일 | 수정 금지 (입력 데이터) |
| `output/` | 곡별 생성 결과 | 직접 편집 금지 |

---

## 수정 후 검증 (반드시 실행)

```bash
# Step 1: 단위 테스트 전체
python -m pytest -q
# 목표: 336 passed, 0 failed

# Step 2: 전체 곡 정책 안전화 검증
python validate_output.py
# 목표: 214곡 전체 PASS, 정책 위험 표현 0건

# Step 3: 구문 오류 확인
python -m py_compile main.py web_app.py validate_output.py
```

**완료 기준**: 336 passed + 0 failed + 정책 위험 표현 0건

---

## genre_profiles.json 수정 규칙

- 새 장르 추가 시 기존 20개 장르와 동일한 JSON 스키마 유지
- `roles` 안에 반드시 포함: `outfit`, `outfit_girl`, `prop`, `color`, `reference_image`, `vocal`, `vocal_action`, `guitar`, `bass`, `drum`, `crowd`, `stage`
- `reference_image`는 `reference/` 폴더 내 실재 파일명 사용: `base.png`, `hiphop.png`, `rock.png`, `jazz.png`, `ballad.png`, `electronic.png`, `idol_boy.png`, `idol_girl.png`, `telephone.png`
- 추가 후 반드시 pytest 전체 실행

---

## 자주 발생하는 문제

| 문제 | 원인 | 해결 |
|---|---|---|
| 정책 위험 표현 잔존 | 새 템플릿 또는 장르 프로파일에 위험 표현 포함 | `validate_output.py` 실행 후 해당 표현 확인 |
| pytest 실패 | `genre_profiles.json` 스키마 변경 | 기존 테스트의 기대값과 비교 |
| `KeyError` in template | `{변수}` 플레이스홀더가 `genre_profiles.json`에 없음 | 해당 필드 추가 |

---

*Last Updated: 2026-06-10*
