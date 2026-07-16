from __future__ import annotations

from pathlib import Path

from app.core import EvaluationReport, Verdict


class MarkdownReportWriter:
    def write(self, report: EvaluationReport, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "analysis_report.md"
        path.write_text(self.render(report), encoding="utf-8")
        return path

    def render(self, report: EvaluationReport) -> str:
        audio = report.audio
        overall = "N/A" if report.overall_score is None else f"{report.overall_score:.1f}/100"
        lines = [
            "# Music Analysis Report",
            "",
            "## Summary",
            "",
            f"- File: `{audio.file_name}`",
            f"- Mode: `{report.track.mode.value}`",
            f"- Overall: **{overall}**",
            f"- Verdict: **{report.overall_verdict.value}**",
            "",
            "## Audio Evidence",
            "",
            f"- Available: {audio.available}",
            f"- Duration: {audio.duration_label}",
            f"- Sample rate: {audio.sample_rate}",
            f"- Channels: {audio.channels}",
            f"- BPM: {audio.bpm:.1f}" if audio.bpm else "- BPM: not estimated",
            f"- BPM confidence: {audio.bpm_confidence:.2f}" if audio.bpm_confidence else "- BPM confidence: not estimated",
            f"- Estimated key: {audio.estimated_key}",
            f"- LUFS integrated: {audio.lufs_integrated:.2f}" if audio.lufs_integrated is not None else "- LUFS integrated: not measured",
            f"- RMS mean: {audio.rms_mean:.4f}",
            f"- Peak amplitude: {audio.peak_amplitude:.3f}",
            f"- Dynamic range proxy: {audio.dynamic_range_db:.2f} dB",
        ]
        if audio.frequency_bands:
            lines.extend(["", "### Frequency Bands", ""])
            for name, value in audio.frequency_bands.items():
                lines.append(f"- {name}: {value}")
        if audio.error:
            lines.append(f"- Error: {audio.error}")
        for warning in audio.warnings:
            lines.append(f"- Warning: {warning}")
        lines.extend(["", "## Scores", ""])
        for score in report.scores:
            value = "N/A" if score.score is None else f"{score.score:.1f}/100"
            lines.extend([
                f"### {score.group}",
                "",
                f"- Score: {value}",
                f"- Verdict: {score.verdict.value}",
                f"- Criteria: `{score.criteria_file}`",
                f"- Reason: {score.reason}",
            ])
            if score.evidence:
                lines.append(f"- Evidence: {'; '.join(score.evidence)}")
            if score.uncertainty:
                lines.append(f"- Uncertainty: {score.uncertainty}")
            if score.next_action:
                lines.append(f"- Next action: {score.next_action}")
            lines.append("")
        if report.overall_verdict == Verdict.HOLD and report.hold_reasons:
            lines.extend(["## HOLD Reasons", ""])
            for reason in report.hold_reasons:
                lines.append(f"- {reason}")
        return "\n".join(lines).rstrip() + "\n"
