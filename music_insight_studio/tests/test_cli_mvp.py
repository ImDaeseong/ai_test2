from __future__ import annotations

import importlib.util
import json
import math
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
from pathlib import Path

from app.analyzers import AudioAnalyzer, TextAnalyzer
from app.core import AnalysisMode, TrackInput, Verdict
from app.services import AnalysisService
from app.notation import LeadSheetMusicXmlWriter, NoteEvent, TranscriptionResult
from app.web.security import UploadSecurityPolicy, validate_audio_payload, validate_content_length
from app.web.server import STATIC_FILES, WebPaths, UploadedAudio, UNSUPPORTED_AUDIO_MESSAGE, analyze_upload, is_allowed_audio, parse_report_path, render_home, render_score_page, render_user_result, safe_filename


ROOT = Path(__file__).resolve().parents[1]


def write_test_wav(path: Path, seconds: float = 1.0, sample_rate: int = 8000, peak_amp: float = 0.6) -> None:
    frames = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        data = bytearray()
        for index in range(frames):
            amp = 0.2 if index < frames // 2 else peak_amp
            sample = int(32767 * amp * math.sin(2 * math.pi * 440 * index / sample_rate))
            data.extend(struct.pack("<h", sample))
        wav.writeframes(bytes(data))


def has_optional_dsp() -> bool:
    return bool(importlib.util.find_spec("numpy") and importlib.util.find_spec("soundfile"))


def codec_available(format_name: str) -> bool:
    if not importlib.util.find_spec("soundfile"):
        return False
    import soundfile as sf

    return format_name.upper() in sf.available_formats()


