# ai_test2 Security Boundary

## Data Classification

Allowed in repository:

- Public documentation
- Synthetic examples
- Template prompts
- Test fixtures that do not include private data
- `.env.example` files with variable names only

Not allowed in repository:

- Real API keys or tokens
- Passwords, private keys, cookies, session values
- Private customer/company data
- Internal-only server addresses or credentials
- Raw private resumes, private channel analytics, or non-public creator data

## API Boundary

- `ai_multi_agent` may use OpenRouter for text prompt execution when `OPENROUTER_API_KEY` is present.
- `ai_multi_agent` may use OpenAI image generation when `OPENAI_API_KEY` is present.
- Absence of API keys must be handled with a clear error or copy-only fallback.
- No other project should require external API keys.

## Media Boundary

- `ai_img_video_prompt_capcut` may read local audio, subtitle, LRC, markdown, and clip files.
- Local media files should be treated as user-owned working assets, not source code.
- Large or private media should not be committed unless explicitly classified as public fixture material.

## YouTube Research Boundary

- `youtube_research` may collect public metadata through yt-dlp.
- It must not download audio/video content as part of the benchmark workflow.
- It must not store private account data, cookies, or authenticated-only analytics.

## Prompt Safety Boundary

- Safety filters and risk maps may reduce policy-sensitive phrasing.
- Safety filters must not be removed to bypass platform policy.
- Prompt outputs must avoid artist/style cloning, real-person impersonation, and unsafe content instructions.

## Required Checks Before Release

- Search for key-like strings: `API_KEY`, `SECRET`, `TOKEN`, `PASSWORD`, `BEGIN PRIVATE KEY`, `sk-or-`, `sk-`.
- Confirm real `.env` files are not tracked.
- Run all project tests.
- For public release, manually review examples and media files for private or copyrighted material risk.
