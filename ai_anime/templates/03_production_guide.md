# [SONG_TITLE] — Production Guide

## Song Metadata

| Field | Value |
|---|---|
| Title | [SONG_TITLE] |
| Genre | [GENRE] |
| BPM | [BPM] |
| Tempo | [TEMPO] |
| Mood | [MOOD] |
| Emotion | [EMOTION] |
| Stage Energy | [STAGE_ENERGY] |
| Genre Profile | [GENRE_PROFILE] |

## Song Motif
[SONG_MOTIF]

## Color Palette
[COLOR_RULE]
- Main Color: [COLOR_MAIN]
- Base: [COLOR_BASE]

## Lighting Style
[LIGHTING_STYLE]

## Character

[CHARACTER]

| Feature | Description |
|---|---|
| Hair | [CHARACTER_HAIR] |
| Outfit | [CHARACTER_OUTFIT] |
| Prop | [CHARACTER_PROP] |
| Silhouette | [CHARACTER_SILHOUETTE] |

## Genre Profile Direction
- **Narrative:** [NARRATIVE_DIRECTION]
- **Character:** [CHARACTER_DIRECTION]
- **World:** [GENRE_WORLD]

---

## Production Workflow

### Step 1 — Character Model Sheet (`00_character_sheet.md`)
1. Open `00_character_sheet.md`.
2. Choose one platform (Nijijourney recommended).
3. Generate the 8-view character turnaround model sheet.
4. Select the best result and save it locally.
5. **Do not proceed to scene images until the model sheet is approved.**

### Step 2 — Scene Image Generation (`01_image_prompts.md`)
1. Open `01_image_prompts.md`.
2. For each scene ([SCENE_RANGE]):
   - Attach the approved character model sheet as the reference image.
   - Use the platform-specific prompt for that scene.
   - Generate and select the best image.
3. Work through scenes in order to maintain visual continuity.

### Step 3 — Scene Video Generation (`02_video_prompts.md`)
1. Open `02_video_prompts.md`.
2. For each scene ([SCENE_RANGE]):
   - Attach the approved scene image as the **primary** reference.
   - Attach the character model sheet as secondary reference if supported.
   - Use the platform-specific prompt for that scene.
3. Generate a 5–10 second clip per scene.

### Step 4 — Final Edit
1. Import all [SCENE_COUNT] scene clips in order.
2. Trim to match BPM and song section lengths.
3. Apply [TRANSITION_LANGUAGE] between scenes.
4. Add the original Suno audio track.
5. Export as 1920×1080 or 1080×1920 depending on target platform.

---

## Identity Consistency Rules

- Use the same character face, hair, outfit, and prop across all scenes.
- Only pose, expression, setting, and action change per scene.
- Primary accent color remains: [COLOR_MAIN].
- Anime cinematic styling throughout — never live-action realism.
- No text, watermarks, or logos in any generated image or video.
- Safe, non-violent animated content in all scenes.
