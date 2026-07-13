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

## Full Verification/Regression Loop (2026-07-13, second pass)

[LOOP-START] goal: re-verify Phase 1 completion end to end with regression probes, not just re-read the doc / exit criteria: all 5 suites pass fresh with visible evidence; README/VERIFICATION test-count claims match reality; SECURITY_BOUNDARY's required secrets scan and `.env` check are clean; ARCHITECTURE's file-size claims still hold; at least one regression probe proves a test suite isn't just passing vacuously / max iterations: 3

- All 5 suites re-run fresh, independent of the entry above: `ai_anime` 77 passed, `ai_img_video_aiBoygirl` 337 passed (3 independent runs, consistent), `ai_img_video_prompt_capcut` 65 passed, `ai_multi_agent` 27 passed, `youtube_research` 37 passed.
- **Found and fixed a real bug**: `ai_anime/conftest.py` reassigned `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, ...)` instead of reconfiguring the existing stream in place. This orphaned pytest's own `TerminalReporter` (which holds a reference to the original stdout object created before `pytest_configure` runs), silently swallowing the final summary line and all failure tracebacks — confirmed by injecting a real assertion failure: exit code correctly went to 1 and the `F` marker showed in the dot progress, but zero traceback/summary text was printed, which would make a real future test failure very hard to notice or debug. Fixed by using `stream.reconfigure(encoding="utf-8", errors="replace")` on the existing `sys.stdout`/`sys.stderr` objects instead of replacing them. Re-verified with the same injected failure: full traceback, assertion diff, and `1 failed, 76 passed in 0.54s` summary now all print correctly. Reverted the probe; clean run now also prints its summary line (`77 passed in 0.21s`) for the first time — this is why earlier verification rounds only had "dot output reached 100%, exit 0" as evidence instead of an actual passed count.
- **Found and fixed a stale doc claim**: root `README.md`'s "Running Tests" section said `ai_img_video_aiBoygirl` → `326 passed`, but three independent fresh runs all show `337 passed`. Cross-checked every other test-count reference in root and per-project docs (`grep -rn "passed"`) — all other current-state claims match reality; the only other mismatches found (`ai_img_video_aiBoygirl/CLAUDE.md`'s "목표: 336 passed" target, and various dated historical snapshots in `HANDOFF.md`/`PRE_DEPLOY.md`/`README.md` citing 285/334 as of specific past dates) are either already-exceeded targets or explicitly dated historical records, not current-state claims, so left as-is per this workspace's existing convention of not retroactively editing dated history.
- Security scan (`SECURITY_BOUNDARY.md`'s "Required Checks Before Release"): only 4 tracked `.env*` files exist, all named `.env.example` with placeholder-only content (`sk-or-...`, `sk-...` with literal ellipsis, or "no API keys needed" notes) — no real `.env` tracked, no real key-like strings found in tracked `.py`/`.md`/`.json`/`.txt` files (remaining grep matches were all code reading an env var by name or policy/doc text, not literal secrets).
- `ARCHITECTURE.md`'s cited large-script risk still holds: `ai_img_video_aiBoygirl/main.py` 1823 lines, `ai_img_video_prompt_capcut/main.py` 1334 lines, `ai_anime/main.py` 1323 lines — unchanged, no drift.
- Final `git status --short` in `ai_test2`: only `README.md` (count fix) and `ai_anime/conftest.py` (stdout fix) modified — nothing else touched.

[LOOP-END] result: PASS — one real bug found and fixed (swallowed test failure output), one stale doc claim found and fixed (aiBoygirl count) / gate: 100%

## ai_multi_agent — story/scenario web-UI de-duplication (2026-07-13, Phase 4 first slice)

[LOOP-START] goal: extract the near-duplicate web_app_story.py / web_app_scenario.py into a shared scaffold and add real test coverage for the extracted logic, without changing any user-visible behavior / exit criteria: rendered HTML byte-identical to pre-refactor output; all 4 routes behave identically; at least one regression probe proves the new tests aren't vacuous; full ai_multi_agent + sibling-project regression stays green; git diff scoped to ai_multi_agent only / max iterations: 3

**Finding that triggered this**: `web_app_story.py` and `web_app_scenario.py` (199 lines each) were near-identical copies — same function names (`_prompt_file`, `_prompt_items`, `_output_items`, `_list`, `_detail`), same 4 routes (`/`, `/api/projects`, `/api/detail/<name>`, `/api/run`), differing only in labels (chapter/scene, `ch{:03d}`/`씬{:03d}`), port (5400/5300), and accent color. All 27 existing tests covered only trivial helpers in `main.py`/`config.py` — zero coverage on either web app's actual routes, despite `ai_multi_agent` being the only project with real external API dependency.

**Change**: extracted `web_app_scaffold.py` (`PromptRunnerConfig` dataclass + `create_prompt_runner_app()` factory holding the one copy of all 4 routes and the HTML template). `web_app_story.py`/`web_app_scenario.py` are now 27-line wrappers that just supply their differing config values. Also applied the already-proven `stream.reconfigure()` fix (same as `ai_anime/conftest.py`, see the earlier round in this file) instead of each file's own broken `sys.stdout = io.TextIOWrapper(...)` reassignment.

**Verification (real commands, not recalled)**:
- Rendered `index()` HTML compared byte-for-byte against the pre-refactor version (extracted from `git show HEAD:...` and diffed programmatically) for both `web_app_story.py` and `web_app_scenario.py` — `IDENTICAL` for both.
- Added 12 new tests using Flask's `test_client()` (no real network calls): scaffold-level tests with a fully fake `managed_summary`/`managed_output_file` (isolated from `main.py`) covering index HTML, project listing, detail 404/200, `/api/run`'s missing-API-key/missing-project/success/`FileExistsError` branches; plus wiring tests confirming `web_app_story.py`/`web_app_scenario.py` still expose the right `PORT` and config-driven title strings.
- **Regression-probe proof**: temporarily broke `_detail()`'s `next_label` field to a hardcoded string — `test_existing_project_returns_detail_with_formatted_label` failed immediately with a clear diff; reverted, re-ran, 39/39 passed again.
- Full `ai_multi_agent` suite: `39 passed` (27 original + 12 new), up from 27.
- Full sibling regression (unrelated to this change, confirming no cross-project break): `ai_anime` 77, `ai_img_video_aiBoygirl` 337, `ai_img_video_prompt_capcut` 65, `youtube_research` 37 — all unchanged.
- `git status --short` in `ai_test2`: only `ai_multi_agent/tests_unit.py`, `ai_multi_agent/web_app_scenario.py`, `ai_multi_agent/web_app_story.py` (modified) and `ai_multi_agent/web_app_scaffold.py` (new) — no other project touched.
- Synced stale references: root `README.md`'s `ai_multi_agent` test count (27→39), `ARCHITECTURE.md`'s risk note (marks story/scenario as extracted, anime/mv/webtoon as still pending), `ROADMAP.md`'s Phase 4 item 4 (same).

**Not done**: `web_app_anime.py`/`web_app_mv.py`/`web_app_webtoon.py` still have their own duplicated-boilerplate risk and zero route-level test coverage — different domain models (panels/parts vs. prompts/chapters) mean they need their own scaffold design, not a mechanical reuse of this one. `main.py` (990 lines, CLI/agent orchestration) is also untouched.

[LOOP-END] result: PASS — real duplication removed with zero behavior change (byte-identical HTML, identical route semantics), test coverage added for previously-untested route logic, regression probe confirmed the new tests are load-bearing / gate: 100%

## ai_multi_agent — surface misconfigured project-root path instead of silent empty list (2026-07-13, same-day follow-up)

[LOOP-START] goal: fix a real usability gap found while manually testing the story/scenario refactor live, and add coverage for it / exit criteria: warning is returned by the API and rendered in the UI when the configured project folder is missing; regression probe proves the new test is load-bearing; full ai_multi_agent + sibling regression stays green; git diff scoped correctly / max iterations: 2

**Finding**: while manually verifying the story/scenario refactor in a real browser (see prior section), discovered `ai_multi_agent/.env` did not exist yet, and `STORY_ROOT`/`SCENARIO_ROOT` default to `ai_test2/ai_story` and `ai_test2/ai_Scenario` — folders that do not exist on this machine. The real project data lives under a sibling workspace, `ai_test1/ai_story` and `ai_test1/ai_Scenario`. This is not a code bug (`project_dirs()` already fails safe by returning `[]`), but the UI gave no visible signal that anything was misconfigured — a missing-folder typo and "genuinely zero projects yet" looked identical to the user.

**Fix**: `web_app_scaffold.py`'s `/api/projects` now checks `cfg.output_dir.exists()` and includes `"output_dir_exists"` plus a Korean `"warning"` message (naming the exact missing path) in the JSON response when it's false. The index page's `renderList()` now shows that warning in the sidebar instead of a generic "No projects" message. Created `ai_multi_agent/.env` locally (gitignored, not committed) with the correct `STORY_ROOT=../ai_test1/ai_story` / `SCENARIO_ROOT=../ai_test1/ai_Scenario`, and documented the gotcha + fix in `.env.example` and `ai_multi_agent/README.md`'s config section.

**Verification (real commands/browser, not recalled)**:
- Added 1 new test (`test_projects_warns_when_output_dir_missing`) plus assertions on the existing directory-exists test; full suite: `40 passed` (was 39).
- **Regression-probe proof**: hardcoded `output_dir_exists = True` — new test failed immediately (`assert True is False`); reverted, re-ran, 40/40 passed again.
- **Live browser proof**: temporarily moved the real `.env` aside, started `web_app_story.py`, confirmed via `curl` that `/api/projects` returned `"output_dir_exists":false` and the Korean warning naming the exact missing path, then opened it in an actual browser (Playwright) and confirmed the sidebar shows that warning instead of an empty list. Restored `.env`, restarted, confirmed normal project listing resumes (already verified live with real data in the prior section).
- Full regression after the fix: `ai_multi_agent` 40 passed, `ai_anime` 77, `ai_img_video_aiBoygirl` 337, `ai_img_video_prompt_capcut` 65, `youtube_research` 37 — all unchanged/green.
- `git status --short`: `ai_multi_agent/.env` correctly stays untracked (gitignored); only `.env.example`, `README.md`, `tests_unit.py`, `web_app_scaffold.py` show as the intended diff for this round, plus the story/scenario extraction files from the prior round.

[LOOP-END] result: PASS — a real silent-failure usability gap (found through actually using the app, not just reading code) is now self-diagnosing / gate: 100%

## Exit Criteria

[LOOP-END] result: root governance docs added and all existing tests still pass / gate: 100%

