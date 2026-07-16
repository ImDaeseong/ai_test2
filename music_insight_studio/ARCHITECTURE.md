# Architecture

## Actual Stack

- Python 3.11+ (verified against 3.14)
- Web MVP: stdlib `http.server` (`ThreadingHTTPServer`/`BaseHTTPRequestHandler`) — no Flask/FastAPI dependency
- Markdown/JSON report renderer (no HTML templating engine)

### Dependency Table

Every package below is technically optional in the sense that the app never crashes without it — each one is behind a lazy `try`/`except` import, and the code path just falls back to a lighter estimate. The two `requirements*.txt` files exist to separate "install this, it's the normal setup" from "install this only if you want a specific accuracy upgrade":

| Package | Lives in | When present | When absent |
|---|---|---|---|
| `numpy`, `soundfile` | `requirements.txt` | Full DSP analysis path (BPM/key/frequency bands/etc.) | stdlib WAV-only fallback; MP3/FLAC analysis unavailable |
| `pyloudnorm` | `requirements.txt` | LUFS is measured and included in the report | LUFS field is omitted from the report, everything else still runs |
| `librosa` | `requirements-optional.txt` tier 1 (wired into code, uncommented) | `AudioAnalyzer` prefers `librosa.beat.beat_track` for BPM — see "Librosa BPM Provider" below. Installed and verified in this `.venv` (`0.11.0`). | Falls back to the built-in spectral-flux onset estimator, then RMS envelope |
| `basic-pitch` | `requirements-optional.txt` tier 1 (wired into code, commented out) | `ScoreTranscriber` prefers real audio-to-MIDI note events — see "Notation Export Boundary" below | Falls back to a local numpy/soundfile autocorrelation melody guide, then a section-energy chart. Not installed in this `.venv`, so this is the current default. |
| `music21`, `demucs`, `pedalboard` | `requirements-optional.txt` tier 2 (commented out, not referenced anywhere in `app/`) | N/A — no code calls these yet | No effect either way; listed only as future/deferred candidates (ROADMAP Phase 5, later score post-processing) |

`requirements.txt` is what `README.md`'s Setup section installs by default. `requirements-optional.txt` is never installed automatically; a user has to run `pip install -r requirements-optional.txt` deliberately to pick up `librosa` (and, if uncommented, `basic-pitch`).

### Library Selection Policy

This is a description of the pattern the Dependency Table above already follows in practice, written down so future additions stay consistent:

1. Prefer the stdlib first; only add a dependency when stdlib genuinely can't do the job (audio decoding, real DSP).
2. A new dependency must degrade gracefully — lazy `try`/`except` import with a working fallback, never a hard crash when it's missing.
3. Heavier/model-download dependencies (e.g. `basic-pitch`) stay commented out in `requirements-optional.txt` until there's a concrete reason to install them locally; they must not become required for the MVP path.
4. A dependency with zero code integration (tier 2: `music21`, `demucs`, `pedalboard`) stays commented out and undocumented as "in use" until it's actually wired into `app/` — don't claim a library is used just because it's listed as a future candidate.
5. `SECURITY_BOUNDARY.md`'s External Dependency Rules still apply: no heavy model download or GPU requirement without explicit user approval.

## Folder Structure

