from __future__ import annotations

from pathlib import Path

from app.core import EvaluationReport, ScoreResult, Verdict


class KoreanMarkdownReportWriter:
    """Render a Korean-facing report without mixing UI concerns into scoring."""

    def write(self, report: EvaluationReport, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "analysis_report.ko.md"
        path.write_text(self.render(report), encoding="utf-8")
        return path

    def render(self, report: EvaluationReport) -> str:
        audio = report.audio
        overall = "N/A" if report.overall_score is None else f"{report.overall_score:.1f}/100"
        lines = [
            "# 음악 분석 리포트",
            "",
            "## 요약",
            "",
            f"- 파일: `{audio.file_name}`",
            f"- 분석 모드: `{report.track.mode.value}`",
            f"- 대상 플랫폼: `{report.track.target_platform}`",
            f"- 종합 점수: **{overall}**",
            f"- 최종 판단: **{self._verdict_label(report.overall_verdict)}**",
            "",
            "## 우선 개선 포인트",
            "",
            *[f"- {item}" for item in self._priority_actions(report)],
            "",
            "## Suno 스타일 제안",
            "",
            f"- 현재 스타일: `{self._current_suno_style(report)}`",
            f"- 개선 스타일: `{self._improved_suno_style(report)}`",
            f"- 제안 이유: {self._style_reason(report)}",
            "",
            "## 핵심 오디오 근거",
            "",
            f"- 분석 가능 여부: {'가능' if audio.available else '불가'}",
            f"- 길이: {audio.duration_label}",
            f"- 샘플레이트/채널: {audio.sample_rate} Hz / {audio.channels} ch",
            f"- BPM: {audio.bpm:.1f}" if audio.bpm else "- BPM: 추정 불가",
            f"- BPM 신뢰도: {audio.bpm_confidence:.2f}" if audio.bpm_confidence else "- BPM 신뢰도: 추정 불가",
            f"- 추정 Key: {audio.estimated_key}",
            f"- LUFS: {audio.lufs_integrated:.2f}" if audio.lufs_integrated is not None else "- LUFS: 측정 불가",
            f"- 평균 RMS: {audio.rms_mean:.4f}",
            f"- 피크: {audio.peak_amplitude:.3f}",
            f"- 다이내믹 범위 추정: {audio.dynamic_range_db:.2f} dB",
        ]
        if audio.frequency_bands:
            lines.extend(["", "## 주파수 밴드", ""])
            for name, value in audio.frequency_bands.items():
                lines.append(f"- {self._band_label(name)}: {value}")
        if audio.error:
            lines.extend(["", f"- 오류: {audio.error}"])
        for warning in audio.warnings:
            lines.append(f"- 경고: {warning}")
        lines.extend(["", "## 세부 평가", ""])
        for score in report.scores:
            lines.extend(self._score_block(score))
        if report.overall_verdict == Verdict.HOLD and report.hold_reasons:
            lines.extend(["## HOLD 사유", ""])
            for reason in report.hold_reasons:
                lines.append(f"- {reason}")
        lines.extend([
            "## 판단 기준 메모",
            "",
            "- 진행 가능: 현재 근거상 공개 또는 다음 제작 단계 진행 가능",
            "- 수정 권장: 공개 전 수정 권장",
            "- 보류: 근거 부족 또는 품질/정책 위험 때문에 진행 보류",
            "- 이 리포트의 BPM/Key/LUFS는 계산 추정치이며, 최종 발매 판단 전 청감 확인이 필요합니다.",
        ])
        return "\n".join(lines).rstrip() + "\n"

    def _score_block(self, score: ScoreResult) -> list[str]:
        value = "N/A" if score.score is None else f"{score.score:.1f}/100"
        lines = [
            f"### {self._group_label(score.group)}",
            "",
            f"- 점수: {value}",
            f"- 판단: {self._verdict_label(score.verdict)}",
            f"- 기준 문서: `{score.criteria_file}`",
            f"- 평가 이유: {self._message_label(score.reason)}",
        ]
        if score.evidence:
            lines.append(f"- 근거: {'; '.join(self._evidence_label(item) for item in score.evidence)}")
        if score.uncertainty:
            lines.append(f"- 불확실성: {self._message_label(score.uncertainty)}")
        if score.next_action:
            lines.append(f"- 다음 조치: {self._message_label(score.next_action)}")
        lines.append("")
        return lines


    @staticmethod
    def _priority_actions(report: EvaluationReport) -> list[str]:
        audio = report.audio
        text = report.text
        actions = []

        if audio.peak_amplitude >= 0.999:
            actions.append("마스터링 리미터 ceiling을 낮추고 클리핑/헤드룸을 먼저 확인하세요. 권장 시작점: -1.0 dB ceiling.")
        elif audio.peak_amplitude >= 0.98:
            actions.append("피크가 높습니다. 최종 출력 전 최소한의 헤드룸을 확보하세요.")

        if audio.lufs_integrated is not None and audio.lufs_integrated > -10:
            actions.append("라우드니스가 높은 편입니다. 스트리밍용이면 과한 리미팅으로 인한 피로감이 없는지 청감 확인하세요.")

        if not text.has_lyrics and report.track.mode.value != "instrumental":
            actions.append("가사 또는 훅 정보를 추가하면 가사/훅과 시장성 판단이 더 정확해집니다.")

        if report.track.mode.value == "auto":
            actions.append("SunoAI로 만든 곡이면 mode를 `ai_music`으로 다시 분석해 AI 자연스러움 항목까지 확인하세요.")

        if report.overall_score is not None and report.overall_score < 70:
            actions.append("현재는 발매 확정이 아니라 수정 권장 상태입니다. 위 항목을 보완한 뒤 다시 분석하세요.")

        if not actions:
            actions.append("큰 HOLD 위험은 보이지 않습니다. 최종 발매 전 청감 리뷰와 기준곡 비교만 진행하세요.")

        return actions[:5]


    @staticmethod
    def _current_suno_style(report: EvaluationReport) -> str:
        audio = report.audio
        tags = []

        if audio.bpm:
            bpm = audio.bpm
            if bpm >= 160:
                tags.append("fast energetic")
            elif bpm >= 125:
                tags.append("uptempo")
            elif bpm >= 90:
                tags.append("mid tempo")
            else:
                tags.append("slow tempo")
            tags.append(f"{bpm:.0f} bpm")
        else:
            tags.append("tempo unclear")

        if audio.estimated_key and audio.estimated_key != "unknown":
            tags.append(f"key {audio.estimated_key}")

        tags.append(KoreanMarkdownReportWriter._frequency_style(audio.frequency_bands))
        tags.append(KoreanMarkdownReportWriter._energy_style(audio.section_energies))

        if audio.lufs_integrated is not None:
            if audio.lufs_integrated > -9:
                tags.append("loud master")
            elif audio.lufs_integrated >= -14:
                tags.append("streaming loudness")
            else:
                tags.append("soft master")

        return ", ".join(tag for tag in tags if tag)

    @staticmethod
    def _improved_suno_style(report: EvaluationReport) -> str:
        audio = report.audio
        tags = ["polished modern production", "clear arrangement"]

        if audio.bpm:
            tags.append(f"{audio.bpm:.0f} bpm")
        if audio.estimated_key and audio.estimated_key != "unknown":
            tags.append(f"key {audio.estimated_key}")

        if audio.duration_sec < 90:
            tags.extend(["full song structure", "strong chorus"])
        else:
            tags.extend(["radio ready structure", "memorable hook"])

        if audio.frequency_bands:
            tags.append("balanced low end and bright presence")
        if audio.peak_amplitude >= 0.98:
            tags.append("avoid clipping")
            tags.append("more mastering headroom")
        if audio.dynamic_range_db < 6:
            tags.append("more dynamic contrast")
        if report.overall_score is not None and report.overall_score < 75:
            tags.extend(["tighter mix", "clean master"])

        if report.track.mode.value == "instrumental":
            tags.append("instrumental focus")
        else:
            tags.append("clear lead vocal space")

        return ", ".join(tags)

    @staticmethod
    def _style_reason(report: EvaluationReport) -> str:
        audio = report.audio
        reasons = []
        if audio.bpm:
            reasons.append(f"BPM {audio.bpm:.0f}")
        if audio.estimated_key and audio.estimated_key != "unknown":
            reasons.append(f"Key {audio.estimated_key}")
        if audio.duration_sec < 90:
            reasons.append("짧은 샘플이라 완성곡 구조 보강 필요")
        if audio.peak_amplitude >= 0.98:
            reasons.append("피크가 0 dBFS에 가까워 헤드룸 보강 필요")
        if audio.frequency_bands:
            reasons.append("주파수 밸런스 측정 가능")
        if report.overall_score is not None and report.overall_score < 75:
            reasons.append("점수상 수정 권장 구간")
        return ", ".join(reasons) + "을 기준으로 현재 스타일과 개선 방향을 나눴습니다."

    @staticmethod
    def _frequency_style(bands: dict[str, float]) -> str:
        if not bands:
            return "balanced tone"
        low = bands.get("sub_bass_20_60hz", 0.0) + bands.get("bass_60_250hz", 0.0)
        mid = bands.get("low_mid_250_500hz", 0.0) + bands.get("mid_500_2khz", 0.0)
        high = bands.get("presence_4k_8khz", 0.0) + bands.get("brilliance_8k_16khz", 0.0)
        if low >= mid and low >= high:
            return "bass focused"
        if high >= low and high >= mid:
            return "bright presence"
        if mid >= low and mid >= high:
            return "warm midrange"
        return "balanced tone"

    @staticmethod
    def _energy_style(sections) -> str:
        labels = {section.energy_label for section in sections}
        if len(labels) >= 3:
            return "dynamic section changes"
        if len(labels) == 2:
            return "moderate energy movement"
        if "High" in labels:
            return "high energy loop"
        if "Low" in labels:
            return "minimal energy"
        return "steady energy"


    @staticmethod
    def _evidence_label(item: str) -> str:
        labels = {
            "duration_too_short_for_music_judgment": "길이가 너무 짧아 음악적 완성도 판단은 제한적",
            "duration_demo_length": "데모 길이 구간",
            "duration_release_window": "일반 발매 길이 구간",
            "duration_measurable": "길이 측정 가능",
            "lyrics not provided": "가사 미제공",
            "non-ai mode": "일반 음악 모드",
            "instrumental mode": "연주곡 모드",
            "peak_headroom_risk": "피크가 너무 높아 헤드룸/클리핑 확인 필요",
            "ai_context_missing": "AI/Suno 프롬프트와 가사 근거 부족",
        }
        return labels.get(item, item)
    @staticmethod
    def _message_label(message: str) -> str:
        labels = {
            "Audio evidence indicates the file is measurable and has usable signal quality.": "오디오 파일이 정상적으로 측정 가능하며 기본 신호 품질이 사용 가능한 범위입니다.",
            "BPM/key/LUFS are computational estimates and need human listening confirmation.": "BPM/Key/LUFS는 계산 추정치이므로 최종 판단 전 청감 확인이 필요합니다.",
            "Use listening review or reference-track comparison before final release decisions.": "최종 발매 전 청감 리뷰 또는 기준곡 비교를 진행하십시오.",
            "Composition is estimated from section structure, energy movement, and hook evidence.": "작곡/구성은 섹션 구조, 에너지 흐름, 훅 근거를 기준으로 추정했습니다.",
            "Precise melody and harmony review needs chords, MIDI, or deeper audio analysis.": "정밀한 멜로디/화성 평가는 코드, MIDI, 또는 더 깊은 오디오 분석이 필요합니다.",
            "Provide lyrics/prompt sections and chord progression to improve this score.": "점수를 보강하려면 가사/프롬프트 섹션과 코드 진행 정보를 추가하십시오.",
            "Lyrics were not provided, so hook, pronunciation, and language quality are limited.": "가사가 제공되지 않아 훅, 발음감, 언어 품질 평가는 제한적입니다.",
            "Lyrics were not provided, so hook, pronunciation, and language quality are not scored from audio alone.": "가사가 제공되지 않아 훅, 발음감, 언어 품질은 음원만으로 점수화하지 않았습니다.",
            "The system does not infer lyric quality from audio alone.": "이 시스템은 음원만으로 가사 품질을 단정하지 않습니다.",
            "Provide lyrics or Suno Lyrics for a stronger lyricist review.": "더 정확한 작사가 관점 평가를 위해 가사 또는 Suno Lyrics를 제공하십시오.",
            "Production is estimated from section energy movement and prompt texture evidence.": "프로듀싱은 섹션별 에너지 변화와 프롬프트 질감 근거를 기준으로 추정했습니다.",
            "Instrument layout and vocal space are only proxies until stem or deeper analysis is added.": "스템 분리 또는 심화 분석 전까지 악기 배치와 보컬 공간감은 간접 지표입니다.",
            "Add rhythm, texture, vocal attitude, and space notes in the prompt.": "프롬프트에 리듬, 질감, 보컬 태도, 공간감 메모를 추가하십시오.",
            "Mix/master risk is estimated from RMS, peak, dynamic range, LUFS, and frequency-band proxies when available.": "믹싱/마스터링 위험도는 RMS, 피크, 다이내믹 범위, LUFS, 주파수 밴드 지표를 기준으로 추정했습니다.",
            "True peak, codec artifacts, and final release loudness still need dedicated mastering checks.": "True Peak, 코덱 아티팩트, 최종 발매 라우드니스는 별도 마스터링 점검이 필요합니다.",
            "Compare against platform loudness targets and a reference track before release.": "발매 전 플랫폼 라우드니스 목표와 기준곡을 비교하십시오.",
            "AI naturalness scoring is skipped in general music mode.": "일반 음악 모드에서는 AI 자연스러움 점수를 산정하지 않습니다.",
            "AI naturalness is estimated from AI-tool mentions, repetition, and label-only tag warnings.": "AI 음악 자연스러움은 AI 도구 언급, 반복 패턴, 라벨만 있는 태그 경고를 기준으로 추정했습니다.",
            "Actual vocal artifacts require listening or a specialized model.": "실제 보컬 아티팩트는 청감 확인 또는 전용 분석 모델이 필요합니다.",
            "Provide Suno/Udio prompt and Lyrics to evaluate prompt-result fit later.": "Suno/Udio 프롬프트와 가사를 제공하면 프롬프트와 결과물의 일치도를 더 정확히 볼 수 있습니다.",
            "Release fit is estimated from hook evidence, duration, energy points, and target platform.": "발매 적합성은 훅 근거, 길이, 에너지 포인트, 대상 플랫폼을 기준으로 추정했습니다.",
            "Views, playlist placement, and revenue are never guaranteed.": "조회수, 플레이리스트 편입, 수익은 보장할 수 없습니다.",
            "For A/B comparison, add Hook, Visual, Channel Fit, and Personal Taste inputs.": "A/B 비교를 위해 훅, 비주얼, 채널 적합성, 개인 취향 입력을 추가하십시오.",
        }
        return labels.get(message, message)
    @staticmethod
    def _verdict_label(verdict: Verdict) -> str:
        labels = {
            Verdict.PASS: "진행 가능",
            Verdict.REVISE: "수정 권장",
            Verdict.HOLD: "보류",
            Verdict.NOT_APPLICABLE: "해당 없음",
        }
        return labels.get(verdict, verdict.value)

    @staticmethod
    def _group_label(group: str) -> str:
        labels = {
            "Technical Audio": "기술적 오디오 품질",
            "Composition": "작곡/구성",
            "Lyrics and Hook": "가사/훅",
            "Production": "프로듀싱",
            "Mix and Master": "믹싱/마스터링",
            "AI Naturalness": "AI 음악 자연스러움",
            "Market and Release Fit": "시장성/발매 적합성",
        }
        return labels.get(group, group)

    @staticmethod
    def _band_label(name: str) -> str:
        labels = {
            "sub_bass_20_60hz": "서브베이스 20-60Hz",
            "bass_60_250hz": "베이스 60-250Hz",
            "low_mid_250_500hz": "로우미드 250-500Hz",
            "mid_500_2khz": "미드 500Hz-2kHz",
            "upper_mid_2k_4khz": "어퍼미드 2k-4kHz",
            "presence_4k_8khz": "프레즌스 4k-8kHz",
            "brilliance_8k_16khz": "브릴리언스 8k-16kHz",
        }
        return labels.get(name, name)