def write_soundfile_audio(path: Path, format_name: str, seconds: float = 1.0, sample_rate: int = 8000) -> None:
    import numpy as np
    import soundfile as sf

    t = np.arange(int(seconds * sample_rate), dtype=float) / sample_rate
    first = 0.2 * np.sin(2 * np.pi * 440 * t[: len(t) // 2])
    second = 0.6 * np.sin(2 * np.pi * 440 * t[len(t) // 2 :])
    y = np.concatenate([first, second])
    sf.write(str(path), y, sample_rate, format=format_name.upper())


class CliMvpTests(unittest.TestCase):
    def test_audio_analyzer_reads_wav_without_ui(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            write_test_wav(audio_path)
            features = AudioAnalyzer().analyze(audio_path)
        self.assertTrue(features.available)
        self.assertEqual(features.sample_rate, 8000)
        self.assertGreater(features.rms_mean, 0)
        # 1s fixture is below TARGET_SECTION_SECONDS, so it floors to MIN_SECTIONS.
        self.assertEqual(len(features.section_energies), AudioAnalyzer.MIN_SECTIONS)

    def test_section_count_scales_with_duration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "long.wav"
            write_test_wav(audio_path, seconds=150.0)
            features = AudioAnalyzer().analyze(audio_path)
        expected = round(150.0 / AudioAnalyzer.TARGET_SECTION_SECONDS)
        self.assertEqual(len(features.section_energies), expected)
        self.assertGreater(len(features.section_energies), AudioAnalyzer.MIN_SECTIONS)

    def test_full_scale_peak_is_flagged_and_not_overrewarded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "hot.wav"
            write_test_wav(audio_path, seconds=12.0, peak_amp=1.0)
            features = AudioAnalyzer().analyze(audio_path)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.AUTO))
        scores = {score.group: score for score in report.scores}
        self.assertGreaterEqual(features.peak_amplitude, 0.98)
        self.assertTrue(any("Peak" in warning for warning in features.warnings))
        self.assertIn("peak_headroom_risk", scores["Technical Audio"].evidence)
        self.assertIn("peak_headroom_risk", scores["Mix and Master"].evidence)
        self.assertLess(scores["Technical Audio"].score or 100, 90)
        self.assertEqual(scores["Mix and Master"].verdict, Verdict.REVISE)
        self.assertLess(scores["Mix and Master"].score or 100, 70)


    @unittest.skipUnless(has_optional_dsp(), "optional DSP unavailable in this environment")
    def test_bpm_estimator_prefers_librosa_when_available(self) -> None:
        import numpy as np

        class FakeBeat:
            @staticmethod
            def beat_track(y, sr, hop_length, start_bpm, units):
                return 111.5, np.arange(12)

        class FakeLibrosa:
            beat = FakeBeat()

        analyzer = AudioAnalyzer()
        y = np.zeros(22050 * 8, dtype=float)
        rms = np.ones(160, dtype=float) * 0.1
        with patch.dict(sys.modules, {"librosa": FakeLibrosa()}):
            bpm, confidence = analyzer._estimate_bpm_from_audio_np(y, 22050, rms, np)
        self.assertEqual(bpm, 111.5)
        self.assertGreater(confidence, 0.05)
    @unittest.skipUnless(has_optional_dsp(), "optional DSP unavailable in this environment")
    def test_bpm_estimator_uses_onset_flux_for_pulse_timing(self) -> None:
        import numpy as np

        analyzer = AudioAnalyzer()
        sample_rate = 22050
        seconds = 12.0
        bpm = 123.0
        t = np.arange(int(seconds * sample_rate), dtype=float) / sample_rate
        y = 0.04 * np.sin(2 * np.pi * 220 * t)
        beat_interval = 60.0 / bpm
        for beat in np.arange(0.0, seconds, beat_interval):
            center = int(beat * sample_rate)
            width = int(0.025 * sample_rate)
            start = max(0, center - width)
            end = min(len(y), center + width)
            if end > start:
                envelope = np.hanning(end - start)
                y[start:end] += 0.8 * envelope
        rms = analyzer._windowed_rms_np(y, sample_rate, np)
        estimated_bpm, confidence = analyzer._estimate_bpm_from_audio_np(y, sample_rate, rms, np)
        self.assertLess(abs(estimated_bpm - bpm), 3.0)
        self.assertGreater(confidence, 0.1)

    def test_dynamic_range_uses_robust_percentiles(self) -> None:
        value = AudioAnalyzer._dynamic_range_db([0.000001, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28])
        self.assertLess(value, 6.0)

    def test_text_analyzer_detects_sections_and_ai_mentions(self) -> None:
        lyrics = "[Verse]\n오늘 밤\n[Chorus]\n빛이 남아\n빛이 남아\n[ad-lib]"
        prompt = "Suno clean studio mix"
        features = TextAnalyzer().analyze(lyrics=lyrics, prompt=prompt)
        self.assertTrue(features.has_lyrics)
        self.assertIn("Verse", features.section_names)
        self.assertIn("suno", features.ai_tool_mentions)
        self.assertTrue(features.warnings)

    def test_analysis_service_keeps_pipeline_separated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            out_dir = Path(tmp) / "out"
            write_test_wav(audio_path)
            service = AnalysisService()
            report = service.analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.GENERAL))
            paths = service.write_reports(report, out_dir)
        self.assertNotEqual(report.overall_verdict, Verdict.HOLD)
        self.assertEqual({path.name for path in paths}, {"analysis_report.md", "analysis_report.ko.md", "analysis_report.json", "analysis_lead_sheet.musicxml"})

    def test_cli_generates_markdown_and_json_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            out_dir = Path(tmp) / "out"
            write_test_wav(audio_path)
            result = subprocess.run(
                [sys.executable, "-m", "app.cli", "analyze", str(audio_path), "--out", str(out_dir), "--mode", "general"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((out_dir / "analysis_report.md").exists())
            self.assertTrue((out_dir / "analysis_report.ko.md").exists())
            self.assertTrue((out_dir / "analysis_lead_sheet.musicxml").exists())
            data = json.loads((out_dir / "analysis_report.json").read_text(encoding="utf-8"))
        self.assertIn("overall_verdict", data)
        self.assertGreater(len(data["scores"]), 0)

    def test_korean_report_contains_user_facing_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            out_dir = Path(tmp) / "out"
            write_test_wav(audio_path)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.AUTO))
            AnalysisService().write_reports(report, out_dir)
            text = (out_dir / "analysis_report.ko.md").read_text(encoding="utf-8")
        self.assertIn("# 음악 분석 리포트", text)
        self.assertIn("## 핵심 오디오 근거", text)
        self.assertIn("## 세부 평가", text)
        self.assertIn("기술적 오디오 품질", text)
        self.assertIn("## 우선 개선 포인트", text)
        self.assertIn("가사 또는 훅 정보를 추가", text)
        self.assertIn("mode를 `ai_music`", text)
        self.assertIn("최종 판단", text)
        self.assertIn("수정 권장", text)
        self.assertIn("## Suno 스타일 제안", text)
        self.assertIn("현재 스타일", text)
        self.assertIn("개선 스타일", text)
        self.assertIn("수정 권장: 공개 전 수정 권장", text)
        self.assertNotIn("REVISE / 수정 권장", text)

    def test_hot_korean_report_recommends_headroom(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "hot.wav"
            out_dir = Path(tmp) / "out"
            write_test_wav(audio_path, seconds=12.0, peak_amp=1.0)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.GENERAL))
            AnalysisService().write_reports(report, out_dir)
            text = (out_dir / "analysis_report.ko.md").read_text(encoding="utf-8")
        self.assertIn("avoid clipping", text)
        self.assertIn("more mastering headroom", text)
        self.assertIn("피크가 너무 높아 헤드룸/클리핑 확인 필요", text)
        self.assertIn("마스터링 리미터 ceiling", text)



    def test_general_audio_without_lyrics_marks_lyrics_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            write_test_wav(audio_path)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.GENERAL))
        scores = {score.group: score for score in report.scores}
        self.assertIsNone(scores["Lyrics and Hook"].score)
        self.assertEqual(scores["Lyrics and Hook"].verdict, Verdict.NOT_APPLICABLE)
        self.assertIn("lyrics not provided", scores["Lyrics and Hook"].evidence)

    def test_short_fixture_is_not_overrated_as_release_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            write_test_wav(audio_path)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.GENERAL))
        self.assertEqual(report.overall_verdict, Verdict.REVISE)
        self.assertLess(report.overall_score or 0, 70)
        evidence = " ".join(item for score in report.scores for item in score.evidence)
        self.assertIn("duration_too_short_for_music_judgment", evidence)

    def test_release_length_audio_scores_audio_quality_without_overclaiming_market_fit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "release.wav"
            write_test_wav(audio_path, seconds=90.0)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.GENERAL, target_platform="spotify"))
        scores = {score.group: score for score in report.scores}
        self.assertEqual(scores["Technical Audio"].verdict, Verdict.PASS)
        self.assertEqual(scores["Mix and Master"].verdict, Verdict.PASS)
        self.assertIn("duration_release_window", scores["Market and Release Fit"].evidence)
        self.assertNotEqual(report.overall_verdict, Verdict.HOLD)
        self.assertGreater(report.overall_score or 0, 60)

    def test_composition_and_production_evidence_explains_energy_variety(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            flat_path = Path(tmp) / "flat.wav"
            varied_path = Path(tmp) / "varied.wav"
            write_test_wav(flat_path, seconds=90.0, peak_amp=0.2)
            write_test_wav(varied_path, seconds=90.0, peak_amp=0.6)
            flat_report = AnalysisService().analyze(TrackInput(audio_path=flat_path, mode=AnalysisMode.GENERAL))
            varied_report = AnalysisService().analyze(TrackInput(audio_path=varied_path, mode=AnalysisMode.GENERAL))
        flat_scores = {score.group: score for score in flat_report.scores}
        varied_scores = {score.group: score for score in varied_report.scores}
        self.assertIn("energy_label_variety=1", flat_scores["Composition"].evidence)
        self.assertIn("energy_spread=flat", flat_scores["Production"].evidence)
        self.assertGreaterEqual(len({e for e in varied_scores["Composition"].evidence if e.startswith("energy_label_variety=")}), 1)
        self.assertNotIn("energy_label_variety=1", varied_scores["Composition"].evidence)
        self.assertGreater(varied_scores["Composition"].score or 0, flat_scores["Composition"].score or 0)

    def test_ai_music_without_prompt_or_lyrics_is_not_overrated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "ai.wav"
            write_test_wav(audio_path, seconds=90.0)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.AI_MUSIC))
        scores = {score.group: score for score in report.scores}
        self.assertEqual(scores["AI Naturalness"].verdict, Verdict.REVISE)
        self.assertIn("ai_context_missing", scores["AI Naturalness"].evidence)