```text
ai_test3/
├─ README.md
├─ SPEC.md
├─ ARCHITECTURE.md
├─ ACCEPTANCE_CRITERIA.md
├─ SECURITY_BOUNDARY.md
├─ VERIFICATION.md
├─ HOLD_CONDITIONS.md
├─ ROADMAP.md
├─ docs/                      (see docs/README.md for full read order)
│  ├─ evaluation_criteria.md
│  ├─ scoring_model.md
│  ├─ composer_criteria.md / lyricist_criteria.md / producer_criteria.md
│  ├─ mixing_criteria.md / mastering_criteria.md / ai_music_criteria.md
│  ├─ market_release_criteria.md
│  ├─ audio_analysis_scope.md / ai_music_analysis_scope.md / marketability_scoring.md
│  ├─ reference_sources.md
│  ├─ commercial/    (COMMERCIAL_READINESS.md, PRODUCTION_ARCHITECTURE.md, WEB_SECURITY.md, DATA_RETENTION.md, COPYRIGHT_POLICY.md)
│  └─ features/      (score_generation.md)
├─ app/
│  ├─ core/        (dataclasses/enums only; models.py)
│  ├─ analyzers/    (audio.py: audio features incl. optional librosa BPM provider; text.py: prompt/lyrics parsing)
│  ├─ scoring/      (criteria-file-linked scoring classes: base.py, engine.py, rubric.py, specialists.py)
│  ├─ reports/      (markdown.py, korean_markdown.py, json_report.py rendering)
│  ├─ notation/     (musicxml_writer.py: lead-sheet export; transcription.py: ScoreTranscriber optional basic-pitch/heuristic melody guide; see Notation Export Boundary)
│  ├─ services/     (analysis_service.py: orchestration used by cli and web)
│  ├─ cli/
│  └─ web/          (server.py: stdlib http.server, calls AnalysisService only; security.py: upload extension/signature/size validation)
│     └─ static/vendor/  (vendored browser JS, e.g. OpenSheetMusicDisplay; no CDN calls)
├─ tests/
├─ uploads/    (gitignored, runtime only)
└─ outputs/    (gitignored, runtime only)
```

## Components

### Audio Analyzer

Extracts measurable audio features:

- duration
- BPM
- estimated key
- RMS mean/std
- dynamic range
- spectral centroid/rolloff
- frequency band energy
- LUFS when dependency is available

### Prompt and Lyrics Analyzer

Parses optional Suno prompt or lyrics:

- title, artist, genre, mood, instruments
- section names: Intro, Verse, Pre-Chorus, Chorus, Bridge, Outro
- chord tags and chord progression
- lyric density and repetition clues

### Scoring Engine

Converts raw analysis into practical scores:

- mix balance
- vocal clarity proxy
- low/high frequency balance
- chorus impact
- AI naturalness checklist
- platform fit: YouTube, Spotify, Apple Music, Melon, Shorts/Reels/TikTok

### Report Generator

Builds Markdown/HTML reports:

- executive summary
- technical stats
- strengths and weaknesses
- release recommendation
- improvement checklist

## Data Flow

1. User uploads audio file.
2. File validator checks extension, size, path safety, and readability.
3. Audio analyzer extracts measurable features.
4. Optional prompt/lyrics analyzer extracts structure metadata.
5. Scoring engine evaluates mix, AI feel, and marketability.
6. Report generator writes Markdown/HTML/JSON to `outputs/`.

## Risk Areas

- BPM/Key detection can be wrong for tempo changes, rubato, noisy mixes, or ambiguous harmony.
- Genre and artist similarity cannot be fully reliable without ML models or external metadata.
- AI naturalness is a subjective proxy unless trained classifiers are introduced.
- Demucs and advanced mastering dependencies are heavy and should be optional.

## CLI MVP Code Boundary

The first CLI MVP keeps UI and domain logic separated:

- `app/core`: dataclasses and enums only.
- `app/analyzers`: measurable feature extraction and text/prompt parsing.
- `app/scoring`: criteria-file-linked scoring classes.
- `app/reports`: Markdown/JSON rendering only.
- `app/services`: orchestration layer used by CLI and future web UI.
- `app/cli`: argument parsing and output paths only.
- `app/web`: calls `AnalysisService` and must not contain analysis/scoring logic. It may serve vendored, build-free static JS assets (`app/web/static/vendor/`) for browser-side rendering (e.g. MusicXML notation); this is UI presentation, not analysis logic. Upload validation (extension allowlist, file-signature sniffing, size limits) lives in `app/web/security.py`, kept separate from `server.py`'s routing/rendering so the security policy has one file to review.

## Optional DSP Analysis Boundary

`AudioAnalyzer` has two paths:

- stdlib WAV fallback: always available, used by the CLI MVP and tests.
- optional DSP path: enabled when `numpy` and `soundfile` are installed. See the Dependency Table above for what each package adds and its fallback when absent.

MP3/FLAC decoding is intentionally dependent on optional audio packages. Without them, the analyzer returns a warning rather than crashing.


## Commercial Architecture Note

The current stdlib `http.server` web layer is local-only. A commercial service should introduce a production API layer, upload service, analysis job queue, background worker, object storage, database, auth/quota checks, and privacy-safe report delivery. See `docs/commercial/PRODUCTION_ARCHITECTURE.md`.

## Notation Export Boundary

Score generation must be a separate export module, not part of the scoring engine. The initial feasible version is a MusicXML lead sheet/session chart based on current analysis metadata. Full melody/chord transcription is a later feature that requires additional pitch, onset, beat, and chord evidence. See `docs/features/score_generation.md`.

Section count scales with track duration (`AudioAnalyzer.TARGET_SECTION_SECONDS = 15s`, clamped to 4-24 sections) instead of a fixed count, so the chart's resolution matches the song's length. The Web MVP renders this MusicXML using a locally vendored renderer (`app/web/static/vendor/opensheetmusicdisplay.min.js`); no CDN request is made at runtime, consistent with `SECURITY_BOUNDARY.md`'s local-first policy.

## 2026-07-12 Result Links Open in a New Tab

The result screen's `JSON` and `악보 MusicXML` links previously behaved inconsistently: `JSON` navigated the current tab away from the analysis result, while `악보 MusicXML` expanded an inline panel below the result on the same page. Both now open in a new browser tab (`target="_blank" rel="noopener"`), keeping the original result screen intact.

`악보 MusicXML` now points to a standalone `/score?src=<report-url>` page (`render_score_page`) instead of toggling an inline `.score-view` panel; that page loads the vendored OSMD renderer and fetches/renders the MusicXML on page load. The `src` query value is validated by `parse_report_path` (shared with the existing `/reports/<12-hex-id>/<allowlisted filename>` handler) and rejected with `404` unless it resolves to exactly `analysis_lead_sheet.musicxml` under a well-formed report id — confirmed both by a unit test (`test_score_route_rejects_paths_outside_reports_allowlist`) and a live browser request to `/score?src=/etc/passwd`, which returned `404`.

## 2026-07-12 BPM Estimation Update

BPM estimation now uses a lightweight beat-tracking proxy in the optional DSP path:

- Downsample/limit audio for local performance.
- Build a spectral-flux onset envelope from short FFT frames.
- Score autocorrelation tempo candidates with harmonic support and a mild tempo prior.
- Fall back to RMS-envelope tempo estimation when onset confidence is low.

This is still not a full beat tracker with downbeat, meter, and tempo-change handling, but it reduces coarse BPM grid locking on mastered WAV files.

## 2026-07-12 Librosa BPM Provider

Added an optional `librosa.beat.beat_track` provider ahead of the built-in spectral-flux estimator:

1. `librosa.beat.beat_track` (used when `librosa` is installed and returns confidence >= 0.05)
2. Built-in spectral-flux onset autocorrelation (previous section)
3. RMS-envelope fallback

`librosa` is documented as optional in `requirements-optional.txt`; the analyzer imports it lazily inside a try/except so its absence never breaks analysis. Verified directly (not just via the unit test's fake-librosa patch): a synthetic 120 BPM click track returns a different BPM/confidence pair with `librosa` importable (117.45 BPM, confidence 0.877) versus with the `librosa` import blocked (120.08 BPM, confidence 0.836), confirming both code paths actually execute.

Re-running the 38-file real mastered WAV batch (local verification set, not checked into this repository) with `librosa` installed (0.11.0) gives **15 unique BPM values across 38 files, 0 errors, BPM confidence 0.83-0.90**. The previously recorded "12 to 37 unique BPM" figure for this update was not reproducible on re-verification and has been removed; 15/38 is the measured value as of this update.
