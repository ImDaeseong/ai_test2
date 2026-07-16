# Web Security

## Current state

The local Web MVP accepts WAV/FLAC/MP3 uploads through stdlib `http.server`, saves files under `uploads/<request-id>/`, and writes reports under `outputs/web/<request-id>/`.

This is acceptable for local use only.

## Commercial requirements

### Upload validation

- Maximum file size.
- Maximum duration.
- Extension allowlist.
- MIME/content sniffing.
- Decode validation before analysis.
- Clear error messages.

### Storage safety

- Store uploads outside source tree in production.
- Use object storage or controlled temp directory.
- Never serve uploaded audio directly by arbitrary path.
- Use opaque IDs.
- Enforce ownership on every download.

### Abuse controls

- Rate limits by user/IP.
- Analysis quota by plan.
- Job timeout.
- Concurrent job limit.
- Retry limit.

### Response safety

- Escape all user-controlled content in HTML.
- Do not expose raw stack traces.
- Do not include local filesystem paths in user-facing errors.
- Do not log uploaded filenames if they may contain private data.

## MVP improvement candidates

- Add `MAX_UPLOAD_BYTES` constant.
- Reject empty and oversized requests before reading all body where possible.
- Add tests for oversized uploads.
- Add cleanup helper for old uploads/outputs.
- Rename local server documentation to make local-only status explicit.
