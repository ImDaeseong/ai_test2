# Known Issues — ai_img_video_aiBoygirl

> Last reviewed: 2026-06-09 | Tests: 326/326 passed

## Open Issues

### P2 — Vocal/Guitar 서명 동작 위치 강화

MVP 모드에서 clip 수가 감소하면 Variant A도 제거될 수 있어 서명 동작(signature gestures)이 유실될 수 있다.
서명 동작을 Variant에서 메인 섹션으로 이전하면 MVP 모드에서도 안전하게 유지된다.

---

### P3 — `production_config.json` clips 최솟값 가드 미존재

`기타 clips` 수를 1로 설정하면 Variant A도 제거되어 서명 동작이 유실된다.
clip 수 최솟값 가드 로직 추가가 필요하다.

---

### P4 — 21번째 장르 프로파일

`k-indie` 독립 프로파일 없음 — 현재 `indie` 키워드로 매칭되지만 K-인디 고유 비주얼 스타일과 차이가 있다.

---

## 해결된 이슈

### P1 — `templates/09_video_motion_prompts.md` 서명 동작 미등록 (수정 완료)

`test_video_motion_signature_gestures_present` 테스트가 4개 악기의 서명 동작 문자열을 기대했으나
템플릿에 존재하지 않아 실패. 각 악기 섹션에 서명 동작 추가로 해결.

- 보컬 Variant A: 3개 보컬 서명 동작 추가
- 기타 Variant A: 2개 기타 서명 동작 추가
- 베이스 메인 섹션: 2개 서명 동작 추가
- 드럼 메인 섹션: 2개 서명 동작 추가

---

## 검증 상태 (2026-06-09)

| 항목 | 상태 |
|------|------|
| 단위 테스트 | 326/326 통과 |
| 장르 프로파일 | 32개 |
| `[CHARACTER_*]` 플레이스홀더 | 12개 |
| production_config 모드 | mvp (12 clips) / full (24 clips) |
