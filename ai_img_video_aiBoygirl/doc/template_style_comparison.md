# 템플릿 스타일 비교: ai_img_video_prompt vs ai_img_video_aiBoygirl

> 작성일: 2026-06-09  
> 목적: 두 프로젝트의 템플릿 스타일 차이, 안전성, 설계 의도를 기록한다.

---

## 1. 프로젝트 개요 비교

| 항목 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|------|---------------------|----------------------|
| 캐릭터 | 언데드 사이버펑크 스켈레톤 밴드 (4인 고정) | AI Boy / AI Girl 치비 토이 로봇 피규어 |
| 성별 구분 | 없음 | AI Boy / AI Girl 별도 아웃핏 |
| 배경 | 폐허 사이버펑크 도시 + 거대 마젠타 달 (고정) | 장르별 자동 변환 (고정 배경 없음) |
| 색조 | 네온 마젠타 + 딥 블랙 (하드코딩) | `[CHARACTER_COLOR]` 장르별 가변 |
| 렌더 스타일 | ultra detailed 3D cinematic render | 3D chibi toy render, smooth rounded forms |
| 무드 | 다크 사이버펑크 메탈 | 밝고 귀여운 K-pop 아이돌 팝 |
| 장르 프로파일 | 19개 | 20개 |
| 타겟 장르 | 록·메탈·어그레시브 에너지 중심 | K-pop·발라드·K-인디·R&B 전 장르 |
| reference 이미지 | 폴더 기반 (`[REFERENCE_DIR]`) | 파일 기반 (`[CHARACTER_REFERENCE]`) |

---

## 2. 템플릿 파일별 핵심 변경 사항

### 01 Master Style Prompt

| 구성 요소 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|---------|---------------------|----------------------|
| 캐릭터 정의 | `the same stylized fantasy cyberpunk skeleton music band` | `AI Boy/AI Girl chibi toy robot figure` |
| 외형 고정 | `skeleton vocalist/guitarist/bassist/drummer` | `screen-face display, round robot helmet, stubby chibi body` |
| 무대 배경 | `dark ruined cyberpunk city concert stage` | 제거됨 — 장르별 변환 |
| 달 | `massive glowing neon magenta moon` | 제거됨 |
| 색조 | `neon magenta and deep black` (고정) | `[CHARACTER_COLOR]` (가변) |
| 의상 | `dark stage outfits, decorative metal straps` | `[CHARACTER_OUTFIT] / [CHARACTER_OUTFIT_GIRL]` |
| 렌더 | `ultra detailed 3D cinematic render` | `3D chibi toy render, smooth rounded forms` |

---

### 02 Style Lock Prompt

| 구성 요소 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|---------|---------------------|----------------------|
| 고정 요소 | 스켈레톤 밴드 4명 + 달 + 사이버펑크 도시 | chibi toy robot figure + screen-face + 헬멧 |
| 의상 | 단일 (`decorative metal straps`) | `[CHARACTER_OUTFIT]` / `[CHARACTER_OUTFIT_GIRL]` 이중 |
| 색조 | `neon magenta and deep black` (고정) | `[CHARACTER_COLOR]` (가변) |
| 금지 문구 | 동일 (text/watermarks/logos) | 동일 |

---

### 03~06 악기별 이미지 프롬프트

| 구성 요소 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|---------|---------------------|----------------------|
| 캐릭터 명칭 | `skeleton vocalist`, `skeleton guitarist` 등 | `AI Boy/AI Girl chibi toy robot figure` |
| 의상 | `decorative metal straps, concert costume` | `[CHARACTER_OUTFIT] / [CHARACTER_OUTFIT_GIRL]` |
| 소품 | `decorative concert microphone`, `guitar` 고정 | `[CHARACTER_PROP]` (장르별 가변) |
| 색조 | `neon magenta` 고정 | `[CHARACTER_COLOR]` 가변 |
| 보컬 동작 | 없음 | `[CHARACTER_VOCAL_ACTION]` 플레이스홀더 |

---

### 07 Stage Image Prompt

