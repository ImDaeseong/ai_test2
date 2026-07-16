from __future__ import annotations

from pathlib import Path

from app.analyzers import AudioAnalyzer, TextAnalyzer
from app.core import EvaluationReport, TrackInput
from app.notation import LeadSheetMusicXmlWriter
from app.reports import JsonReportWriter, KoreanMarkdownReportWriter, MarkdownReportWriter
from app.scoring import ScoringEngine


class AnalysisService:
    """Coordinates analyzers, scoring, and reports for CLI and future UI."""

    def __init__(self, audio_analyzer: AudioAnalyzer | None = None, text_analyzer: TextAnalyzer | None = None, scoring_engine: ScoringEngine | None = None) -> None:
        self.audio_analyzer = audio_analyzer or AudioAnalyzer()
        self.text_analyzer = text_analyzer or TextAnalyzer()
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.markdown_writer = MarkdownReportWriter()
        self.korean_markdown_writer = KoreanMarkdownReportWriter()
        self.json_writer = JsonReportWriter()
        self.musicxml_writer = LeadSheetMusicXmlWriter()

    def analyze(self, track: TrackInput) -> EvaluationReport:
        audio = self.audio_analyzer.analyze(track.audio_path)
        text = self.text_analyzer.analyze(lyrics=track.lyrics, prompt=track.prompt)
        scores, overall, verdict, hold_reasons = self.scoring_engine.evaluate(audio, text, track.mode, track.target_platform)
        return EvaluationReport(track, audio, text, scores, overall, verdict, hold_reasons)

    def write_reports(self, report: EvaluationReport, out_dir: Path) -> list[Path]:
        return [
            self.markdown_writer.write(report, out_dir),
            self.korean_markdown_writer.write(report, out_dir),
            self.json_writer.write(report, out_dir),
            self.musicxml_writer.write(report, out_dir),
        ]

