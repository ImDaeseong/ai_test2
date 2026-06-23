# 변경 이력

---

## 2026-06-08 — AI Boy/AI Girl 성별 구분 시스템 추가

**배경:** reference/ 폴더의 9개 디자인 시트를 분석한 결과, 장르별로 AI Boy와 AI Girl의 의상 디자인이 완전히 독립적임을 확인. 기존 `outfit` 필드는 AI Boy 기준 한 줄만 있어 AI Girl 생성 시 의상 정보가 누락됨.

**변경 내용:**

| 파일 | 변경 |
|------|------|
| `genre_profiles.json` | 20개 장르 + defaults에 `outfit_girl` 필드 추가 |
| `main.py` | `_PLACEHOLDER_PATTERN`에 `CHARACTER_OUTFIT_GIRL` 추가, `replacement_map()` 반환 추가 |
| `templates/01~08` | 의상 줄 `AI Boy: [CHARACTER_OUTFIT] / AI Girl: [CHARACTER_OUTFIT_GIRL]` 형태로 변경 |
| `CLAUDE.md` | `roles` 필수 필드 목록에 `outfit_girl` 추가 |
| `README.md` | 플레이스홀더 표 12개로 업데이트, AI Boy/AI Girl 의상 구분 섹션 신설 |
| `doc/` | `character_design.md`, `changelog.md` 신설 |

**검증 결과:** 285 passed, 0 failed (41 errors = Windows OS 권한 문제, 코드 무관)

---

## 2026-06-08 — AI Boy/AI Girl 전환 완료 (스켈레톤 → AI Boy/AI Girl)

**배경:** 프로젝트명 `ai_img_video_prompt` → `ai_img_video_aiBoygirl` 로 변경. 고정 캐릭터를 언데드 사이버펑크 스켈레톤 밴드에서 AI Boy/AI Girl 3D 치비 토이 로봇 피규어로 전환.

**변경 내용:**

| 항목 | 이전 | 이후 |
|------|------|------|
| 캐릭터 | 언데드 사이버펑크 스켈레톤 밴드 (Hermes) | AI Boy/AI Girl 3D 치비 토이 로봇 피규어 |
| 의상 소스 | 하드코딩 (검정 가죽, 체인, 스파이크) | `genre_profiles.json` `roles` 딕셔너리 |
| 플레이스홀더 | 없음 (직접 텍스트) | `[CHARACTER_*]` 11개 시스템 |
| 장르 수 | 19개 | 20개 (`telephone-signal-pop` 추가) |
| reference 이미지 | 단일 기준 이미지 | 장르별 9개 독립 PNG |
| identity lock | 스켈레톤 문구 검사 | AI Boy/AI Girl 치비 피규어 문구 검사 |
| 정책 안전화 | 해골/인체 잔해 치환 | 실사 인체 묘사 차단 |

**추가된 `[CHARACTER_*]` 플레이스홀더 (11개 → 이후 12개):**
`CHARACTER_OUTFIT`, `CHARACTER_PROP`, `CHARACTER_COLOR`, `CHARACTER_REFERENCE`,
`CHARACTER_VOCAL`, `CHARACTER_VOCAL_ACTION`, `CHARACTER_GUITAR`, `CHARACTER_BASS`,
`CHARACTER_DRUM`, `CHARACTER_CROWD`, `CHARACTER_STAGE`

**검증 결과:** 285 passed, 0 failed

---

## 2026-06-07 — 텍스트·워터마크 제외 조건 추가

**배경:** AI 이미지/영상 생성기가 프롬프트 없이도 글자·숫자·로고를 삽입하는 현상 발견.

**변경 내용:**
- 템플릿 01~08 (이미지): `Do not add any text, letters, numbers, watermarks, logos, or UI overlays to the image.`
- 템플릿 09 (영상): `Do not add any text, letters, numbers, watermarks, logos, or UI overlays to the video.`

---

## 2026-06-03 — 플랫폼 정책 안전화 완성 (구 스켈레톤 시대)

**배경:** 일부 AI 이미지 플랫폼이 스켈레톤 관련 표현을 폭력·인체 잔해 맥락으로 오탐.

**변경 내용:**
- `safety_normalize_prompt()` — 위험 표현 치환 딕셔너리
- `POLICY_RISK_TERMS` — 잔여 감지 패턴
- `validate_output.py` — 212곡 전수 검증 스크립트

**검증 결과:** 324 passed (구 버전 테스트 수)

---

## 2026-06-02 — 프로젝트 초기 안정화 (구 ai_img_video_prompt)

- 9개 템플릿 파일 구조 확정
- 19개 장르 프로필 정의
- `soften_aggressive_residue()` — 록/어그레시브 기본값 후처리 완성
- pytest 테스트 324개 작성
- `validate_output.py` 212곡 전수 검증 도입