| 구성 요소 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|---------|---------------------|----------------------|
| 구도 | `4명 full band + 달 + 사이버펑크 도시` | `AI Boy/AI Girl chibi figure + [CHARACTER_CROWD]` |
| 무대 배경 | `dark ruined cyberpunk city stage` | 장르별 — 고정 배경 없음 |
| 색조 | `magenta lasers`, `epic live concert scale` | `[CHARACTER_COLOR] dominant color accent on stage lights` |
| 관중 | `massive crowd silhouettes raising hands` (고정) | `[CHARACTER_CROWD]` (장르별 가변) |

---

### 08 Atmosphere Image Prompt

| 구성 요소 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|---------|---------------------|----------------------|
| 실루엣 | `The same skeleton band silhouetted against the massive glowing neon magenta moon` | `AI Boy/AI Girl chibi toy robot figure silhouetted against the stage light source` |
| 배경 | `huge dark ruined cyberpunk city skyline` | **제거됨** |
| 달 | `massive glowing neon magenta moon` | **제거됨** |
| 색조 | `magenta and black cinematic color palette` (고정) | `[CHARACTER_COLOR] dominant color mood` (가변) |
| 결론 | 사이버펑크 특정 분위기 고정 | 장르에 따라 완전히 다른 분위기 |

---

### 09 Video Motion Prompts

| 구성 요소 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|---------|---------------------|----------------------|
| 헤더 참조 | `band/world identity defined by [REFERENCE_DIR]` | `character consistency: AI Boy/AI Girl chibi toy robot figure identity` |
| 보컬 묘사 | `the skeleton vocalist sings with high-energy rock intensity` | `AI Boy/AI Girl [CHARACTER_VOCAL]` + `[CHARACTER_VOCAL_ACTION]` |
| 기타 묘사 | `the skeleton guitarist performs a high-energy guitar solo` | `AI Boy/AI Girl [CHARACTER_GUITAR]` |
| 베이스 묘사 | `the skeleton bassist plays a heavy bass line` | `AI Boy/AI Girl [CHARACTER_BASS]` |
| 드럼 묘사 | `the skeleton drummer strikes the drums intensely` | `AI Boy/AI Girl [CHARACTER_DRUM]` |
| 무대 묘사 | `the full skeleton band performs on stage` | `AI Boy/AI Girl [CHARACTER_STAGE]` |
| 분위기 묘사 | `skeleton band silhouettes` + `massive neon magenta moon` | `AI Boy/AI Girl silhouette remains still or shifts subtly` |
| 조명 색 | `magenta concert lights` (고정) | `[CHARACTER_COLOR] concert lights` (가변) |
| Variant 구조 | A/B/C 전부 포함 | MVP/Full 모드에 따라 `production_config.json`으로 필터링 |

---

## 3. 텍스트 금지 구문 적용 현황

> AI 이미지·영상 생성기가 프롬프트 없이 글자·숫자·로고를 삽입하는 것을 방지한다.

### 이미지 프롬프트 (01~08)

| 파일 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|------|---------------------|----------------------|
| 01 | ✅ `Do not add any text, letters, numbers, watermarks, logos, or UI overlays to the image.` | ✅ 동일 |
| 02 | ✅ | ✅ |
| 03 | ✅ | ✅ |
| 04 | ✅ | ✅ |
| 05 | ✅ | ✅ |
| 06 | ✅ | ✅ |
| 07 | ✅ | ✅ |
| 08 | ✅ | ✅ |

### 영상 프롬프트 (09) — 메인 6개 섹션

| 섹션 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|------|---------------------|----------------------|
| 보컬 영상 | ✅ 헤더 내 포함 | ✅ 헤더 내 포함 |
| 기타 영상 | ✅ | ✅ |
| 베이스 영상 | ✅ | ✅ |
| 드럼 영상 | ✅ | ✅ |
| 전체 무대 영상 | ✅ | ✅ |
| 분위기 영상 | ✅ | ✅ |

### 영상 프롬프트 (09) — Motion Variants 섹션

Variant 블록을 Kling에서 단독 제출할 때는 메인 섹션의 안전 지시가 포함되지 않는다.
**두 파일 모두 2026-06-09 패치**: Motion Variants 헤더에 안전 지시 주의 문구 추가.

```
> 단독 제출 시 반드시 첫 줄에 다음을 추가하세요:
> Do not add text, watermarks, logos, or UI overlays to the video.
```

---

