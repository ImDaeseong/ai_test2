from __future__ import annotations

from app.core import AnalysisMode, Verdict
from app.scoring.base import BaseScorer, ScoringContext, clamp, verdict_from_score
from app.scoring.rubric import (
    MIN_DYNAMIC_RANGE_DB,
    MIN_FULL_TRACK_DURATION_SEC,
    MIN_REVIEWABLE_DURATION_SEC,
    MIN_SIGNAL_RMS,
    PEAK_HEADROOM_LIMIT,
    RELEASE_DURATION_MAX_SEC,
    RELEASE_DURATION_MIN_SEC,
    cap_for_short_duration,
    duration_evidence,
)




def section_energy_stats(audio) -> tuple[int, float, float]:
    values = [section.mean_rms for section in audio.section_energies] if audio.available else []
    if not values:
        return 0, 0.0, 0.0
    labels = len({section.energy_label for section in audio.section_energies})
    low = min(values)
    high = max(values)
    contrast = (high - low) / high if high > 1e-9 else 0.0
    avg = sum(values) / len(values)
    movement = sum(abs(value - avg) for value in values) / len(values) / avg if avg > 1e-9 else 0.0
    return labels, contrast, movement


def lufs_release_score(lufs: float | None) -> float:
    if lufs is None:
        return 0.0
    if -16.0 <= lufs <= -9.0:
        return 8.0
    if -18.0 <= lufs < -16.0 or -9.0 < lufs <= -7.0:
        return 4.0
    return -4.0


def peak_headroom_score(peak: float) -> float:
    if peak <= 0:
        return 0.0
    if peak <= 0.95:
        return 12.0
    if peak <= PEAK_HEADROOM_LIMIT:
        return 8.0
    if peak < 0.999:
        return -8.0
    return -18.0
class TechnicalAudioScorer(BaseScorer):
    group = "Technical Audio"
    criteria_file = "docs/audio_analysis_scope.md"

    def score(self, context: ScoringContext):
        audio = context.audio
        if not audio.available:
            return self.result(0, Verdict.HOLD, [audio.error or "No measurable audio features available."], "Audio evidence is unavailable, so technical scoring is on HOLD.", next_action="Use a readable WAV/MP3/FLAC file or install optional decoders.")
        score = 42.0
        if audio.duration_sec >= MIN_FULL_TRACK_DURATION_SEC:
            score += 14
        elif audio.duration_sec >= MIN_REVIEWABLE_DURATION_SEC:
            score += 7
        else:
            score -= 10
        if audio.rms_mean > MIN_SIGNAL_RMS:
            score += min(14.0, audio.rms_mean / 0.18 * 14.0)
        score += peak_headroom_score(audio.peak_amplitude)
        score += min(12.0, max(0.0, (audio.dynamic_range_db - 2.0) / 8.0 * 12.0))
        _, energy_contrast, energy_movement = section_energy_stats(audio)
        if audio.section_energies:
            score += min(7.0, 3.0 + energy_contrast * 8.0 + energy_movement * 6.0)
        score += lufs_release_score(audio.lufs_integrated)
        if audio.frequency_bands:
            score += 3.0
        score = cap_for_short_duration(clamp(score), audio.duration_sec, 65.0)
        evidence = [duration_evidence(audio.duration_sec), f"duration={audio.duration_label}", f"rms={audio.rms_mean:.4f}", f"peak={audio.peak_amplitude:.3f}", f"dynamic_range={audio.dynamic_range_db:.2f}dB", f"energy_contrast={energy_contrast:.2f}", f"energy_movement={energy_movement:.2f}", f"bpm={audio.bpm:.2f}", f"bpm_confidence={audio.bpm_confidence:.2f}", f"key={audio.estimated_key}"]
        if audio.peak_amplitude >= PEAK_HEADROOM_LIMIT:
            evidence.append("peak_headroom_risk")
        if audio.lufs_integrated is not None:
            evidence.append(f"lufs={audio.lufs_integrated:.2f}")
        uncertainty = "BPM/key/LUFS are computational estimates and need human listening confirmation." if audio.lufs_integrated is not None else "LUFS is unavailable unless pyloudnorm is installed."
        return self.result(score, verdict_from_score(score), evidence, "Audio evidence indicates the file is measurable and has usable signal quality.", uncertainty, "Use listening review or reference-track comparison before final release decisions.")

