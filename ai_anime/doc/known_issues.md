# Known Issues — ai_anime

> Last reviewed: 2026-06-27

## Open Issues

### P1 — `scripts/genre_reference.py` import 경로 오류

`scripts/` 하위에서 루트 `main.py`를 직접 import하면 `ModuleNotFoundError`가 발생한다.
이 파일은 참조용 유틸리티지만 현재 실행 불가 상태.

**증상:**
```python
# scripts/genre_reference.py
from main import _IDENTITY_HINTS   # ← FileNotFoundError
```

**수정 방법:**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from main import _IDENTITY_HINTS
```

---

### P2 — `validate-diversity` 커맨드 미존재

장르 분포 검증 커맨드가 없어 특정 장르에 편중된 input 세트를 조기에 탐지할 수 없다.
Suno 부정 태그(`-Acoustic guitar`)가 장르 키워드로 오탐될 경우 감지 불가.

**제안:** `python main.py validate-diversity` — 장르별 곡 수 분포 출력

---

### P3 — `_match_genre()` 에서 `raw_text` 전체 대상 키워드 매칭

장르 키워드가 가사 본문에도 등장할 때 오매칭 위험이 있다.
`genre` 필드 라인만을 대상으로 매칭하면 정확도가 높아진다.

---

## 추가 고려 사항

| 우선순위 | 항목 | 세부 내용 |
|---------|------|---------|
| P4 | 11번째 장르 프로파일 추가 | `city-pop` 또는 `neo-r&b` — 현재 `electronic_synth_default` 폴백 다수 |

---

## 프로파일 추가 완료 — 2026-06-27

| 장르 | 추가 위치 | 키워드 |
|------|---------|--------|
| `dark_trap` | `PROFILE_KEYWORDS`, `_IDENTITY_HINTS`, `anime_profiles.json` | dark industrial trap, dark trap, industrial rap, aggressive trap, hardcore trap |
| `trap_soul` | `PROFILE_KEYWORDS`, `_IDENTITY_HINTS`, `anime_profiles.json` | trap soul, alt r&b, dark moody r&b, dark r&b, dark rhythm |

**알려진 한계 (현상 유지 결정):**
- `아직도 거기 있었어` (alt R&B, trap soul) → score-based 매칭에서 3파 동점 발생, `acoustic_ballad` 선택됨
- 원인: lo-fi piano 등 가사 내 piano 키워드가 acoustic_ballad 점수를 올림
- 판단: anime MV 맥락에서 acoustic_ballad 스타일도 자연스러움 — 현상 유지
- 필요 시 input 파일에 `Genre Profile: trap_soul` 한 줄 추가로 즉시 오버라이드 가능

---

## 검증 상태 (2026-06-27)

| 항목 | 상태 |
|------|------|
| 단위 테스트 | 77/77 통과 |
| 지원 장르 프로파일 | 9개 (dark_trap, trap_soul 추가) |
| 이미지 플랫폼 | 6종 |
| 외부 API | 없음 (순수 Python 템플릿 치환) |
