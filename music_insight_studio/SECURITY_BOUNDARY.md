# Security Boundary

## Local-First Policy

MVP analysis runs locally. Audio files, prompts, and reports must not be sent to external services unless the user explicitly enables an integration.

## Sensitive Data Rules

Do not store:

- API keys
- tokens
- passwords
- private company data
- customer data
- internal server addresses
- unpublished business identifiers

## File Handling Rules

- Accept only intended audio extensions: `.mp3`, `.wav`, `.flac`, optionally `.m4a` later.
- Normalize uploaded filenames to safe names.
- Prevent `..`, absolute path injection, and overwrite of unrelated files.
- Store temporary inputs in `uploads/` and generated outputs in `outputs/`.
- Add a retention policy before long-term storage is implemented.

## External Dependency Rules

- Heavy models such as Demucs are optional.
- Any dependency download must be explicit.
- External LLM analysis must require user-provided credentials and explicit opt-in.

## Copyright and Ethics

- The tool may compare broad stylistic traits, but must not claim to clone a living artist.
- The tool should frame artist similarity as high-level reference language, not impersonation guidance.
- The tool must not promise platform performance or revenue.
