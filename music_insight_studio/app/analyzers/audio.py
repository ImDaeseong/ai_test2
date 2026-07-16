from __future__ import annotations

import importlib.util
import math
import wave
from array import array
from pathlib import Path
from typing import Any

from app.core import AudioFeatures, SectionEnergy


class AudioAnalyzer:
    """Extract measurable audio evidence without depending on UI code.

    The analyzer uses numpy+soundfile+pyloudnorm when available. If optional
    packages are unavailable or fail, WAV still works through the stdlib path.
    """

    SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".aiff", ".aif", ".aifc", ".caf"}
    TARGET_SECTION_SECONDS = 15.0
    MIN_SECTIONS = 4
    MAX_SECTIONS = 24
    BPM_ANALYSIS_RATE = 22050
    MAX_BPM_ANALYSIS_SECONDS = 180.0
    BPM_FFT_SIZE = 2048
    BPM_HOP_SIZE = 512
    BAND_RANGES = {
        "sub_bass_20_60hz": (20, 60),
        "bass_60_250hz": (60, 250),
        "low_mid_250_500hz": (250, 500),
        "mid_500_2khz": (500, 2000),
        "upper_mid_2k_4khz": (2000, 4000),
        "presence_4k_8khz": (4000, 8000),
        "brilliance_8k_16khz": (8000, 16000),
    }

    def analyze(self, audio_path: Path | str) -> AudioFeatures:
        path = Path(audio_path)
        extension = path.suffix.lower()
        base = AudioFeatures(False, str(path), path.name, extension)
        if not path.exists():
            base.error = f"Audio file not found: {path}"
            return base
        if extension not in self.SUPPORTED_EXTENSIONS:
            supported = ", ".join(sorted(self.SUPPORTED_EXTENSIONS))
            base.error = f"Unsupported audio extension: {extension}. Supported extensions: {supported}. M4A/AAC require conversion to WAV, MP3, or FLAC."
            return base
        if self._has_optional_dsp():
            try:
                return self._analyze_with_optional_dsp(path)
            except Exception as exc:  # pragma: no cover - codec/environment dependent
                if extension != ".wav":
                    base.error = f"Optional DSP analysis failed: {exc}"
                    return base
                fallback = self._analyze_wav_fallback(path)
                fallback.warnings.append(f"Optional DSP analysis failed; stdlib WAV fallback used: {exc}")
                return fallback
        if extension != ".wav":
            base.warnings.append("MP3/FLAC/OGG/AIFF/CAF decoding requires optional dependencies: numpy and soundfile.")
            return base
        return self._analyze_wav_fallback(path)

    @staticmethod
    def _has_optional_dsp() -> bool:
        return bool(importlib.util.find_spec("numpy") and importlib.util.find_spec("soundfile"))

    def _analyze_with_optional_dsp(self, path: Path) -> AudioFeatures:
        import numpy as np
        import soundfile as sf

        data, sample_rate = sf.read(str(path), always_2d=True)
        channels = int(data.shape[1]) if data.ndim == 2 else 1
        y = np.mean(data, axis=1).astype(float) if data.ndim == 2 else np.asarray(data, dtype=float)
        duration = float(len(y) / sample_rate) if sample_rate else 0.0
        rms_values = self._windowed_rms_np(y, sample_rate, np)
        rms_mean = float(np.mean(rms_values)) if rms_values.size else 0.0
        rms_std = float(np.std(rms_values)) if rms_values.size else 0.0
        peak = float(np.max(np.abs(y))) if y.size else 0.0
        spectrum, freqs = self._full_spectrum_np(y, sample_rate, np)
        lufs, lufs_warning = self._try_lufs(y, sample_rate)
        warnings = []
        if lufs_warning:
            warnings.append(lufs_warning)
        if peak >= 0.999:
            warnings.append("Peak reaches full scale; check clipping or limiter ceiling before release.")
        elif peak >= 0.98:
            warnings.append("Peak is very close to full scale; leave more mastering headroom.")
        bpm, bpm_confidence = self._estimate_bpm_from_audio_np(y, int(sample_rate), rms_values, np)
        return AudioFeatures(
            available=True,
            file_path=str(path),
            file_name=path.name,
            extension=path.suffix.lower(),
            duration_sec=duration,
            sample_rate=int(sample_rate),
            channels=channels,
            rms_mean=rms_mean,
            rms_std=rms_std,
            peak_amplitude=peak,
            dynamic_range_db=self._dynamic_range_db_np(rms_values, np),
            bpm=bpm,
            bpm_confidence=bpm_confidence,
            estimated_key=self._estimate_key_np(spectrum, freqs, np),
            lufs_integrated=lufs,
            frequency_bands=self._frequency_bands_np(spectrum, freqs, np),
            section_energies=self._section_energies_np(y, sample_rate, np),
            warnings=warnings,
        )

    @staticmethod
    def _windowed_rms_np(y: Any, sample_rate: int, np: Any) -> Any:
        if len(y) == 0:
            return np.asarray([], dtype=float)
        window = max(1, sample_rate // 20) if sample_rate else 1024
        values = []
        for start in range(0, len(y), window):
            chunk = y[start:start + window]
            if len(chunk):
                values.append(float(np.sqrt(np.mean(chunk * chunk))))
        return np.asarray(values, dtype=float)

    def _estimate_bpm_from_audio_np(self, y: Any, sample_rate: int, rms_values: Any, np: Any) -> tuple[float, float]:
        librosa_bpm, librosa_confidence = self._estimate_bpm_with_librosa_np(y, sample_rate, np)
        if librosa_bpm > 0.0 and librosa_confidence >= 0.05:
            return librosa_bpm, librosa_confidence
        prepared, effective_rate = self._prepare_bpm_audio_np(y, sample_rate, np)
        onset = self._spectral_flux_onset_np(prepared, effective_rate, np)
        bpm, confidence = self._estimate_bpm_from_envelope_np(onset, effective_rate / self.BPM_HOP_SIZE, np)
        if confidence >= 0.08:
            return bpm, confidence
        return self._estimate_bpm_from_envelope_np(rms_values, 20.0, np)

    def _estimate_bpm_with_librosa_np(self, y: Any, sample_rate: int, np: Any) -> tuple[float, float]:
        try:
            import librosa
        except Exception:
            return 0.0, 0.0
        try:
            prepared, effective_rate = self._prepare_bpm_audio_np(y, sample_rate, np)
            if len(prepared) < self.BPM_FFT_SIZE or effective_rate <= 0:
                return 0.0, 0.0
            tempo, beats = librosa.beat.beat_track(
                y=prepared,
                sr=effective_rate,
                hop_length=self.BPM_HOP_SIZE,
                start_bpm=120.0,
                units="frames",
            )
            tempo_array = np.asarray(tempo, dtype=float).reshape(-1)
            if tempo_array.size == 0:
                return 0.0, 0.0
            bpm = self._normalize_tempo_range(float(tempo_array[0]))
            beat_count = len(beats) if beats is not None else 0
            duration = len(prepared) / effective_rate
            expected_beats = max(1.0, duration * bpm / 60.0)
            coverage = min(1.0, beat_count / expected_beats)
            confidence = max(0.05, min(0.95, 0.35 + coverage * 0.55)) if beat_count >= 2 else 0.05
            return round(float(bpm), 2), confidence
        except Exception:
            return 0.0, 0.0
    def _prepare_bpm_audio_np(self, y: Any, sample_rate: int, np: Any) -> tuple[Any, int]:
        if len(y) == 0 or sample_rate <= 0:
            return y, sample_rate
        max_samples = int(self.MAX_BPM_ANALYSIS_SECONDS * sample_rate)
        if len(y) > max_samples:
            y = y[:max_samples]
        if sample_rate <= self.BPM_ANALYSIS_RATE:
            return y, sample_rate
        factor = max(1, int(round(sample_rate / self.BPM_ANALYSIS_RATE)))
        return y[::factor], int(round(sample_rate / factor))

    def _spectral_flux_onset_np(self, y: Any, sample_rate: int, np: Any) -> Any:
        if len(y) < self.BPM_FFT_SIZE or sample_rate <= 0:
            return np.asarray([], dtype=float)
        window = np.hanning(self.BPM_FFT_SIZE)
        previous = None
        values = []
        for start in range(0, len(y) - self.BPM_FFT_SIZE, self.BPM_HOP_SIZE):
            frame = y[start:start + self.BPM_FFT_SIZE]
            spectrum = np.abs(np.fft.rfft(frame * window))
            if previous is None:
                values.append(0.0)
            else:
                diff = spectrum - previous
                values.append(float(np.sum(diff[diff > 0.0])))
            previous = spectrum
        envelope = np.asarray(values, dtype=float)
        if envelope.size < 8:
            return envelope
        envelope = np.maximum(envelope - float(np.percentile(envelope, 35)), 0.0)
        peak = float(np.max(envelope))
        return envelope / peak if peak > 1e-12 else envelope

    @staticmethod
    def _estimate_bpm_from_envelope_np(envelope: Any, frame_rate: float, np: Any) -> tuple[float, float]:
        if envelope.size < 8 or frame_rate <= 0:
            return 0.0, 0.0
        envelope = envelope - float(np.mean(envelope))
        max_abs = float(np.max(np.abs(envelope)))
        if max_abs <= 1e-9:
            return 0.0, 0.0
        envelope = envelope / max_abs
        corr = np.correlate(envelope, envelope, mode="full")[len(envelope) - 1:]
        if corr.size < 4 or corr[0] <= 1e-12:
            return 0.0, 0.0
        min_bpm, max_bpm = 55.0, 210.0
        min_lag = max(1, int(frame_rate * 60.0 / max_bpm))
        max_lag = min(len(corr) - 1, int(frame_rate * 60.0 / min_bpm))
        if max_lag <= min_lag:
            return 0.0, 0.0
        corr_norm = corr / (float(corr[0]) + 1e-12)
        candidates = []
        for lag in range(min_lag, max_lag + 1):
            value = float(corr_norm[lag])
            left = float(corr_norm[lag - 1]) if lag > 0 else value
            right = float(corr_norm[lag + 1]) if lag + 1 < len(corr_norm) else value
            if value < left or value < right:
                continue
            bpm = 60.0 * frame_rate / lag
            harmonic = 0.0
            if lag * 2 < len(corr_norm):
                harmonic += 0.35 * max(0.0, float(corr_norm[lag * 2]))
            if lag // 2 >= min_lag:
                harmonic += 0.20 * max(0.0, float(corr_norm[lag // 2]))
            tempo_prior = 1.0 - min(0.35, abs(bpm - 120.0) / 240.0)
            candidates.append((value * tempo_prior + harmonic, lag, value))
        if not candidates:
            best_lag = int(np.argmax(corr_norm[min_lag:max_lag + 1])) + min_lag
            candidates = [(float(corr_norm[best_lag]), best_lag, float(corr_norm[best_lag]))]
        _, lag, raw_confidence = max(candidates, key=lambda item: item[0])
        lag = float(lag)
        lag_index = int(round(lag))
        if min_lag < lag_index < max_lag:
            left = float(corr_norm[lag_index - 1])
            center = float(corr_norm[lag_index])
            right = float(corr_norm[lag_index + 1])
            denom = left - 2.0 * center + right
            if abs(denom) > 1e-12:
                lag += 0.5 * (left - right) / denom
        bpm = 60.0 * frame_rate / lag if lag > 0 else 0.0
        bpm = AudioAnalyzer._normalize_tempo_range(bpm)
        return round(float(bpm), 2), max(0.0, min(1.0, raw_confidence))

    @staticmethod
    def _normalize_tempo_range(bpm: float) -> float:
        while bpm < 70.0 and bpm > 0.0:
            bpm *= 2.0
        while bpm > 180.0:
            bpm /= 2.0
        return bpm
    @staticmethod
    def _full_spectrum_np(y: Any, sample_rate: int, np: Any) -> tuple[Any, Any]:
        if len(y) == 0 or sample_rate <= 0:
            return np.asarray([], dtype=float), np.asarray([], dtype=float)
        spectrum = np.abs(np.fft.rfft(y * np.hanning(len(y))))
        freqs = np.fft.rfftfreq(len(y), d=1.0 / sample_rate)
        return spectrum, freqs

    @staticmethod
    def _estimate_key_np(spectrum: Any, freqs: Any, np: Any) -> str:
        if spectrum.size == 0:
            return "unknown"
        mask = (freqs >= 80.0) & (freqs <= 2000.0) & (spectrum > 0)
        if not mask.any():
            return "unknown"
        midi = np.round(69 + 12 * np.log2(freqs[mask] / 440.0)).astype(int)
        pitch_classes = np.zeros(12, dtype=float)
        np.add.at(pitch_classes, midi % 12, spectrum[mask])
        if not pitch_classes.any():
            return "unknown"
        names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return names[int(np.argmax(pitch_classes))]

    def _frequency_bands_np(self, spectrum: Any, freqs: Any, np: Any) -> dict[str, float]:
        if spectrum.size == 0:
            return {}
        bands = {}
        for name, (low, high) in self.BAND_RANGES.items():
            mask = (freqs >= low) & (freqs < high)
            bands[name] = round(float(np.mean(spectrum[mask])) if mask.any() else 0.0, 6)
        return bands

    @staticmethod
    def _try_lufs(y: Any, sample_rate: int) -> tuple[float | None, str]:
        if not importlib.util.find_spec("pyloudnorm"):
            return None, "LUFS analysis requires optional dependency: pyloudnorm."
        import pyloudnorm as pyln

        meter = pyln.Meter(sample_rate)
        return float(meter.integrated_loudness(y)), ""

    @staticmethod
    def _dynamic_range_db_np(rms: Any, np: Any) -> float:
        nonzero = rms[rms > 1e-9]
        if nonzero.size == 0:
            return 0.0
        low = float(np.percentile(nonzero, 10))
        high = float(np.percentile(nonzero, 95))
        if low <= 1e-9:
            low = float(np.min(nonzero))
        return float(20.0 * np.log10(high / low)) if low > 1e-9 and high > 0 else 0.0

    @classmethod
    def _section_count_for_duration(cls, duration_sec: float) -> int:
        estimated = round(duration_sec / cls.TARGET_SECTION_SECONDS)
        return max(cls.MIN_SECTIONS, min(cls.MAX_SECTIONS, estimated))

    def _section_energies_np(self, y: Any, sample_rate: int, np: Any) -> list[SectionEnergy]:
        if len(y) == 0 or sample_rate <= 0:
            return []
        total_sections = self._section_count_for_duration(len(y) / sample_rate)
        section_len = max(1, len(y) // total_sections)
        temp = []
        max_rms = 0.0
        for index in range(total_sections):
            start = index * section_len
            end = len(y) if index == total_sections - 1 else min(len(y), (index + 1) * section_len)
            chunk = y[start:end]
            rms = float(np.sqrt(np.mean(chunk * chunk))) if len(chunk) else 0.0
            max_rms = max(max_rms, rms)
            temp.append((index, start, end, rms))
        return self._section_energy_objects(temp, max_rms, sample_rate)

    def _analyze_wav_fallback(self, path: Path) -> AudioFeatures:
        try:
            with wave.open(str(path), "rb") as wav:
                channels = wav.getnchannels()
                sample_rate = wav.getframerate()
                sample_width = wav.getsampwidth()
                frames = wav.getnframes()
                raw = wav.readframes(frames)
        except wave.Error as exc:
            return AudioFeatures(False, str(path), path.name, path.suffix.lower(), error=f"Invalid WAV file: {exc}")
        except OSError as exc:
            return AudioFeatures(False, str(path), path.name, path.suffix.lower(), error=f"Could not read audio file: {exc}")
        duration = frames / sample_rate if sample_rate else 0.0
        samples = self._samples_from_bytes(raw, sample_width)
        mono = self._to_mono(samples, channels)
        normalized = self._normalize(mono, sample_width)
        rms_values = self._windowed_rms(normalized, sample_rate)
        rms_mean = sum(rms_values) / len(rms_values) if rms_values else 0.0
        rms_std = self._std(rms_values, rms_mean)
        peak = max((abs(v) for v in normalized), default=0.0)
        warnings = ["BPM, key, LUFS, and frequency-band analysis require optional DSP dependencies."]
        if peak >= 0.999:
            warnings.append("Peak reaches full scale; check clipping or limiter ceiling before release.")
        elif peak >= 0.98:
            warnings.append("Peak is very close to full scale; leave more mastering headroom.")
        return AudioFeatures(
            available=True,
            file_path=str(path),
            file_name=path.name,
            extension=path.suffix.lower(),
            duration_sec=duration,
            sample_rate=sample_rate,
            channels=channels,
            rms_mean=rms_mean,
            rms_std=rms_std,
            peak_amplitude=peak,
            dynamic_range_db=self._dynamic_range_db(rms_values),
            estimated_key="unknown",
            section_energies=self._section_energies(normalized, sample_rate),
            warnings=warnings,
        )

    @staticmethod
    def _samples_from_bytes(raw: bytes, sample_width: int) -> list[int]:
        if sample_width == 1:
            return [b - 128 for b in raw]
        if sample_width == 2:
            values = array("h")
            values.frombytes(raw)
            return list(values)
        if sample_width == 4:
            values = array("i")
            values.frombytes(raw)
            return list(values)
        raise wave.Error(f"Unsupported sample width: {sample_width}")

    @staticmethod
    def _to_mono(samples: list[int], channels: int) -> list[float]:
        if channels <= 1:
            return [float(v) for v in samples]
        mono = []
        for index in range(0, len(samples), channels):
            frame = samples[index:index + channels]
            if frame:
                mono.append(sum(frame) / len(frame))
        return mono

    @staticmethod
    def _normalize(samples: list[float], sample_width: int) -> list[float]:
        max_value = float((2 ** (8 * sample_width - 1)) - 1)
        return [max(-1.0, min(1.0, value / max_value)) for value in samples] if max_value > 0 else []

    @staticmethod
    def _windowed_rms(samples: list[float], sample_rate: int) -> list[float]:
        if not samples:
            return []
        window = max(1, sample_rate // 20) if sample_rate else 1024
        values = []
        for start in range(0, len(samples), window):
            chunk = samples[start:start + window]
            if chunk:
                values.append(math.sqrt(sum(v * v for v in chunk) / len(chunk)))
        return values

    @staticmethod
    def _std(values: list[float], mean: float) -> float:
        return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values)) if values else 0.0

    @staticmethod
    def _dynamic_range_db(rms_values: list[float]) -> float:
        nonzero = [value for value in rms_values if value > 1e-9]
        if not nonzero:
            return 0.0
        ordered = sorted(nonzero)
        low_index = max(0, min(len(ordered) - 1, math.ceil((len(ordered) - 1) * 0.10)))
        high_index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * 0.95)))
        low = ordered[low_index] if ordered[low_index] > 1e-9 else min(nonzero)
        high = ordered[high_index]
        return 20.0 * math.log10(high / low) if low > 1e-9 and high > 0 else 0.0

    def _section_energies(self, samples: list[float], sample_rate: int) -> list[SectionEnergy]:
        if not samples or sample_rate <= 0:
            return []
        total_sections = self._section_count_for_duration(len(samples) / sample_rate)
        section_len = max(1, len(samples) // total_sections)
        temp = []
        max_rms = 0.0
        for index in range(total_sections):
            start = index * section_len
            end = len(samples) if index == total_sections - 1 else min(len(samples), (index + 1) * section_len)
            chunk = samples[start:end]
            rms = math.sqrt(sum(v * v for v in chunk) / len(chunk)) if chunk else 0.0
            max_rms = max(max_rms, rms)
            temp.append((index, start, end, rms))
        return self._section_energy_objects(temp, max_rms, sample_rate)

    @staticmethod
    def _section_energy_objects(temp: list[tuple[int, int, int, float]], max_rms: float, sample_rate: int) -> list[SectionEnergy]:
        result = []
        for index, start, end, rms in temp:
            relative = rms / max_rms if max_rms else 0.0
            label = "High" if relative >= 0.75 else "Medium" if relative >= 0.35 else "Low"
            result.append(SectionEnergy(f"Part {index + 1}", start / sample_rate, end / sample_rate, rms, label))
        return result





