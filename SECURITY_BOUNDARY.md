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

- 음악·영상 도구 5개는 외부 API 키 없이 동작한다. `music_insight_studio`의 선택 의존성(`librosa`, `basic-pitch`)도 로컬 Python 패키지이며 원격 API가 아니다.
- `CareerDiff`만 `OPENAI_API_KEY`와 `OPENAI_MODEL`을 선택적으로 사용한다. 앱 환경변수에 키가 없으면 Git에서 제외된 `../ai_agent/keyinfo/keys.env`의 `OPENAI_API_KEY`만 서버 메모리로 읽는다. 어느 경로든 키를 사용할 수 있으면 채용공고와 이력서가 외부 API로 전송되므로 화면에서 이를 알려야 한다.
- 실제 키는 `CareerDiff/app/.env.local`, 프로세스 환경변수 또는 위 개인 공유 파일로만 주입하고 로그, 검증 JSON, trace에 기록하지 않는다.

## Career Data Boundary

- `CareerDiff`의 이력서와 채용공고는 개인·지원 관련 데이터로 취급한다.
- 실제 후보자 데이터는 소스 fixture로 커밋하지 않으며 `CareerDiff/data/`의 런타임 파일도 Git 추적 대상이 아니다.
- 적합도 점수와 보완 제안은 의사결정 지원 정보이며 채용·탈락을 자동 결정하지 않는다. 실제 지원 또는 채용 판단에는 사람 검토가 필요하다.

## Media Boundary

- `ai_img_video_prompt_capcut` may read local audio, subtitle, LRC, markdown, and clip files.
- Local media files should be treated as user-owned working assets, not source code.
- Large or private media should not be committed unless explicitly classified as public fixture material.

## Audio Analysis Boundary

- `music_insight_studio` may read local user-uploaded audio files (WAV/MP3/FLAC/OGG/AIFF) for analysis only.
- Raw audio and generated reports must not be persisted beyond the local session unless explicitly documented (see its own `docs/commercial/DATA_RETENTION.md`).
- Must not upload user audio to any external service — analysis stays local.

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
- Confirm `CareerDiff/data/`와 실제 이력서·채용공고가 추적되지 않았고, OpenAI 사용 화면이 외부 전송 사실을 고지한다.
