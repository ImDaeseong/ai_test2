# Documentation Index

Full map of every document in this project. `docs/README.md` covers the read order for the evaluation-criteria set specifically; this file covers everything, including the root-level product/process documents.

## Product and process (root)

- `README.md`: project entrance — purpose, stack, setup, usage, documentation map, development principles.
- `SPEC.md`: purpose, inputs/outputs, MVP feature list, reuse plan, evaluation-criteria source.
- `ARCHITECTURE.md`: actual stack, dependency table, folder structure, module boundaries, data flow, risk areas, dated implementation notes (BPM/transcription/link-behavior changes).
- `ACCEPTANCE_CRITERIA.md`: MVP completion criteria and "done" definition.
- `SECURITY_BOUNDARY.md`: local-first policy, sensitive-data rules, file-handling rules, copyright/ethics.
- `VERIFICATION.md`: verification loop, per-feature verification commands and expected signals, and the round-by-round Verification Log.
- `HOLD_CONDITIONS.md`: conditions that must stop implementation and require human review.
- `ROADMAP.md`: phase-by-phase status summary (0-7).

## Evaluation criteria (`docs/`)

See `docs/README.md` for the intended read order. Files: `evaluation_criteria.md`, `scoring_model.md`, `composer_criteria.md`, `lyricist_criteria.md`, `producer_criteria.md`, `mixing_criteria.md`, `mastering_criteria.md`, `ai_music_criteria.md`, `market_release_criteria.md`, `audio_analysis_scope.md`, `ai_music_analysis_scope.md`, `marketability_scoring.md`, `reference_sources.md`.

## Feature documents (`docs/features/`)

- `score_generation.md`: MusicXML export design, `ScoreTranscriber` provider chain, library decision (basic-pitch/music21/librosa.pyin), implementation update log.

## Commercial-readiness documents (`docs/commercial/`)

Read before converting the local MVP into a public or paid service; see `docs/commercial/README.md` for the rule that the current stdlib web layer is a local demo surface only.

- `COMMERCIAL_READINESS.md`: current commercial-readiness decision, blockers, hardening log.
- `PRODUCTION_ARCHITECTURE.md`: target service architecture for public/commercial deployment.
- `WEB_SECURITY.md`: upload, file handling, API, and abuse-control requirements.
- `DATA_RETENTION.md`: uploaded audio, generated reports, and deletion/export policy.
- `COPYRIGHT_POLICY.md`: copyright, artist-cloning, reference-track, and user-content policy.

## Maintenance rule

When a change touches more than one of these documents (e.g., a new optional library, a new module, a new web route), update all of them in the same round, not just the one that prompted the change — see the Verification Log in `VERIFICATION.md` for examples of rounds that caught stale cross-references this way.