class WebMvpTests(unittest.TestCase):
    def test_upload_security_rejects_oversized_body_and_spoofed_audio(self) -> None:
        policy = UploadSecurityPolicy(max_upload_bytes=16)
        with self.assertRaisesRegex(ValueError, "too large"):
            validate_content_length(17, policy)
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_audio_payload("fake.wav", b"not a wave file", UploadSecurityPolicy())

    def test_upload_security_accepts_real_wav_signature(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            write_test_wav(audio_path)
            payload = audio_path.read_bytes()
        validate_audio_payload("sample.wav", payload, UploadSecurityPolicy())

    def test_web_upload_validation_allows_supported_audio_only(self) -> None:
        self.assertTrue(is_allowed_audio("demo.WAV"))
        self.assertTrue(is_allowed_audio("demo.flac"))
        self.assertTrue(is_allowed_audio("demo.mp3"))
        self.assertFalse(is_allowed_audio("demo.txt"))
        self.assertEqual(safe_filename("../bad name.mp3"), "bad_name.mp3")
        self.assertIn("M4A/AAC", UNSUPPORTED_AUDIO_MESSAGE)

    def test_web_home_renders_upload_form(self) -> None:
        page = render_home().decode("utf-8")
        self.assertIn('enctype="multipart/form-data"', page)
        self.assertIn('name="audio"', page)
        self.assertIn(".ogg", page)
        self.assertIn(".aiff", page)
        self.assertIn('name="mode"', page)
        self.assertNotIn('name="prompt"', page)
        self.assertNotIn('name="lyrics"', page)
        self.assertNotIn('name="target"', page)
        self.assertIn("음악 분석", page)
        self.assertIn("음원 파일", page)
        self.assertIn("분석 모드", page)
        self.assertIn("분석하기", page)
        self.assertNotIn("Audio File", page)
        self.assertNotIn(">Analyze<", page)

    def test_web_upload_uses_analysis_service_and_returns_inline_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            write_test_wav(audio_path)
            uploaded = UploadedAudio("sample.wav", audio_path.read_bytes())
            links, verdict, score, report_text = analyze_upload(
                uploaded,
                AnalysisMode.GENERAL,
                "general",
                WebPaths(Path(tmp) / "uploads", Path(tmp) / "outputs"),
            )
            generated = list((Path(tmp) / "outputs").glob("*/analysis_report.ko.md"))
            generated_score = list((Path(tmp) / "outputs").glob("*/analysis_lead_sheet.musicxml"))
        self.assertEqual(verdict, Verdict.REVISE)
        self.assertIsNotNone(score)
        self.assertIn("korean_markdown", links)
        self.assertIn("musicxml", links)
        self.assertEqual(len(generated), 1)
        self.assertEqual(len(generated_score), 1)
        self.assertIn("# 음악 분석 리포트", report_text)
        self.assertIn("## 세부 평가", report_text)

    def test_web_result_shows_json_and_score_links_with_friendly_verdict(self) -> None:
        html_text = render_user_result(
            {
                "markdown": "/reports/demo/analysis_report.md",
                "korean_markdown": "/reports/demo/analysis_report.ko.md",
                "json": "/reports/demo/analysis_report.json",
                "musicxml": "/reports/demo/analysis_lead_sheet.musicxml",
            },
            Verdict.REVISE,
            69.7,
            "# 음악 분석 리포트\n\n## 요약\n\n- 최종 판단: **수정 권장**\n",
        )
        self.assertIn("수정 권장", html_text)
        self.assertIn("analysis_report.json", html_text)
        self.assertIn("analysis_lead_sheet.musicxml", html_text)
        self.assertIn("악보 MusicXML", html_text)
        self.assertNotIn("Korean Markdown", html_text)
        self.assertNotIn(">Markdown</a>", html_text)

    def test_web_result_links_open_in_new_tab_instead_of_inline(self) -> None:
        html_text = render_user_result(
            {
                "markdown": "/reports/demo/analysis_report.md",
                "korean_markdown": "/reports/demo/analysis_report.ko.md",
                "json": "/reports/demo/analysis_report.json",
                "musicxml": "/reports/demo/analysis_lead_sheet.musicxml",
            },
            Verdict.REVISE,
            69.7,
            "# 음악 분석 리포트\n",
        )
        self.assertIn('href="/reports/demo/analysis_report.json" target="_blank" rel="noopener"', html_text)
        self.assertIn('href="/score?src=%2Freports%2Fdemo%2Fanalysis_lead_sheet.musicxml" target="_blank" rel="noopener"', html_text)
        self.assertNotIn('class="score-view"', html_text)
        self.assertNotIn('onclick="return renderScoreView(this);"', html_text)

    def test_web_home_does_not_load_score_renderer_inline(self) -> None:
        # The score renderer now lives on the standalone /score page (new tab),
        # not on the home page, so the home page should not pay its load cost.
        page = render_home().decode("utf-8")
        self.assertNotIn('/static/vendor/opensheetmusicdisplay.min.js', page)
        self.assertNotIn('score-notation', page)
        self.assertNotIn('score-xml', page)

    def test_score_page_loads_vendored_renderer_and_wraps_systems(self) -> None:
        page = render_score_page("/reports/demo/analysis_lead_sheet.musicxml").decode("utf-8")
        self.assertIn('/static/vendor/opensheetmusicdisplay.min.js', page)
        self.assertIn('score-notation', page)
        self.assertIn('score-xml', page)
        self.assertIn('data-musicxml-url="/reports/demo/analysis_lead_sheet.musicxml"', page)
        # Without this, OSMD squeezes every measure onto a single unreadable
        # line instead of wrapping into readable systems.
        self.assertIn('RenderXMeasuresPerLineAkaSystem', page)

    def test_score_route_rejects_paths_outside_reports_allowlist(self) -> None:
        self.assertIsNone(parse_report_path("/reports/demo/../../etc/passwd"))
        self.assertIsNone(parse_report_path("/reports/not-hex-id/analysis_lead_sheet.musicxml"))
        self.assertIsNone(parse_report_path("/reports/0123456789ab/analysis_report.md.bak"))
        self.assertEqual(parse_report_path("/reports/0123456789ab/analysis_lead_sheet.musicxml"), ("0123456789ab", "analysis_lead_sheet.musicxml"))

    def test_vendored_score_renderer_asset_is_present_on_disk(self) -> None:
        file_path, content_type = STATIC_FILES["/static/vendor/opensheetmusicdisplay.min.js"]
        self.assertTrue(file_path.is_file())
        self.assertIn("javascript", content_type)


class OptionalDspFallbackTests(unittest.TestCase):
    def test_mp3_dependency_behavior_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "placeholder.mp3"
            audio_path.write_bytes(b"not a real mp3")
            features = AudioAnalyzer().analyze(audio_path)
        self.assertFalse(features.available)
        if has_optional_dsp():
            self.assertIn("optional dsp analysis failed", features.error.lower())
        else:
            self.assertIn("optional dependencies", " ".join(features.warnings).lower())
            self.assertEqual(features.error, "")

    def test_report_includes_advanced_audio_fields_even_when_unestimated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            out_dir = Path(tmp) / "out"
            write_test_wav(audio_path)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.GENERAL))
            paths = AnalysisService().write_reports(report, out_dir)
            markdown_path = next(path for path in paths if path.name == "analysis_report.md")
            text = markdown_path.read_text(encoding="utf-8")
        self.assertIn("BPM:", text)
        self.assertIn("Estimated key:", text)
        self.assertIn("LUFS integrated:", text)

    def test_stdlib_wav_fallback_runs_without_numpy_available(self) -> None:
        # Regression test: _analyze_wav_fallback previously crashed with
        # NameError (referenced undefined `y`/`np` copy-pasted from the
        # numpy-based analysis path) whenever numpy/soundfile were actually
        # unavailable. Force that path explicitly so this is caught
        # regardless of whether numpy happens to be installed in the
        # environment running this test.
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            write_test_wav(audio_path)
            with patch.object(AudioAnalyzer, "_has_optional_dsp", return_value=False):
                features = AudioAnalyzer().analyze(audio_path)
        self.assertTrue(features.available, features.error)
        self.assertEqual(features.error, "")
        self.assertEqual(features.bpm, 0.0)
        self.assertEqual(features.estimated_key, "unknown")
        self.assertIn("optional dsp dependencies", " ".join(features.warnings).lower())


