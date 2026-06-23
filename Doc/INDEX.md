# ai-tools — 설계 문서 인덱스

각 설계 문서는 버그 수정·기능 개선·신규 장르 추가 시 가장 먼저 확인합니다.

---

## 문서 목록

| 문서 | 프로젝트 | 핵심 패턴 | 외부 API |
|---|---|---|---|
| [ai_anime.md](ai_anime.md) | 애니 MV 프롬프트 자동 생성 | JSON 프로파일 + 템플릿 치환 + CapCut 맵 | 없음 |
| [ai_img_video_aiBoygirl.md](ai_img_video_aiBoygirl.md) | AI Boy/AI Girl 치비 로봇 MV 프롬프트 생성 | JSON 프로파일 32개 + [CHARACTER_*] 치환 + 정책 필터 | 없음 |
| [ai_img_video_prompt_capcut.md](ai_img_video_prompt_capcut.md) | CapCut 타임라인 자동 생성 | LRC 파싱 + 슬롯 매핑 + 드래프트 JSON | 없음 |
| [ai_multi_agent.md](ai_multi_agent.md) | 프롬프트 실행 관리 허브 | 5개 웹 UI + OpenRouter API + 작업 상태 관리 | OpenRouter (필수) / OpenAI (선택) |
| [youtube_research.md](youtube_research.md) | AI 음악 유튜브 채널 벤치마킹 | yt-dlp 수집 + AI 채널 필터 + 마크다운 리포트 | yt-dlp (무료) |

---

## 공통 설계 원칙

### 1. 데이터 흐름 방향
```
input/ (txt) → main.py → output/ (md/json)
```
- `input/`는 읽기 전용 (절대 수정 금지)
- `output/`는 항상 `main.py`로만 생성

### 2. 설정값 외부화
- 장르·색상·스타일 값 → `*_profiles.json` 또는 `templates/`
- API 키 → `.env` (코드에 직접 쓰지 않음)
- 임계값·경로 → 모듈 상단 상수 (`ALL_CAPS`)

### 3. 안전 필터 패턴 (ai_anime, ai_img_video_aiBoygirl)
- `SAFETY_BLOCKLIST` — 금지어 목록 (출력 검증용)
- `SAFETY_RISK_MAP` — 위험 표현 → 안전 표현 치환 (생성 시 적용)
- 모든 생성 결과는 `safety_filter()` 통과 후 저장

### 4. 테스트 전략
- 순수 함수 단위 테스트만 (`tests_unit.py`)
- 외부 API·네트워크 호출 없이 실행 가능
- Windows stdout 인코딩 이슈 → `conftest.py` 패턴으로 해결

### 5. 플레이스홀더 규칙
- `ai_anime`: `[UPPER_SNAKE_CASE]` 대괄호 형식
- `ai_img_video_aiBoygirl`: `[CHARACTER_*]` 대괄호 형식 (12개)
- 미치환 플레이스홀더 → `validate` 명령으로 검출

---

## 프로젝트 간 관계

```
ai_img_video_aiBoygirl       ai_anime
   (AI Boy/AI Girl MV)        (애니 MV)
         ↓                       ↓
  09_video_motion_prompts.md  02_video_prompts.md
         ↓                       ↓
         └────────────┬──────────┘
                      ↓
        ai_img_video_prompt_capcut
          (CapCut 타임라인 자동 생성)
                      ↓
              CapCut PC 편집

ai_multi_agent ←─ ai_img_video_aiBoygirl / ai_anime 프롬프트 실행
  └─ 5개 웹 UI (story / scenario / mv / anime / webtoon)

youtube_research ←─ 독립 파이프라인 (경쟁 채널 벤치마킹)
```

---

*Last Updated: 2026-06-23*
