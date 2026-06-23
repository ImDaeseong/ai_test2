# Output Prompt Structures

This document records how `ai_multi_agent` reads prompt outputs from the four sibling projects and where it saves execution results.

Workspace root:

```text
[project-root]/   ← the folder where you cloned the repository
```

Shared API settings:

```text
[project-root]/.env   ← place your API keys here (see .env.example)
```

`OPENROUTER_API_KEY` is required for text prompt execution. `OPENAI_API_KEY` is required only for automatic MV image generation.

## 1. Hermes MV

Source project:

```text
ai_img_video_prompt\output\<song title>\
```

Observed source files:

```text
00_prompt_overview.md
01_master_style_prompt.md
02_style_lock_prompt.md
03_vocal_image_prompt.md
04_guitar_image_prompt.md
05_bass_image_prompt.md
06_drum_image_prompt.md
07_stage_image_prompt.md
08_crowd_image_prompt.md
09_video_motion_prompts.md
README.md
```

Execution unit:

```text
01_vocal  -> 03_vocal_image_prompt.md  + "보컬 영상" section from 09_video_motion_prompts.md
02_guitar -> 04_guitar_image_prompt.md + "기타 영상" section
03_bass   -> 05_bass_image_prompt.md   + "베이스 영상" section
04_drum   -> 06_drum_image_prompt.md   + "드럼 영상" section
05_stage  -> 07_stage_image_prompt.md  + "전체 무대 영상" section
06_crowd  -> 08_crowd_image_prompt.md  + "관객 영상" section
```

Managed result folder:

```text
ai_multi_agent\output\mv\<song title>\parts\<part>\
  image_prompt.md
  video_prompt.md
  image.png
  manifest.json
  status.json
```

Web page and batch file:

```text
web_app_mv.py          port 5200
실행_web_mv.bat
```

Notes:

- Hermes is part-based, not a simple sequential GPT prompt runner.
- Image generation uses OpenAI image API when `OPENAI_API_KEY` exists.
- Video prompts are extracted from headings inside `09_video_motion_prompts.md`.
- The MV page shows all 6 parts and supports generating a specific part, not only the next part.

## 2. Story

Source project:

```text
ai_story\output\<project name>\
```

Observed structure:

```text
state.json
설정집.md
chapters\
  ch001_GPT_프롬프트.md
  ch002_GPT_프롬프트.md
  ...
```

State fields used:

```text
title
total_chapters
current_chapter
```

Execution unit:

```text
chapters\chNNN_GPT_프롬프트.md
```

Managed result folder:

```text
ai_multi_agent\output\story\<project name>\chapters\
  ch001_GPT_출력.md
  ch002_GPT_출력.md
  ...
```

Web page and batch file:

```text
web_app_story.py       port 5400
실행_web_story.bat
```

Notes:

- Story uses three-digit chapter numbers: `ch001`, not `ch01`.
- Progress in `ai_multi_agent` is based on saved managed output files, not only the original `state.json`.
- The Story page shows every chapter prompt and supports running a selected chapter prompt.

## 3. Scenario

Source project:

```text
ai_Scenario\output\<project name>\
```

Observed structure:

```text
state.json
설정집.md
scenes\
  씬001_GPT_프롬프트.md
  씬002_GPT_프롬프트.md
  ...
```

State fields used:

```text
title
total_scenes
current_scene
```

Execution unit:

```text
scenes\씬NNN_GPT_프롬프트.md
```

Managed result folder:

```text
ai_multi_agent\output\scenario\<project name>\scenes\
  씬001_GPT_출력.md
  씬002_GPT_출력.md
  ...
```

Web page and batch file:

```text
web_app_scenario.py    port 5300
실행_web_scenario.bat
```

Notes:

- Scenario uses three-digit scene numbers: `씬001`.
- Like Story, progress is determined by managed output files under `ai_multi_agent\output`.
- The Scenario page shows every scene prompt and supports running a selected scene prompt.

## 4. Anime

Source project:

```text
ai_anime\output\<song title>\
```

Observed structure:

