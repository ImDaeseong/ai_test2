# 설계 문서 — ai_img_video_aiBoygirl

> AI Boy/AI Girl 3D 치비 토이 로봇 피규어 고정 캐릭터 MV 이미지·영상 프롬프트 자동 생성
> 외부 AI API 없음. 순수 Python 표준 라이브러리만 사용.

---

## 1. 목적과 범위

Suno 곡 정보 txt를 입력받아, AI Boy/AI Girl 3D 치비 토이 로봇 피규어 세계관의 뮤직비디오 제작에 필요한 9종 프롬프트 파일을 자동 생성한다. 캐릭터 형태(로봇 헬멧, TV 스크린 페이스, 치비 바디)는 고정이고, 곡마다 장르 프로파일이 교체되어 의상·소품·색상·에너지·카메라가 달라진다.

**입력**: `input/{곡 제목}.txt`
**출력**: `output/{곡 제목}/` 아래 11개 파일 + `_ALL_PROMPT_OVERVIEW.md`, `_PROMPT_AUDIT.md` (루트)

| 번호 | 파일 | 용도 |
|---|---|---|
| 00 | `00_prompt_overview.md` | 전체 프롬프트 요약 + 곡 방향 (한글) |
| 01 | `01_master_style_prompt.md` | 전체 세계관 기준 장면 |
| 02 | `02_style_lock_prompt.md` | 캐릭터 고정 기준 |
| 03 | `03_vocal_image_prompt.md` | 보컬 클로즈업 |
| 04 | `04_guitar_image_prompt.md` | 기타 연주 장면 |
| 05 | `05_bass_image_prompt.md` | 베이스 연주 장면 |
| 06 | `06_drum_image_prompt.md` | 드럼 연주 장면 |
| 07 | `07_stage_image_prompt.md` | 전체 무대 와이드 |
| 08 | `08_atmosphere_image_prompt.md` | 분위기/실루엣 장면 |
| 09 | `09_video_motion_prompts.md` | Kling/Flow 영상 모션 프롬프트 + Variant + CapCut 맵 |
| — | `README.md` | 곡별 제작 순서 가이드 |

---

## 2. 아키텍처

```
main.py
├── parse_song()              txt 파싱 → Song
├── load_genre_profiles()     genre_profiles.json 로드
├── _match_profile()          장르 키워드 매칭 → 프로파일 선택 (배열 순서 우선)
├── infer_profile()           Song → GenreProfile
├── adapt_prompt_text()       템플릿 → 곡별 치환
│   ├── replacement_map()     [SONG_TITLE], [GENRE], [MOOD] 등
│   ├── replacement_map()     [CHARACTER_*] 12개 플레이스홀더
│   └── soften_aggressive_residue()  장르별 잔여 표현 후처리
└── create_song_folder()      11개 파일 output/ 에 저장

validate_output.py
└── 6섹션 전수 검증 (214곡): 프로파일 매칭, 잔여 표현, 구조, placeholder, 정책, 미적용 장르
```

### ai_anime와 구조 비교

| 항목 | ai_anime | ai_img_video_aiBoygirl |
|---|---|---|
| 플레이스홀더 형식 | `[UPPER_SNAKE]` | `[CHARACTER_*]` 대괄호 |
| 프로파일 수 | 7개 (anime_profiles.json) | 32개 (genre_profiles.json) |
| 캐릭터 | 곡마다 새 캐릭터 생성 | AI Boy/AI Girl 고정 |
| 성별 구분 | 없음 | `outfit` / `outfit_girl` 독립 |
| 출력 파일 수 | 곡당 5개 | 곡당 11개 |
| 영상 Variant | CapCut 맵 기준 자동 계산 | 역할별 Variant A/B + CapCut 맵 |
| 정책 검증 | `main.py validate` | `validate_output.py` (전수) |

---

## 3. 데이터 흐름

```
txt 파일
  └→ parse_song()        → Song(title, genre, bpm, energy, mood, ...)

Song
  └→ _match_profile()    → profile (32개 중 1개, 배열 순서 우선 매칭)
                         → GenreProfile(roles, lighting, camera, stage_energy, ...)

Song + GenreProfile
  └→ replacement_map()   → {[CHARACTER_*]: 값} 딕셔너리

SongContext
  └→ adapt_prompt_text(template_path)
       ├→ [CHARACTER_*] 치환 (12개)
       ├→ soften_aggressive_residue()   softening_type별 후처리
       └→ safety_normalize_prompt()     정책 안전화

  (× 9개 템플릿 파일)
  └→ output/{slug}/00~09.md + README.md
```

---

## 4. 핵심 설계 결정

### 4-1. 캐릭터 고정 + 장르별 가변

AI Boy/AI Girl의 형태(로봇 헬멧, TV 스크린 페이스, 치비 바디 비율)는 불변이다. 곡마다 달라지는 것은:
- 의상·소품·색상 (`roles` 딕셔너리)
- 에너지 레벨 / 카메라 스타일 / 무대 구성
- 조명 스타일 / 특수 효과

### 4-2. AI Boy / AI Girl 성별 독립 의상

각 장르 프로파일은 `outfit`(AI Boy)와 `outfit_girl`(AI Girl) 필드를 독립적으로 갖는다.
템플릿 01~08에서 두 캐릭터를 모두 표시하며, GPT 이미지 생성 시 원하는 캐릭터만 남기고 사용한다.

### 4-3. 키워드 매칭 — 배열 순서 우선

