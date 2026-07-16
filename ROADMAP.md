# ai_test2 Roadmap

## Phase 1 — Governance Documents

Goal: make the project safe to change.

- Add `SPEC.md`, `ARCHITECTURE.md`, `SECURITY_BOUNDARY.md`, `HOLD_CONDITIONS.md`, and `VERIFICATION.md`.
- Link them from README and CLAUDE.
- Re-run all existing tests.

## Phase 2 — Source/Data Layout Audit

Goal: separate source, examples, fixtures, generated output, and private working assets.

- Inventory `input/`, media files, references, templates, and outputs.
- Mark which files are source fixtures and which are private/working assets.
- Add `examples/` and `tests/fixtures/` conventions before moving files.
- Do not delete or move large working assets without human review.

## Phase 3 — Contract Documentation and Tests

Goal: protect cross-project behavior before refactoring.

- Document CapCut Editing Map format.
- Document LRC section label normalization.
- Document clip naming and fallback rules.
- Add contract tests for `09_video_motion_prompts.md -> ai_img_video_prompt_capcut`.

## Phase 4 — Module Extraction

Goal: reduce large script risk while preserving CLI compatibility.

Suggested extraction order:

1. `ai_img_video_prompt_capcut`: parsing and CapCut draft writer boundaries
2. `ai_anime`: prompt rendering and CapCut export split
3. `ai_img_video_aiBoygirl`: parser, profile selector, safety filter, validator split
4. `ai_multi_agent`: shared web/service helpers across 5 UIs — story/scenario extracted 2026-07-13 (`web_app_scaffold.py`); anime/mv/webtoon still pending (different domain models, larger effort)
5. `youtube_research`: already small; keep mostly as-is unless adding providers

`music_insight_studio` (added 2026-07-17) is out of scope for this phase — it already has `app/{analyzers,scoring,notation,reports,services,web,cli}/` module boundaries, not a single large script.

## Phase 5 — Documentation Refresh

Goal: make docs match real commands and evidence.

- Replace stale test counts with latest evidence.
- Add per-project `VERIFICATION.md` only where the project is actively changed.
- Keep root README short and move deep details into docs.

## Phase 6 — Optional Packaging

Goal: improve maintainability after behavior is stable.

- Consider `src/` packages per project.
- Consider shared small utilities only after file contracts are stable.
- Avoid central shared code that makes independent projects hard to run.
