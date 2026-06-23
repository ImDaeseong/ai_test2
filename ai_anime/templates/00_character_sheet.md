# [SONG_TITLE] — Character Model Sheet

Generate this AI Boy/AI Girl chibi toy figure design sheet FIRST before any scene images.
Attach this design sheet as a reference when generating every scene image.

> **Character Base Reference:** `[CHARACTER_REFERENCE]` — 이 이미지를 업로드하여 캐릭터 스타일 기준으로 사용하세요. 모든 씬 생성 시 이 reference와 완성된 character sheet를 함께 첨부합니다.

**Song:** [SONG_TITLE] | **Genre Profile:** [GENRE_PROFILE] | **Character Direction:** [CHARACTER_DIRECTION]

---

## GPT Image (gpt-image-2 / OpenAI)

Create a 3D chibi toy figure design sheet for '[SONG_TITLE]'. Show the character in 8 views: front full-body, left side full-body, right side full-body, back full-body, three-quarter full-body, face close-up, prop close-up of [CHARACTER_PROP], and a gender/subject check label. Character: [CHARACTER]. Helmet: [CHARACTER_HAIR]. Outfit: [CHARACTER_OUTFIT]. Prop: [CHARACTER_PROP]. Silhouette: [CHARACTER_SILHOUETTE]. [COLOR_RULE]. 3D chibi toy figure design sheet, collectible toy aesthetic, smooth rounded 3D toy rendering, white or neutral background, no scene environment, no action pose.

Do not add any text, letters, numbers, watermarks, logos, or UI overlays to the image.

**Model:** `gpt-image-2` | **Quality:** `high` | **Size:** `1536x1024`
**필수 추가:** `Do not add any text, letters, numbers, watermarks, logos, or UI overlays to the image.`

> Use gpt-image-2 at quality='high' for the model sheet. Specify 'anime cel-shaded illustration, clean linework, white background' for the sheet layout. Generate the full turnaround before any scene work.

---

## Google Gemini (Imagen 3)

3D 치비 토이 피규어 디자인 시트. '[SONG_TITLE]' AI Boy/AI Girl 로봇 캐릭터. 8가지 뷰: 정면 전신, 왼쪽 측면, 오른쪽 측면, 후면 전신, 3/4 전신, 얼굴 클로즈업, [CHARACTER_PROP] 소품 클로즈업, 성별/유형 레이블. 캐릭터: [CHARACTER]. 헬멧: [CHARACTER_HAIR]. 의상: [CHARACTER_OUTFIT]. 실루엣: [CHARACTER_SILHOUETTE]. [COLOR_RULE]. 3D 치비 토이 피규어 스타일, 컬렉터블 토이 렌더링, 흰색 또는 중립 배경, 배경 장면 없음.

Do not add any text, letters, numbers, watermarks, logos, or UI overlays to the image.

**비율:** `16:9` 또는 `1:1` | **언어:** 한국어 프롬프트 직접 사용 가능

> 한국어 프롬프트로 직접 사용. 대화형 반복 편집으로 세부 수정 가능.

---

## Midjourney v7

3D chibi toy figure design sheet for '[SONG_TITLE]', 8 views: front full-body, left side, right side, back, three-quarter, face close-up, prop close-up of [CHARACTER_PROP], gender check label. [CHARACTER]. Helmet: [CHARACTER_HAIR]. Outfit: [CHARACTER_OUTFIT]. Silhouette: [CHARACTER_SILHOUETTE]. [COLOR_RULE]. 3D chibi toy figure, collectible toy aesthetic, smooth rounded 3D rendering, white background, no scene environment. --v 7 --ar 16:9 --s 300 --no watermark, text, letters, numbers, logo, UI overlay, signature

> For 3D chibi toy figure sheets, use --v 7 with 'collectible toy figure, smooth 3D rendering, white background' style anchors. Use --oref for character consistency across scenes.

---

## Nijijourney (--niji 7)

3D chibi toy figure design sheet for '[SONG_TITLE]', 8 views: front full-body, left side, right side, back, three-quarter, face close-up, prop close-up of [CHARACTER_PROP], gender check label. [CHARACTER]. Helmet: [CHARACTER_HAIR]. Outfit: [CHARACTER_OUTFIT]. Silhouette: [CHARACTER_SILHOUETTE]. [COLOR_RULE]. 3D chibi toy figure, collectible toy aesthetic, smooth rounded 3D rendering, white background, no scene environment. --niji 7 --ar 16:9 --s 250 --no watermark, text, logo, background scene, environment

> 3D 치비 토이 피규어 시트 플랫폼. --seed 고정 후 씬 전체 일관성 확보. collectible toy figure / 3D chibi toy turnaround reference 스타일 앵커 사용.

---

## FLUX.1 (Black Forest Labs)

[CHARACTER] displayed in a clean turnaround design sheet layout showing front, side, back, and three-quarter full-body views plus a face close-up and a prop close-up of [CHARACTER_PROP]. [CHARACTER_HAIR]. [CHARACTER_OUTFIT]. [CHARACTER_SILHOUETTE]. 3D chibi toy figure design sheet, collectible toy aesthetic, smooth rounded 3D toy rendering, clean white background, no scene environment, no action poses. No text, no watermarks, no logos.

**규칙:** 자연어 문장만 사용. 가중치 문법(`(word:1.5)`) 사용 금지. 40-75단어 유지.

> ComfyUI 사용 시: clip_l에 짧은 키워드, t5xxl에 상세 문장 분리 입력.

---

## Leonardo.Ai Phoenix 2.0

Create a 3D chibi toy figure design sheet for '[SONG_TITLE]'. Show the character in 8 views: front full-body, left side full-body, right side full-body, back full-body, three-quarter full-body, face close-up, prop close-up of [CHARACTER_PROP], and a gender/subject check label. Character: [CHARACTER]. Helmet: [CHARACTER_HAIR]. Outfit: [CHARACTER_OUTFIT]. Prop: [CHARACTER_PROP]. Silhouette: [CHARACTER_SILHOUETTE]. [COLOR_RULE]. 3D chibi toy figure design sheet, collectible toy aesthetic, smooth 3D toy rendering, white or neutral background.

Do not add any text, letters, numbers, watermarks, logos, or UI overlays to the image.

**Model:** Phoenix 2.0 | **Alchemy:** `on` | **Guidance:** `7` | **Style preset:** `CINEMATIC`
**캐릭터 일관성:** Character Reference 업로드 → Fixed Seed로 씬 전체 일관성 확보

> Phoenix 2.0 + Consistent Character Engine. 시트 생성 후 Character Reference로 등록하여 씬 전체에 사용.
