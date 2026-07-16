from __future__ import annotations

import importlib.util
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NoteEvent:
    start_sec: float
    end_sec: float
    midi: int
    velocity: int = 80
    confidence: float = 0.0

    @property
    def pitch_name(self) -> tuple[str, int, int]:
        steps = ["C", "C", "D", "D", "E", "F", "F", "G", "G", "A", "A", "B"]
        alters = [0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0]
        pitch_class = self.midi % 12
        octave = (self.midi // 12) - 1
        return steps[pitch_class], alters[pitch_class], octave


@dataclass(frozen=True)
class TranscriptionResult:
    provider: str
    note_events: list[NoteEvent] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def available(self) -> bool:
        return bool(self.note_events)


class ScoreTranscriber:
    """Optional audio-to-note transcription boundary for score export.

    This deliberately stays outside AudioAnalyzer and ScoringEngine. Analysis can
    remain deterministic and lightweight while score export may use heavier MIR
    dependencies when they are installed.
    """

    MIN_MIDI = 36
    MAX_MIDI = 84
    # Worst-case event count for the heuristic path is MAX_HEURISTIC_SECONDS / min hop
    # (0.12s, see _estimate_note_events), ~750 events; 400 covers realistic 60-180bpm
    # tempos (hop floor of 0.5s-0.33s) without truncating before the analysis window ends.
    MAX_EVENTS = 400
    HEURISTIC_SAMPLE_RATE = 11025
    MAX_HEURISTIC_SECONDS = 90.0

    def transcribe(self, audio_path: Path | str, bpm: float = 0.0) -> TranscriptionResult:
        path = Path(audio_path)
        basic_pitch = self._try_basic_pitch(path)
        if basic_pitch.available:
            return basic_pitch
        heuristic = self._try_heuristic_melody(path, bpm)
        if basic_pitch.warnings:
            return TranscriptionResult(
                provider=heuristic.provider,
                note_events=heuristic.note_events,
                warnings=[*basic_pitch.warnings, *heuristic.warnings],
            )
        return heuristic

    def _try_basic_pitch(self, path: Path) -> TranscriptionResult:
        if not importlib.util.find_spec("basic_pitch"):
            return TranscriptionResult("heuristic", warnings=["basic-pitch is not installed; using local heuristic melody guide."])
        try:  # pragma: no cover - optional dependency path
            from basic_pitch.inference import predict

            _, _, note_events = predict(str(path))
            parsed = self._parse_basic_pitch_events(note_events)
            return TranscriptionResult("basic-pitch", parsed[: self.MAX_EVENTS], [] if parsed else ["basic-pitch returned no note events."])
        except Exception as exc:  # pragma: no cover - model/runtime dependent
            return TranscriptionResult("heuristic", warnings=[f"basic-pitch transcription failed; using local heuristic melody guide: {exc}"])

    def _parse_basic_pitch_events(self, note_events: Any) -> list[NoteEvent]:
        parsed: list[NoteEvent] = []
        for event in note_events or []:
            start = end = pitch = confidence = None
            if isinstance(event, dict):
                start = event.get("start_time_s", event.get("start_time", event.get("start")))
                end = event.get("end_time_s", event.get("end_time", event.get("end")))
                pitch = event.get("pitch_midi", event.get("midi_pitch", event.get("pitch")))
                confidence = event.get("confidence", event.get("amplitude", 0.8))
            elif isinstance(event, (list, tuple)) and len(event) >= 3:
                start, end, pitch = event[0], event[1], event[2]
                confidence = event[3] if len(event) >= 4 and isinstance(event[3], (int, float)) else 0.8
            try:
                midi = int(round(float(pitch)))
                start_sec = max(0.0, float(start))
                end_sec = max(start_sec + 0.05, float(end))
                if self.MIN_MIDI <= midi <= self.MAX_MIDI:
                    parsed.append(NoteEvent(start_sec, end_sec, midi, 90, max(0.0, min(1.0, float(confidence or 0.0)))))
            except (TypeError, ValueError):
                continue
        return self._merge_repeated_notes(parsed)

    def _try_heuristic_melody(self, path: Path, bpm: float) -> TranscriptionResult:
        if not (importlib.util.find_spec("numpy") and importlib.util.find_spec("soundfile")):
            return TranscriptionResult("none", warnings=["Score melody guide requires numpy and soundfile, or install basic-pitch for stronger transcription."])
        try:
            import numpy as np
            import soundfile as sf

            data, sample_rate = sf.read(str(path), always_2d=True)
            y = np.mean(data, axis=1).astype(float)
            if y.size == 0 or sample_rate <= 0:
                return TranscriptionResult("heuristic", warnings=["Audio file has no samples for melody guide."])
            total_duration_sec = y.size / sample_rate
            y, effective_rate, limited = self._prepare_heuristic_audio(y, int(sample_rate), np)
            note_events = self._estimate_note_events(y, effective_rate, float(bpm or 0.0), np)
            covered_sec = note_events[-1].end_sec if note_events else 0.0
            warnings = ["Heuristic melody guide only; install basic-pitch for polyphonic audio-to-MIDI transcription."]
            if limited or covered_sec < total_duration_sec - 1.0:
                warnings.append(
                    f"Heuristic melody guide covers 0:00-{covered_sec:.0f}s of {total_duration_sec:.0f}s total "
                    f"(~{self.MAX_HEURISTIC_SECONDS:.0f}s local-performance cap); the rest of the track is not "
                    "transcribed. Install basic-pitch or run a background job for full-track coverage."
                )
            return TranscriptionResult("heuristic", note_events, warnings if note_events else ["No stable pitched events found for melody guide."])
        except Exception as exc:  # pragma: no cover - codec/environment dependent
            return TranscriptionResult("none", warnings=[f"Heuristic melody guide failed: {exc}"])

    def _prepare_heuristic_audio(self, y: Any, sample_rate: int, np: Any) -> tuple[Any, int, bool]:
        max_samples = int(self.MAX_HEURISTIC_SECONDS * sample_rate)
        limited = bool(y.size > max_samples)
        if limited:
            y = y[:max_samples]
        if sample_rate <= self.HEURISTIC_SAMPLE_RATE:
            return y, sample_rate, limited
        target_len = max(1, int(y.size * self.HEURISTIC_SAMPLE_RATE / sample_rate))
        indices = np.linspace(0, y.size - 1, target_len).astype(int)
        return y[indices], self.HEURISTIC_SAMPLE_RATE, True

    def _estimate_note_events(self, y: Any, sample_rate: int, bpm: float, np: Any) -> list[NoteEvent]:
        quarter_sec = 60.0 / bpm if bpm and bpm > 20 else 0.5
        window_sec = max(0.18, min(0.5, quarter_sec))
        hop_sec = max(0.12, min(0.5, quarter_sec))
        window = max(256, int(window_sec * sample_rate))
        hop = max(128, int(hop_sec * sample_rate))
        max_abs = float(np.max(np.abs(y))) if y.size else 0.0
        if max_abs <= 1e-8:
            return []
        energy_gate = max(0.01, max_abs * 0.04)
        events: list[NoteEvent] = []
        for start in range(0, max(1, len(y) - window), hop):
            chunk = y[start:start + window]
            rms = float(np.sqrt(np.mean(chunk * chunk))) if chunk.size else 0.0
            if rms < energy_gate:
                continue
            freq, confidence = self._estimate_f0_autocorr(chunk, sample_rate, np)
            if freq <= 0 or confidence < 0.22:
                continue
            midi = int(round(69 + 12 * math.log2(freq / 440.0)))
            if self.MIN_MIDI <= midi <= self.MAX_MIDI:
                events.append(NoteEvent(start / sample_rate, min(len(y), start + hop) / sample_rate, midi, 72, confidence))
        return self._merge_repeated_notes(events)[: self.MAX_EVENTS]

    @staticmethod
    def _estimate_f0_autocorr(chunk: Any, sample_rate: int, np: Any) -> tuple[float, float]:
        chunk = chunk - float(np.mean(chunk))
        if float(np.max(np.abs(chunk))) <= 1e-9:
            return 0.0, 0.0
        chunk = chunk * np.hanning(len(chunk))
        fft_size = 1 << (2 * len(chunk) - 1).bit_length()
        spectrum = np.fft.rfft(chunk, fft_size)
        corr = np.fft.irfft(spectrum * np.conj(spectrum), fft_size)[: len(chunk)]
        if not corr.size or corr[0] <= 1e-12:
            return 0.0, 0.0
        min_freq, max_freq = 80.0, 1000.0
        min_lag = max(1, int(sample_rate / max_freq))
        max_lag = min(len(corr) - 1, int(sample_rate / min_freq))
        if max_lag <= min_lag:
            return 0.0, 0.0
        search = corr[min_lag:max_lag + 1]
        best = int(np.argmax(search)) + min_lag
        confidence = float(corr[best] / (corr[0] + 1e-12))
        return float(sample_rate / best), max(0.0, min(1.0, confidence))

    @staticmethod
    def _merge_repeated_notes(events: list[NoteEvent]) -> list[NoteEvent]:
        if not events:
            return []
        ordered = sorted(events, key=lambda item: item.start_sec)
        merged: list[NoteEvent] = []
        current = ordered[0]
        for event in ordered[1:]:
            if event.midi == current.midi and event.start_sec <= current.end_sec + 0.08:
                current = NoteEvent(current.start_sec, max(current.end_sec, event.end_sec), current.midi, max(current.velocity, event.velocity), max(current.confidence, event.confidence))
            else:
                merged.append(current)
                current = event
        merged.append(current)
        return merged