class CodecAnalysisTests(unittest.TestCase):
    @unittest.skipUnless(has_optional_dsp() and codec_available("FLAC"), "FLAC codec unavailable in this environment")
    def test_audio_analyzer_reads_real_flac(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.flac"
            write_soundfile_audio(audio_path, "FLAC")
            features = AudioAnalyzer().analyze(audio_path)
        self.assertTrue(features.available, features.error)
        self.assertEqual(features.extension, ".flac")
        self.assertEqual(features.sample_rate, 8000)
        self.assertEqual(features.estimated_key, "A")
        self.assertIsNotNone(features.lufs_integrated)
        self.assertEqual(len(features.frequency_bands), 7)

    @unittest.skipUnless(has_optional_dsp() and codec_available("MP3"), "MP3 codec unavailable in this environment")
    def test_audio_analyzer_reads_real_mp3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.mp3"
            write_soundfile_audio(audio_path, "MP3")
            features = AudioAnalyzer().analyze(audio_path)
        self.assertTrue(features.available, features.error)
        self.assertEqual(features.extension, ".mp3")
        self.assertEqual(features.sample_rate, 8000)
        self.assertGreater(features.duration_sec, 0.9)
        self.assertEqual(len(features.frequency_bands), 7)

class FakeTranscriber:
    def transcribe(self, audio_path: Path | str, bpm: float = 0.0) -> TranscriptionResult:
        return TranscriptionResult("test-transcriber", [NoteEvent(0.0, 0.5, 69, 80, 0.9), NoteEvent(0.5, 1.0, 71, 80, 0.8)], [])


class EmptyTranscriber:
    def transcribe(self, audio_path: Path | str, bpm: float = 0.0) -> TranscriptionResult:
        return TranscriptionResult("none", [], ["No stable pitched events found for melody guide."])


class NotationExportTests(unittest.TestCase):
    def test_musicxml_transcription_export_writes_pitched_notes_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            out_dir = Path(tmp) / "out"
            write_test_wav(audio_path)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.GENERAL))
            path = LeadSheetMusicXmlWriter(FakeTranscriber()).write(report, out_dir)
            text = path.read_text(encoding="utf-8")
        self.assertIn("Transcription Guide", text)
        self.assertIn("test-transcriber", text)
        self.assertIn("<pitch>", text)
        self.assertIn("<step>A</step>", text)
        self.assertIn("Automatic transcription guide only", text)

    def test_musicxml_lead_sheet_export_uses_analysis_metadata_when_no_notes_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            audio_path = Path(tmp) / "sample.wav"
            out_dir = Path(tmp) / "out"
            write_test_wav(audio_path)
            report = AnalysisService().analyze(TrackInput(audio_path=audio_path, mode=AnalysisMode.GENERAL))
            path = LeadSheetMusicXmlWriter(EmptyTranscriber()).write(report, out_dir)
            self.assertTrue(path.exists())
            text = path.read_text(encoding="utf-8")
        self.assertIn("score-partwise", text)
        self.assertIn("Analysis Lead Sheet", text)
        self.assertIn("Generated from analysis metadata", text)
        self.assertIn("No melody/chord transcription", text)

if __name__ == "__main__":
    unittest.main()