```text
00_image_generation_guide.md
00_output_folder_guide.md
00_production_guide.md
00_prompt_to_video_workflow.md
character_reference_prompt.md
image_prompts\
  00_character_turnaround_model_sheet.md
  scene_01_intro_action.md
  scene_01_intro_detail.md
  scene_01_intro_emotion.md
  scene_01_intro_wide.md
  ...
video_prompts\
  scene_01_intro.md
  scene_02_verse.md
  ...
video_clip_prompts\
  scene_01_intro_clip_01.md
  scene_01_intro_clip_02.md
  ...
  timeline_plan.md
```

Prompt groups reflected in the Anime web page:

```text
reference:
  00_prompt_to_video_workflow.md
  character_reference_prompt.md
  image_prompts\00_character_turnaround_model_sheet.md

image:
  image_prompts\scene_*_wide.md
  image_prompts\scene_*_action.md
  image_prompts\scene_*_emotion.md
  image_prompts\scene_*_detail.md

video:
  video_prompts\scene_*.md

clip:
  video_clip_prompts\scene_*_clip_*.md
```

Managed result folder:

```text
ai_multi_agent\output\anime\<song title>\
  00_prompt_to_video_workflow_result.md
  character_reference_prompt_result.md
  image_prompts\scene_01_intro_action_result.md
  video_prompts\scene_01_intro_result.md
  video_clip_prompts\scene_01_intro_clip_01_result.md
```

Web page and batch file:

```text
web_app_anime.py       port 5500
실행_web_anime.bat
```

Notes:

- Anime is grouped by production stage.
- The web page now exposes group progress and allows selecting a specific group.
- `timeline_plan.md` is treated as a reference plan, not a direct execution prompt.
- The Anime page shows every prompt in the selected group and supports running a selected prompt file.

## 5. Webtoon

Source project:

```text
ai-webtoon\output\<song title>\
```

Observed structure:

```text
00_style_reference.md
00_prompt_overview.md
01_storyboard.md
panels\
  panel_001_intro_wide.md
  panel_002_intro_silhouette.md
  panel_NNN_[section]_[type].md
  ...
```

Each panel file contains prompts for four platforms:
- GPT Image (gpt-image-2) — used for automatic generation via OpenAI API
- Nijijourney (--niji 7)
- FLUX.1
- Gemini / Imagen 3

Execution unit:

```text
panels\panel_NNN_[section]_[type].md  (one panel = one image)
```

Panel file naming:

```text
panel_[NNN]_[section]_[type].md
  NNN:     zero-padded panel number
  section: intro / verse / prechorus / chorus / bridge / outro / instrumental
  type:    wide / medium / closeup / silhouette / detail / crowd / atmosphere
```

Managed result folder:

```text
ai_multi_agent\output\webtoon\<song title>\panels\<panel_stem>\
  image_prompt.md     ← extracted GPT Image prompt
  image.png           ← generated image (if OPENAI_API_KEY set)
  status.json         ← {"done": true/false}
```

Web page and batch file:

```text
web_app_webtoon.py     port 5600
실행_web_webtoon.bat
```

Notes:

- Webtoon is panel-based. Each panel generates one image (no video prompt).
- Panel count varies by song BPM and section structure (typically 25–50 panels per song).
- Image generation uses GPT Image prompt extracted from `## GPT Image` block in each panel file.
- Reference images are read from `ai-webtoon\reference\` (7 PNG files: band, vocalist, guitarist, bassist, stage, drummer, crowd).
- The webtoon page shows all panels with done/image status and supports running a selected panel or the next pending panel.
- `01_storyboard.md` is shown as a reference plan, not a direct execution prompt.

## Execution Policy

The output folders contain many prompts. `ai_multi_agent` must not treat a project as a single prompt.

Current web behavior:

```text
Hermes MV:  show all 6 part prompts; run next part or selected part.
Story:      show all chNNN prompts; run next chapter or selected chapter.
Scenario:   show all 씬NNN prompts; run next scene or selected scene.
Anime:      show prompts by reference/image/video/clip group; run next prompt or selected prompt.
```

API calls are still executed one at a time. This is intentional so a long project does not spend API credits unexpectedly and so failed prompts can be retried cleanly.

## Current Web Surface

The project intentionally has four project-specific web pages and four project-specific batch files:

```text
web_app_anime.py       실행_web_anime.bat
web_app_mv.py          실행_web_mv.bat
web_app_scenario.py    실행_web_scenario.bat
web_app_story.py       실행_web_story.bat
```

There is no central hub page. The project model is one web page per source project.