## 4. 09 Video Motion Prompts 개선 사항 (2026-06-09)

### ai_img_video_prompt 수정 내용

| 위치 | 수정 전 | 수정 후 | 이유 |
|------|---------|---------|------|
| 베이스 영상 | `steady skeletal nod on the beat` | `steady stylized nod on the beat` | "skeletal" — 일부 영상 AI 콘텐츠 필터 오탐 위험 |
| 드럼 영상 | `skull nodding on the main beat` | `head nodding on the main beat` | "skull" — 콘텐츠 필터 오탐 위험 |
| 하단 편집 가이드 | `and crowd variants` | `and atmosphere variants` | 오기 — 해당 섹션명은 "atmosphere" |
| Motion Variants 헤더 | (없음) | 단독 제출 시 안전 지시 추가 주의문 | Variant 단독 사용 시 텍스트 금지 안내 누락 |

### ai_img_video_aiBoygirl 수정 내용

| 위치 | 수정 전 | 수정 후 | 이유 |
|------|---------|---------|------|
| Motion Variants 헤더 | (없음) | 단독 제출 시 안전 지시 추가 주의문 | Variant 단독 사용 시 텍스트 금지 안내 누락 |

---

## 5. 주요 설계 차이 요약

### 고정 vs 가변 전략

```
ai_img_video_prompt:
  배경(달·도시)    → 고정
  색조(마젠타+블랙) → 고정
  캐릭터 외형       → 고정
  장르 에너지       → 가변 (roles, lighting 등)

ai_img_video_aiBoygirl:
  캐릭터 구조       → 고정 (chibi robot figure 형태)
  색조              → 가변 [CHARACTER_COLOR]
  의상              → 가변 [CHARACTER_OUTFIT / OUTFIT_GIRL]
  소품              → 가변 [CHARACTER_PROP]
  배경 분위기       → 가변 (장르 프로파일 기반)
```

### 영상 Variant 필터링

```
ai_img_video_prompt:
  항상 A/B/C 전부 출력

ai_img_video_aiBoygirl:
  production_config.json 의 mode 설정에 따라 자동 필터
  mvp:  vocal A/B, guitar A, bass 없음, drum 없음, stage A/B, atmosphere A/B
  full: 전체 A/B/C
```

### 캐릭터 성별 구분

```
ai_img_video_prompt:
  성별 구분 없음 — 단일 캐릭터 외형

ai_img_video_aiBoygirl:
  AI Boy: [CHARACTER_OUTFIT]
  AI Girl: [CHARACTER_OUTFIT_GIRL]
  → 모든 이미지/영상 템플릿에 두 가지 의상 동시 명시
```

---

## 6. AI 오류 방지 체크리스트

두 프로젝트의 프롬프트가 AI 모델에서 오류 없이 처리되기 위한 현재 상태:

| 항목 | ai_img_video_prompt | ai_img_video_aiBoygirl |
|------|---------------------|----------------------|
| 텍스트·워터마크 금지 (이미지 01~08) | ✅ 전 파일 적용 | ✅ 전 파일 적용 |
| 텍스트·워터마크 금지 (영상 09 메인 섹션) | ✅ 전 섹션 헤더 | ✅ 전 섹션 헤더 |
| 텍스트·워터마크 금지 (Motion Variants) | ⚠️ 주의문 추가 (2026-06-09) | ⚠️ 주의문 추가 (2026-06-09) |
| 콘텐츠 필터 오탐 키워드 제거 | ✅ skull→head, skeletal→stylized | ✅ 스켈레톤 표현 없음 |
| 플레이스홀더 잔여 검증 | ✅ `validate_song_folder()` | ✅ `validate_song_folder()` |
| 과도하게 긴 단일 지시문 | ⚠️ 09 헤더 1문장 280자 | ⚠️ 09 헤더 1문장 280자 |
| 상충하는 지시 없음 | ✅ | ✅ |

> ⚠️ 09 헤더 280자 주의: Kling 등 일부 영상 AI는 프롬프트 총 길이 제한이 있다.
> 제한에 걸릴 경우 identity 부분을 `Preserve character identity from uploaded image.`로 단축한 뒤
> 나머지 동작·카메라 지시만 남기는 축약 버전 사용을 권장한다.
