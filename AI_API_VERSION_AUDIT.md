# AI/API and dependency audit — 2026-10-09

## Boundary summary

| Project | Actual AI/API boundary | Enforced decision |
|---|---|---|
| `ai_anime` | Generates prompt Markdown locally; an explicit opt-in smoke command can call OpenAI once | OpenAI target remains `gpt-image-2.5-sunburst`; retired Imagen 3 wording is replaced by `gemini-3.1-flash-image`; paid calls require both a key and `--confirm-paid-call` |
| `ai_img_video_aiBoygirl` | Generates provider-agnostic image/video prompts locally | No AI SDK or live API claim; identity, safety, and rights-boundary tests remain authoritative |
| `ai_img_video_prompt_capcut` | Consumes prompt/editing-map files and local media | No AI SDK; the `schema_version: 1.2` timeline contract remains the integration boundary |
| `youtube_research` | Calls the external `yt-dlp` executable for public metadata, not a generative AI API | Require a reviewed version, reject provider failures, and never flatten failure into an empty successful collection |
| `music_insight_studio` | Performs local numerical/audio analysis; “AI naturalness” is a disclosed heuristic | No AI SDK; update the tested numerical package floors while preserving local fallbacks |

## Provider and package evidence

- OpenAI image generation: `gpt-image-2.5-sunburst` is a supported image model. Checked against <https://developers.openai.com/api/reference/resources/images/methods/generate> on 2026-10-09.
- Google image generation: Google documents Imagen as a shut-down legacy family and lists current Gemini image models including `gemini-3.1-flash-image`. Checked against <https://ai.google.dev/gemini-api/docs/image-generation> on 2026-10-09.
- yt-dlp: latest stable observed was `2026.08.19`; `2026.02.21` fixed CVE-2026-26331. Checked against <https://github.com/yt-dlp/yt-dlp/releases> on 2026-10-09.
- Audio packages: PyPI latest releases observed were NumPy `2.5.3`, SoundFile `0.14.0`, pyloudnorm `0.2.0`, and librosa `1.0.0`. The current librosa line requires Python 3.12+. Checked on PyPI on 2026-10-09.
- Basic Pitch remains optional at `0.4.0`, supports only documented Python versions through 3.11, and is therefore not installed into the Python 3.14 verified environment.

## Verification

```powershell
python -m unittest tests.test_ai_api_contract
python -m unittest tests.test_repository_contract
```

Only `ai_anime/live_api_smoke.py` has a paid/live generative API path. It is excluded from ordinary batches, performs one low-quality 1024×1024 request, validates the returned image bytes in memory, and does not save the image. A live result must not be claimed unless that command actually returns PASS in the current session.

The 2026-10-09 verification run returned PASS for one `gpt-image-2.5-sunburst` request. It decoded 1,504,804 image bytes in memory, received a request ID, and saved no image. See `VERIFICATION.md` for the loop record.