`_match_profile()`은 `genre_profiles.json` 배열 순서대로 첫 번째 매칭 프로파일을 반환한다.
서브스트링 충돌이 있는 장르는 배열 순서로 우선순위를 결정한다:
- `dreampop` → `indie` 앞 배치 (`indie`의 "dream" 키워드가 "dream pop" 흡수 방지)
- `house` → `citypop` 앞 배치 ("funky disco" 구문 키워드 우선)
- `orchestra` → 배열 맨 끝 (classical 서브스트링 리스크 최소화)

### 4-4. softening_type 후처리

장르별 공격적 잔여 표현을 안전화한다:

| softening_type | 적용 장르 예 |
|---|---|
| `soft` | ballad, dreampop, folk, lo-fi, korean-traditional |
| `groove` | dance-pop, r&b, soul-pop, citypop, kpop-girl |
| `retro` | synth-pop, ambient |
| `hiphop` | hip-hop, pop-rap, melodic_rap |
| `null` | 나머지 (기본 정책 필터만 적용) |

### 4-5. 정책 안전화 2단계

1. **생성 시**: `adapt_prompt_text()` → `safety_normalize_prompt()` 인라인 치환
2. **사후 검증**: `validate_output.py` → 214곡 전수 6섹션 검사, 위험 표현 0건 확인

---

## 5. genre_profiles.json 스키마

```json
{
  "profiles": [
    {
      "name": "rock",
      "softening_type": null,
      "keywords": ["rock", "punk", "metal", "grunge", "hard rock"],
      "roles": {
        "outfit": "AI Boy 의상 설명",
        "outfit_girl": "AI Girl 의상 설명",
        "prop": "소품",
        "color": "주조색",
        "reference_image": "rock.png",
        "vocal": "보컬 설명",
        "vocal_action": "보컬 동작",
        "guitar": "기타 설명",
        "bass": "베이스 설명",
        "drum": "드럼 설명",
        "crowd": "관중 설명",
        "stage": "무대 설명"
      },
      "lighting_style": "...",
      "camera_style": "...",
      "stage_energy": "...",
      "special_effects": "...",
      "mood_rules": [...]
    }
  ]
}
```

**32개 장르** (2026-06-09 기준):
```
subway, hyper-pop, dance-pop, rock, jazz, ballad
pop-rap, r&b, soul-pop, lo-fi, neo-soul, psychedelic
folk, dreampop, indie, afrobeats, synth-pop, house, hip-hop, ambient
melodic_rap, blues, cinematic, citypop, funk, future-bass
kpop-girl, korean-traditional, orchestra, reggae, trot, telephone-signal-pop
defaults (감성 시네마틱 팝 — 매칭 안 된 장르용)
```

---

## 6. reference/ 이미지 시스템

`reference/` 폴더의 PNG 파일은 GPT 이미지 생성 시 첨부하는 캐릭터 디자인 기준 이미지다.

**22개 PNG** (2026-06-09 기준):
```
base.png              ← defaults 프로파일 기본값
rock.png, jazz.png, ballad.png, hiphop.png, electronic.png
idol_boy.png, idol_girl.png, telephone.png
r&b.png, house.png
blues.png, cinematic.png, citypop.png, dreampop.png, funk.png
future.png, koreantraditional.png, orchestra.png, reggae.png, trot.png
```

`genre_profiles.json`의 `roles.reference_image` 필드가 파일명을 지정한다.

---

## 7. 알려진 버그 패턴

| 증상 | 원인 | 해결 |
|---|---|---|
| 정책 위험 표현 잔존 | 새 템플릿·프로파일에 위험 표현 포함 | `validate_output.py` 실행 후 FAIL 항목 확인 |
| `[CHARACTER_*]` 그대로 출력 | `genre_profiles.json` roles에 해당 키 없음 | JSON에 누락 키 추가 |
| 장르 매칭 오류 | 키워드 서브스트링 충돌 | 배열 순서 조정 (dreampop → indie 앞 등) |
| pytest 실패 | JSON 스키마 변경 시 기대값 불일치 | 테스트의 기대값과 새 JSON 구조 비교 |

---

## 8. 테스트 전략

```
python -m pytest -q      →  326 passed, 0 failed (2026-06-23 기준)
validate_output.py       →  214곡 PASS, 위험 표현 0건
```

- **단위 테스트** (`tests/test_main.py`): 순수 함수 + JSON 파싱 + 플레이스홀더 치환 검증
- **통합 검증** (`validate_output.py`): 실제 output/ 파일 전수 정책 6섹션 검사

---

## 9. 신규 장르 추가 시 체크리스트

1. `genre_profiles.json`의 `profiles` 배열에 새 장르 객체 추가 (기존 스키마 동일하게)
2. `roles` 필드 12개 모두 포함: `outfit`, `outfit_girl`, `prop`, `color`, `reference_image`, `vocal`, `vocal_action`, `guitar`, `bass`, `drum`, `crowd`, `stage`
3. `reference/` 폴더에 해당 장르 PNG 추가
4. 키워드 충돌 확인 — 기존 장르와 서브스트링 관계 점검 후 배열 순서 결정
5. `mood_rules` 항목 추가
6. `python -m pytest -q` 전체 통과 확인
7. `python main.py create-all --force` 실행
8. `python validate_output.py` 정책 검증 PASS 확인

---

## 10. 확장 시 주의사항

- **템플릿 추가**: `templates/` 에 새 파일 추가 시 `create_song_folder()` 파일 목록, `validate_output.py`의 `IMAGE_FILES`/`PROMPT_FILES`, README 템플릿 모두 동기화 필요.
- **분위기 영상 Variant 추가**: `templates/09_video_motion_prompts.md`에 섹션 추가 후 CapCut Editing Map도 업데이트.
- **outfit_girl 독립 유지**: AI Girl 의상은 AI Boy와 독립 설계. 동일 의상 재사용 금지.

---

*Last Updated: 2026-06-09*
