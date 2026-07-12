# ai_test2 Verification

## Verification Loop

[LOOP-START] goal: modernize ai_test2 structure without breaking existing tools / exit criteria: root governance docs exist, current tests pass, and next refactor steps are documented / max iterations: 3

## Progress Gates

- 0%: purpose and one-sentence use case are not defined.
- 20%: purpose, security boundary, acceptance criteria, verification commands, and HOLD conditions are defined.
- 40%: project analysis is complete and risks are identified.
- 60%: document changes are complete.
- 80%: verification commands or checks pass, and discovered issues are fixed or recorded.
- 90%: regression check, documentation, and handoff notes are complete.
- 100%: agreed verification criteria pass and no HOLD condition remains.

## Current Gate

100%: Root modernization documents were added, README/CLAUDE now link the governance docs, test temp-directory handling was corrected to respect explicit `--basetemp`, and all existing project tests pass. No HOLD condition remains.

## Required Commands

Run from each project directory:

```powershell
cd C:\Users\cs930\Desktop\ai_test2\ai_anime
python -m pytest tests_unit.py -q

cd C:\Users\cs930\Desktop\ai_test2\ai_img_video_aiBoygirl
python -m pytest -q

cd C:\Users\cs930\Desktop\ai_test2\ai_img_video_prompt_capcut
python -m pytest tests_unit.py -q

cd C:\Users\cs930\Desktop\ai_test2\ai_multi_agent
python -m pytest tests_unit.py -q

cd C:\Users\cs930\Desktop\ai_test2\youtube_research
python -m pytest tests_unit.py -q
```

## Document Checks

- `SPEC.md` contains the one-sentence use case and acceptance criteria.
- `ARCHITECTURE.md` defines current risks, target module boundaries, and file contracts.
- `SECURITY_BOUNDARY.md` defines allowed/disallowed data and API boundaries.
- `HOLD_CONDITIONS.md` defines security, scope, verification, and product HOLD conditions.
- `ROADMAP.md` defines the modernization sequence.
- `README.md` links to the governance documents.
- `CLAUDE.md` points agents to this verification file before implementation work.

## Latest Evidence

Verified 2026-07-13:

- Document scan found `One-Sentence Use Case`, `Target Module Boundaries`, `API Boundary`, `Security HOLD`, `Progress Gates`, `Phase 1`, `Governance Docs`, and `변경 전 확인 문서`.
- `python -m pytest tests_unit.py -q` in `ai_anime` -> dot output reached `[100%]` and exited 0.
- `python -m pytest -q --basetemp C:\Users\cs930\Desktop\hermes-agents\.tmp_ai_test2_pytest\aiBoygirl` in `ai_img_video_aiBoygirl` -> `337 passed, 1 warning in 4.67s`.
- `python -m pytest tests_unit.py -q --basetemp C:\Users\cs930\Desktop\hermes-agents\.tmp_ai_test2_pytest\prompt_capcut` in `ai_img_video_prompt_capcut` -> `65 passed, 1 warning in 0.38s`.
- `python -m pytest tests_unit.py -q --basetemp C:\Users\cs930\Desktop\hermes-agents\.tmp_ai_test2_pytest\multi_agent` in `ai_multi_agent` -> `27 passed, 1 warning in 0.22s`.
- `python -m pytest tests_unit.py -q --basetemp C:\Users\cs930\Desktop\hermes-agents\.tmp_ai_test2_pytest\youtube_research` in `youtube_research` -> `37 passed, 1 warning in 0.24s`.

The warning in the four `--basetemp` runs is a pytest cache warning from this sandbox user's inability to write `.pytest_cache` inside the `ai_test2` project folders. It does not affect test pass/fail. A real verification issue was found and fixed: four `conftest.py` files previously overwrote explicit `--basetemp` values with project-local `.pytest_tmp`, which failed when the project-local temp directories were owned by another Windows user. They now respect an explicit `--basetemp` and only fall back to project-local `.pytest_tmp` when none is provided.

## Exit Criteria

[LOOP-END] result: root governance docs added and all existing tests still pass / gate: 100%

