# Acceptance Criteria

## MVP Completion Criteria

- A user can place or upload one MP3/WAV/FLAC file for analysis.
- The system returns a Markdown or HTML report without crashing.
- The report includes duration, BPM, Key, energy, dynamic range, and frequency balance where dependencies allow.
- The report includes Korean explanations for mix quality, strengths, weaknesses, and release-readiness.
- The report clearly labels estimates as estimates.
- Invalid files produce a controlled error message.
- Outputs are written under `outputs/` only.
- Upload handling does not allow path traversal.

## Quality Criteria

- Core analysis functions have focused tests using synthetic or small fixture audio.
- Scoring rules are documented and deterministic.
- Optional dependencies fail gracefully.
- The system works without external network access for MVP.

## Done Definition

MVP is done when the verification commands in `VERIFICATION.md` pass and no HOLD condition in `HOLD_CONDITIONS.md` remains active.
