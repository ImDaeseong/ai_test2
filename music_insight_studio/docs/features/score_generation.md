# Feature: Score Generation and Notation Export

## Purpose

Allow Music Insight Studio to export a basic score or lead sheet from analysis data when enough musical evidence exists.

## Feasibility decision

Current analysis data can support only a limited score export:

- estimated BPM,
- estimated key,
- duration,
- section energy labels,
- optional lyrics/prompt sections.

This is not enough for accurate full transcription. Accurate melody/chord/drum notation requires pitch tracking, onset detection, chord recognition, beat tracking, and possibly source separation.

## MVP notation scope

Start with a simple lead sheet / session chart export, not full automatic transcription.

MVP output:

- MusicXML file.
- Optional MIDI click/guide file later.
- Title, estimated key, estimated tempo.
- Section structure from `section_energies`, sized to track duration (~15s per section, clamped to 4-24 sections; see `AudioAnalyzer.TARGET_SECTION_SECONDS`) rather than a fixed count.
- Section labels and energy annotations.
- Optional lyric section names if provided.
- Confidence notes explaining that melody/chords are not fully transcribed.
- Web MVP renders this MusicXML in-browser on demand (locally vendored OpenSheetMusicDisplay, no CDN), alongside the raw MusicXML text.

## Later advanced notation scope

Later features may add:

- beat grid,
- onset events,
- vocal melody approximation,
- chord estimation,
- bass rhythm hints,
- drum pattern approximation,
- MusicXML + MIDI + PDF export.

## Required data model additions later

```python
@dataclass
class NotationEvent:
    start_sec: float
    duration_sec: float
    pitch: str | None
    velocity: float | None
    label: str
    confidence: str

@dataclass
class ScoreExport:
    title: str
    estimated_key: str
    estimated_bpm: float
    format: str
    path: str
    confidence: str
    limitations: list[str]
```

## Suggested module boundary

```text
app/
  notation/
    __init__.py
    lead_sheet.py
    musicxml_writer.py
    midi_writer.py       (later)
    transcription.py     (later)
```

## Suggested libraries

### MVP

- Standard library XML writer for simple MusicXML.
- No heavy dependency required.

### Later

- `music21` for richer MusicXML manipulation.
- `pretty_midi` or `mido` for MIDI export.
- `librosa` for onset/beat/chroma features.
- `basic-pitch` or similar model only after explicit dependency approval.

## Rules

- Do not claim the generated score is exact transcription.
- Every score export must include confidence and limitations.
- Keep notation export separate from scoring logic.
- Do not require heavy ML dependencies for the MVP lead-sheet export.

## Verification checks

- Given an `EvaluationReport`, MusicXML export includes title, tempo, key, and section labels.
- Export does not crash when BPM/key are unknown.
- Export includes limitation notes.
- Existing analysis tests still pass.

## 2026-07-12 Implementation Update

The score export now has a separate transcription boundary:

- `ScoreTranscriber` first tries optional `basic-pitch` note events when the package is installed.
- If `basic-pitch` is unavailable, it uses a local numpy/soundfile autocorrelation melody guide for rough pitched notes.
- If no pitched events are reliable, `LeadSheetMusicXmlWriter` falls back to the older section-energy session chart.
- The MusicXML output clearly labels generated notes as a transcription guide, not publication-ready sheet music.

Library decision:

- `basic-pitch` is the preferred first upgrade for audio-to-MIDI because it is built for automatic music transcription and returns note events/MIDI from audio.
- `music21` is the preferred later score post-processing layer for quantization, notation cleanup, and richer MusicXML export.
- `librosa.pyin` remains useful for monophonic pitch tracking, but it is weaker than a dedicated AMT model for polyphonic songs.

Acceptance boundary:

- For a full mixed/mastered WAV, automatic notation is still approximate.
- Commercial UI must call this output `악보 가이드` or `transcription guide`, not `정확한 악보`.
- A future production worker should cache model loading and run long audio transcription as a background job.

## 2026-07-17 Verification Fix: heuristic coverage was truncated below its own stated window

Verification against 44 real mastered WAVs (`C:\Users\cs930\Downloads\wav_마스터링\작업완료`, 1:30-3:20 each)
found `ScoreTranscriber`'s heuristic path stopped collecting note events at `MAX_EVENTS=96` well before
reaching the `MAX_HEURISTIC_SECONDS=90` window it advertised in its own warning text — average coverage was
33% of track duration (min 23%, max 54%), while the score's warning claimed "first 90s" regardless.

Fix in `app/notation/transcription.py`:

- Raised `MAX_EVENTS` from 96 to 400 (sized for the worst-case event rate across realistic 60-180bpm hop
  intervals over the 90s window) and removed the redundant early `break` in `_estimate_note_events` — the
  loop was already bounded by the pre-truncated 90s audio buffer, so the count-based break only hurt coverage.
- The heuristic-path warning now reports the actual covered duration (`0:00-{covered}s of {total}s`) instead
  of a hardcoded "first 90s" claim, so it stays honest even if the window constant changes later.

Re-verification after the fix (same 44 files): average coverage rose to 48.5% (min 41%, max 59%), which now
matches the arithmetic of a 90s cap over ~150-200s tracks — i.e. coverage is limited only by the documented
window, not by a hidden secondary truncation.

Known tradeoff: isolated `ScoreTranscriber.transcribe()` time rose from ~0.35s to ~0.43s per file (warm,
same 44 files), because the loop no longer exits early within the 90s window. This is the real cost of
actually scanning the window the warning already claimed to scan, and it is small in absolute terms.

Correction (verified after an initial mis-measurement): a first pass wrongly attributed a ~2-3s-to-10.6s
per-file slowdown to this fix. Isolating `AnalysisService.analyze()` from `write_reports()` across 8 real
files showed `analyze()` (librosa-based BPM/LUFS/etc., untouched by this fix) alone averages ~9.4s/file,
while `write_reports()` (transcription + all four report writers) averages ~0.4s/file both before and after
this change. The multi-second-per-file cost is pre-existing `AudioAnalyzer` cost, unrelated to score
generation — do not re-attribute it to this fix again.

Extending `MAX_HEURISTIC_SECONDS` to cover full-length tracks synchronously was intentionally not done here
— it conflicts with the "background job" acceptance boundary above and would add real, proportional latency
to the (already small) transcription step. If full-track coverage is wanted, do it as the background-job
worker already called for, not as a bigger synchronous constant.