class ComposerScorer(BaseScorer):
    group = "Composition"
    criteria_file = "docs/composer_criteria.md"

    def score(self, context: ScoringContext):
        audio = context.audio
        text = context.text
        score = 45.0
        energy_variety, energy_contrast, energy_movement = section_energy_stats(audio)
        if audio.available and len(audio.section_energies) >= 4:
            score += min(24.0, energy_variety * 5.0 + energy_contrast * 18.0 + energy_movement * 10.0)
        if text.section_names:
            score += 15
        if text.hook_candidates:
            score += 10
        if audio.available and audio.duration_sec >= MIN_FULL_TRACK_DURATION_SEC:
            score += 5
        score = cap_for_short_duration(clamp(score), audio.duration_sec, 55.0)
        return self.result(score, verdict_from_score(score), [duration_evidence(audio.duration_sec), f"sections={len(text.section_names)}", f"hook_candidates={len(text.hook_candidates)}", f"energy_label_variety={energy_variety}", f"energy_contrast={energy_contrast:.2f}", f"energy_movement={energy_movement:.2f}"], "Composition is estimated from section structure, energy movement, and hook evidence.", "Precise melody and harmony review needs chords, MIDI, or deeper audio analysis.", "Provide lyrics/prompt sections and chord progression to improve this score.")

class LyricistScorer(BaseScorer):
    group = "Lyrics and Hook"
    criteria_file = "docs/lyricist_criteria.md"

    def score(self, context: ScoringContext):
        if context.mode == AnalysisMode.INSTRUMENTAL:
            return self.result(None, Verdict.NOT_APPLICABLE, ["instrumental mode"], "Lyrics scoring is skipped in instrumental mode.")
        text = context.text
        if not text.has_lyrics:
            return self.result(None, Verdict.NOT_APPLICABLE, ["lyrics not provided"], "Lyrics were not provided, so hook, pronunciation, and language quality are not scored from audio alone.", "The system does not infer lyric quality from audio alone.", "Provide lyrics or Suno Lyrics for a stronger lyricist review.")
        score = 60.0
        if text.hook_candidates:
            score += 15
        if text.repeated_line_count <= 2:
            score += 10
        if not text.warnings:
            score += 10
        if text.lyric_line_count >= 8:
            score += 5
        score = clamp(score)
        return self.result(score, verdict_from_score(score), [f"lines={text.lyric_line_count}", f"repeated_lines={text.repeated_line_count}"], "Lyrics are scored from line count, repetition, hook candidates, and Suno tag safety.", next_action="Review title fit, singability, and short-form hook strength manually.")


class ProducerScorer(BaseScorer):
    group = "Production"
    criteria_file = "docs/producer_criteria.md"

    def score(self, context: ScoringContext):
        audio = context.audio
        score = 45.0
        energy_spread = "none"
        if audio.available and audio.section_energies:
            labels = [section.energy_label for section in audio.section_energies]
            if "High" in labels and "Low" in labels:
                score += 20
                energy_spread = "high_and_low"
            elif len(set(labels)) >= 2:
                score += 12
                energy_spread = "mixed"
            else:
                energy_spread = "flat"
        if context.text.has_prompt:
            score += 10
        if audio.rms_std > 0.005:
            score += 10
        if audio.available and audio.duration_sec >= MIN_FULL_TRACK_DURATION_SEC:
            score += 5
        score = cap_for_short_duration(clamp(score), audio.duration_sec, 60.0)
        return self.result(score, verdict_from_score(score), [duration_evidence(audio.duration_sec), f"section_energy_count={len(audio.section_energies)}", f"prompt={context.text.has_prompt}", f"energy_spread={energy_spread}"], "Production is estimated from section energy movement and prompt texture evidence.", "Instrument layout and vocal space are only proxies until stem or deeper analysis is added.", "Add rhythm, texture, vocal attitude, and space notes in the prompt.")


