# Scoring Model

이 문서는 `ai_test3` 1차 점수 산식의 기준이다. MVP 점수는 예측이 아니라 같은 기준으로 곡을 비교하기 위한 의사결정 보조값이다.

## Output Principle

리포트는 단일 총점보다 하위 점수와 근거를 먼저 보여준다. 총점은 선택적으로 계산하되, 항상 불확실성과 근거를 같이 표시한다.

## Default Score Groups

| Group | Weight | Criteria File |
|---|---:|---|
| Technical Audio | 15 | audio_analysis_scope.md, mixing_criteria.md |
| Composition | 15 | composer_criteria.md |
| Lyrics and Hook | 15 | lyricist_criteria.md |
| Production | 15 | producer_criteria.md |
| Mix and Master | 15 | mixing_criteria.md, mastering_criteria.md |
| AI Naturalness | 10 | ai_music_criteria.md |
| Market and Release Fit | 15 | market_release_criteria.md |

## Mode Adjustments

### Instrumental Mode

- Lyrics and Hook weight moves to Composition and Production.
- Vocal/lyric checks are marked `not applicable`.

### Non-AI Mode

- AI Naturalness is optional and does not penalize the track unless AI artifacts are detected or declared.
- Its weight can move to Production and Mix.

### AI Music Mode

- AI Naturalness is active.
- Prompt-result fit is evaluated when prompt text is provided.

### Comparison Mode

- Scores are used relatively.
- The report must explain why A should be released before B, not merely show higher total score.

## Evidence Requirements

Every score must include:

- numeric score or PASS/REVISE/HOLD
- source evidence: audio metric, lyrics, prompt, or user-provided target
- explanation in Korean
- uncertainty note
- next action

## Score Bands

- 85-100: strong candidate; publish or advance if no HOLD.
- 70-84: usable; revise small issues.
- 55-69: promising but needs focused revision.
- 40-54: concept exists but production/songwriting issues are significant.
- 0-39: not ready or evidence too weak.

## HOLD Overrides

Any HOLD condition overrides numeric score. A high score cannot cancel copyright, impersonation, sensitive data, unsafe upload, or unreadable-file risks.

## Anti-Claims

The system must not claim guaranteed views, revenue, playlist placement, platform success, or exact artist similarity.
## Duration Calibration

A readable file is not automatically release-ready. Very short fixtures or snippets can prove that decoding and analysis work, but they should not receive a release-ready overall score.

Current MVP duration gates:

- under 10 seconds: measurable snippet; cap most music/release scores and mark evidence as `duration_too_short_for_music_judgment`
- 10-29 seconds: demo-length evidence; useful for tone/quality checks but weak for composition and market fit
- 30+ seconds: reviewable music segment
- 90-240 seconds: default release-window bonus for streaming/general market fit

The fixture files in `tests/fixtures` are intentionally short, so their expected overall verdict is `REVISE` even when audio decoding, BPM, Key, LUFS, and frequency-band analysis all succeed.
## Release-Length Fixture

`tests/fixtures/release_90s.mp3` is a generated 90-second fixture used to verify the release-window path. It is still synthetic, so it does not prove hook quality or real market demand, but it confirms that duration gates, DSP metrics, and report generation work for a normal-length file.

Expected MVP signal for the fixture:

- CLI verdict: `PASS`
- score: around `77`
- evidence includes `duration_release_window`
- Lyrics and Hook may remain `REVISE` when lyrics are not provided

