from __future__ import annotations

from app.core import AnalysisMode, AudioFeatures, ScoreResult, TextFeatures, Verdict
from app.scoring.base import ScoringContext
from app.scoring.specialists import AIMusicScorer, ComposerScorer, LyricistScorer, MarketReleaseScorer, MixMasterScorer, ProducerScorer, TechnicalAudioScorer


class ScoringEngine:
    DEFAULT_WEIGHTS = {
        "Technical Audio": 15,
        "Composition": 15,
        "Lyrics and Hook": 15,
        "Production": 15,
        "Mix and Master": 15,
        "AI Naturalness": 10,
        "Market and Release Fit": 15,
    }

    def __init__(self) -> None:
        self.scorers = [TechnicalAudioScorer(), ComposerScorer(), LyricistScorer(), ProducerScorer(), MixMasterScorer(), AIMusicScorer(), MarketReleaseScorer()]

    def evaluate(self, audio: AudioFeatures, text: TextFeatures, mode: AnalysisMode = AnalysisMode.AUTO, target_platform: str = "general") -> tuple[list[ScoreResult], float | None, Verdict, list[str]]:
        resolved_mode = self._resolve_mode(mode, text)
        context = ScoringContext(audio, text, resolved_mode, target_platform)
        scores = [scorer.score(context) for scorer in self.scorers]
        hold_reasons = [score.reason for score in scores if score.verdict == Verdict.HOLD]
        if hold_reasons:
            return scores, None, Verdict.HOLD, hold_reasons
        applicable = [score for score in scores if score.score is not None and score.verdict != Verdict.NOT_APPLICABLE and self._weight_for(score.group, resolved_mode) > 0]
        if not applicable:
            return scores, None, Verdict.REVISE, []
        total_weight = sum(self._weight_for(score.group, resolved_mode) for score in applicable)
        weighted = sum((score.score or 0.0) * self._weight_for(score.group, resolved_mode) for score in applicable)
        overall = weighted / total_weight if total_weight else None
        if overall is None:
            verdict = Verdict.REVISE
        elif overall >= 70:
            verdict = Verdict.PASS
        elif overall >= 40:
            verdict = Verdict.REVISE
        else:
            verdict = Verdict.HOLD
        return scores, overall, verdict, []

    def _weight_for(self, group: str, mode: AnalysisMode) -> float:
        weights = dict(self.DEFAULT_WEIGHTS)
        if mode == AnalysisMode.INSTRUMENTAL:
            weights["Lyrics and Hook"] = 0
            weights["Composition"] += 7.5
            weights["Production"] += 7.5
        if mode == AnalysisMode.GENERAL:
            weights["AI Naturalness"] = 0
            weights["Production"] += 5
            weights["Mix and Master"] += 5
        return weights.get(group, 0)

    @staticmethod
    def _resolve_mode(mode: AnalysisMode, text: TextFeatures) -> AnalysisMode:
        if mode != AnalysisMode.AUTO:
            return mode
        if text.ai_tool_mentions:
            return AnalysisMode.AI_MUSIC
        return AnalysisMode.GENERAL
