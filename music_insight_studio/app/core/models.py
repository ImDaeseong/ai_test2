from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class AnalysisMode(str, Enum):
    AUTO = "auto"
    GENERAL = "general"
    AI_MUSIC = "ai_music"
    INSTRUMENTAL = "instrumental"


class Verdict(str, Enum):
    PASS = "PASS"
    REVISE = "REVISE"
    HOLD = "HOLD"
    NOT_APPLICABLE = "N/A"


@dataclass(frozen=True)
class TrackInput:
    audio_path: Path
    mode: AnalysisMode = AnalysisMode.AUTO
    lyrics: str = ""
    prompt: str = ""
    target_platform: str = "general"


@dataclass
class SectionEnergy:
    name: str
    start_sec: float
    end_sec: float
    mean_rms: float
    energy_label: str


@dataclass
class AudioFeatures:
    available: bool
    file_path: str
    file_name: str
    extension: str
    duration_sec: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    rms_mean: float = 0.0
    rms_std: float = 0.0
    peak_amplitude: float = 0.0
    dynamic_range_db: float = 0.0
    bpm: float = 0.0
    bpm_confidence: float = 0.0
    estimated_key: str = "unknown"
    lufs_integrated: float | None = None
    frequency_bands: dict[str, float] = field(default_factory=dict)
    section_energies: list[SectionEnergy] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def duration_label(self) -> str:
        minutes, seconds = divmod(int(self.duration_sec), 60)
        return f"{minutes}:{seconds:02d}"


@dataclass
class TextFeatures:
    has_lyrics: bool = False
    has_prompt: bool = False
    section_names: list[str] = field(default_factory=list)
    lyric_line_count: int = 0
    repeated_line_count: int = 0
    hook_candidates: list[str] = field(default_factory=list)
    ai_tool_mentions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ScoreResult:
    group: str
    score: float | None
    verdict: Verdict
    evidence: list[str]
    reason: str
    uncertainty: str = ""
    next_action: str = ""
    criteria_file: str = ""


@dataclass
class EvaluationReport:
    track: TrackInput
    audio: AudioFeatures
    text: TextFeatures
    scores: list[ScoreResult]
    overall_score: float | None
    overall_verdict: Verdict
    hold_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["audio"]["duration_label"] = self.audio.duration_label
        data["track"]["audio_path"] = str(self.track.audio_path)
        data["track"]["mode"] = self.track.mode.value
        data["overall_verdict"] = self.overall_verdict.value
        for score in data["scores"]:
            score["verdict"] = score["verdict"].value
        return data