class MixMasterScorer(BaseScorer):
    group = "Mix and Master"
    criteria_file = "docs/mixing_criteria.md, docs/mastering_criteria.md"

    def score(self, context: ScoringContext):
        audio = context.audio
        if not audio.available:
            return self.result(0, Verdict.HOLD, [audio.error or "audio unavailable"], "Mix/master scoring needs readable audio evidence.")
        score = 50.0
        if 0.02 <= audio.rms_mean <= 0.35:
            score += 15
        if audio.peak_amplitude <= PEAK_HEADROOM_LIMIT:
            score += 15
        else:
            score -= 15
        if audio.dynamic_range_db >= MIN_DYNAMIC_RANGE_DB:
            score += 10
        if audio.lufs_integrated is not None:
            score += 5
        if audio.frequency_bands:
            score += 5
        if audio.peak_amplitude >= 0.999:
            score = min(score, 65.0)
        elif audio.peak_amplitude >= PEAK_HEADROOM_LIMIT:
            score = min(score, 68.0)
        score = cap_for_short_duration(clamp(score), audio.duration_sec, 70.0)
        evidence = [duration_evidence(audio.duration_sec), f"rms={audio.rms_mean:.4f}", f"peak={audio.peak_amplitude:.3f}", f"dynamic_range={audio.dynamic_range_db:.2f}dB"]
        if audio.peak_amplitude >= PEAK_HEADROOM_LIMIT:
            evidence.append("peak_headroom_risk")
        if audio.lufs_integrated is not None:
            evidence.append(f"lufs={audio.lufs_integrated:.2f}")
        if audio.frequency_bands:
            evidence.append(f"frequency_bands={len(audio.frequency_bands)}")
        uncertainty = "True peak, codec artifacts, and final release loudness still need dedicated mastering checks."
        return self.result(score, verdict_from_score(score), evidence, "Mix/master risk is estimated from RMS, peak, dynamic range, LUFS, and frequency-band proxies when available.", uncertainty, "Compare against platform loudness targets and a reference track before release.")


class AIMusicScorer(BaseScorer):
    group = "AI Naturalness"
    criteria_file = "docs/ai_music_criteria.md"

    def score(self, context: ScoringContext):
        text = context.text
        ai_mode = context.mode == AnalysisMode.AI_MUSIC or bool(text.ai_tool_mentions)
        if context.mode == AnalysisMode.GENERAL and not ai_mode:
            return self.result(None, Verdict.NOT_APPLICABLE, ["non-ai mode"], "AI naturalness scoring is skipped in general music mode.")
        missing_context = not text.has_prompt and not text.has_lyrics
        score = 55.0 if missing_context else 70.0
        if text.repeated_line_count > 3:
            score -= 15
        if text.warnings:
            score -= 20
        if text.has_prompt:
            score += 5
        score = clamp(score)
        evidence = [f"ai_mentions={','.join(text.ai_tool_mentions) or 'none'}", f"warnings={len(text.warnings)}"]
        if missing_context:
            evidence.append("ai_context_missing")
        return self.result(score, verdict_from_score(score), evidence, "AI naturalness is estimated from AI-tool mentions, repetition, and label-only tag warnings.", "Actual vocal artifacts require listening or a specialized model.", "Provide Suno/Udio prompt and Lyrics to evaluate prompt-result fit later.")


class MarketReleaseScorer(BaseScorer):
    group = "Market and Release Fit"
    criteria_file = "docs/market_release_criteria.md"

    def score(self, context: ScoringContext):
        audio = context.audio
        text = context.text
        score = 40.0
        if text.hook_candidates:
            score += 15
        if audio.available and RELEASE_DURATION_MIN_SEC <= audio.duration_sec <= RELEASE_DURATION_MAX_SEC:
            score += 15
        elif audio.available and audio.duration_sec >= MIN_FULL_TRACK_DURATION_SEC:
            score += 5
        if audio.available and any(section.energy_label == "High" for section in audio.section_energies):
            score += 10
        if context.target_platform.lower() in {"youtube", "shorts", "spotify", "melon", "apple"}:
            score += 5
        score = cap_for_short_duration(clamp(score), audio.duration_sec, 45.0)
        return self.result(score, verdict_from_score(score), [duration_evidence(audio.duration_sec), f"target={context.target_platform}", f"duration={audio.duration_label}"], "Release fit is estimated from hook evidence, duration, energy points, and target platform.", "Views, playlist placement, and revenue are never guaranteed.", "For A/B comparison, add Hook, Visual, Channel Fit, and Personal Taste inputs.")






