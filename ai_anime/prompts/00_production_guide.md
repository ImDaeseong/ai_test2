# Production Guide - 그래서 더 좋아

## Core Idea

곡마다 다른 캐릭터와 세계관을 만들되, 한 곡 내부에서는 같은 기준 시트, 같은 팔레트, 같은 소품/실루엣/제목 잠금 문구를 반복 사용합니다.

## Identity

- Primary subject: youthful restless protagonist with bright alert eyes and energetic asymmetrical styling, male-presenting one human lead character, telephone-signal-pop anime vocalist tracing a distant phone-line pulse through the chorus, clean modular silhouette with one tactile imperfection or analog detail, face structure: soft rectangular face, low brows, deep-set eyes, song-specific face detail: soft round eyes with a tiny catchlight shaped like the song motif, signature gesture: keeps one hand near the collar when holding back words
- Signature prop: thin ajaeng-string bracelet shimmering on chorus pulses
- Accent detail: electric blue remains dominant, but the prop and gestures follow this song motif: a forced smile reflected as a split ambient expression. This exact face structure, body silhouette, hair shape, outfit category, accessory, and gesture set belong only to '그래서 더 좋아'. Treat this as a completely new lead character for this song, not a costume variation of another protagonist
- Palette: {'base': 'deep indigo and midnight space backgrounds', 'main_color': 'electric blue', 'shadow_color': 'dark sapphire and deep indigo shadow', 'secondary_light': 'subtle soft rose shimmer secondary glow', 'highlight': 'cool pearl and icy white highlights', 'rule': 'limited-color anime palette: electric blue dominant, dark shadows, near-black backgrounds, subtle soft rose shimmer secondary glow, cool pearl and icy white highlights'}

## Folder Workflow

1. `image_prompts`에서 기준 시트와 4종 씬 이미지를 만듭니다.
2. `video_prompts`에서 씬 전체 연출을 확인합니다.
3. `video_clip_prompts`에서 클립별 영상 생성 프롬프트를 사용합니다.
4. 생성된 클립을 씬 순서대로 편집합니다.

## Quality Check

- 이미지 4종 모두 같은 캐릭터/피사체 정체성을 유지하는지 확인합니다.
- 영상 프롬프트에 `Preserve the character design` 또는 주 피사체 보존 문구가 있는지 확인합니다.
- 다른 노래 제목이나 이전 곡의 캐릭터 설명이 섞여 있으면 재생성합니다.
- `detail` 샷은 사람이 없어도 소품, 색, motif가 같은 곡 전용이어야 합니다.

Scenes: 10
