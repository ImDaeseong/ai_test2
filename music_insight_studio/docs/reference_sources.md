# Reference Sources

## Analysis_music

Local sibling project outside this repository (path intentionally omitted).

Useful files:

- `app/analyzers/audio.py`: numpy/soundfile-based feature extraction, with stdlib WAV fallback
- `analyzer/suno_parser.py`: Suno prompt, lyrics, sections, chords parsing
- `generators/report_gen.py`: report structure and improvement suggestions
- `web/app.py`: Flask upload/report flow reference

Risks:

- Some Korean comments/output appear mojibake encoded and should be rewritten cleanly.
- Existing report generator mixes prompt analysis and audio analysis tightly.

## mp3_daw

Local sibling project outside this repository (path intentionally omitted).

Useful files:

- `engine.py`: BPM, Key, LUFS, frequency bands, waveform peaks, mastering, stem separation
- `main.go`: folder watcher and web server architecture reference
- `static/index.html`: simple UI reference

Risks:

- Advanced dependencies are heavy: demucs, pedalboard, pyloudnorm.
- Stem separation may download large model files.
- Mastering should be optional and clearly labeled as preview processing.

## Reuse Decision

For MVP, reuse concepts and small functions, but rebuild clean module boundaries in `ai_test3` instead of copying the full projects wholesale.

## ai_test1 and hermes-agents Evaluation References

`ai_test1` is the primary source for music-making criteria: lyric quality, hook design, Suno usage, production texture, genre routing, and mix/mastering concepts.

`hermes-agents/ai-workspace` is the primary source for user/channel criteria: `justaimusickr` direction, Hook/Mood/Visual/Channel Fit/Personal scoring, YouTube workflow, and broader strategic constraints.

The consolidated evaluation basis is now documented in `docs/evaluation_criteria.md`.

## Specialist Criteria First-Pass Docs

The 1차 implementation-readiness criteria set consists of:

- composer criteria: melody, harmony, rhythm, form, hook arrival
- lyricist criteria: hook line, syllable/pronunciation, modern language, scene-based emotion
- producer criteria: sound identity, groove, arrangement, vocal/space fit
- mixing criteria: frequency balance, vocal clarity, mud, fatigue, space, dynamics
- mastering criteria: LUFS, peak/clipping, platform readiness, over-compression risk
- AI music criteria: AI artifact, repetition, vocal naturalness, prompt-result fit
- market/release criteria: Hook/Mood/Visual/Channel Fit/Personal, A/B release priority
- scoring model: weights, mode adjustments, HOLD overrides

