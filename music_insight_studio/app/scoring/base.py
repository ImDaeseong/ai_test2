from __future__ import annotations

from dataclasses import dataclass

from app.core import AnalysisMode, AudioFeatures, ScoreResult, TextFeatures, Verdict


@dataclass(frozen=True)
class ScoringContext:
    audio: AudioFeatures
    text: TextFeatures
    mode: AnalysisMode
    target_platform: str = "general"


class BaseScorer:
    group = "Base"
    criteria_file = ""

    def score(self, context: ScoringContext) -> ScoreResult:
        raise NotImplementedError

    def result(self, score: float | None, verdict: Verdict, evidence: list[str], reason: str, uncertainty: str = "", next_action: str = "") -> ScoreResult:
        return ScoreResult(self.group, score, verdict, evidence, reason, uncertainty, next_action, self.criteria_file)


def verdict_from_score(score: float) -> Verdict:
    if score >= 70:
        return Verdict.PASS
    if score >= 40:
        return Verdict.REVISE
    return Verdict.HOLD


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))
