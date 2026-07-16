from __future__ import annotations

MIN_REVIEWABLE_DURATION_SEC = 10.0
MIN_FULL_TRACK_DURATION_SEC = 30.0
RELEASE_DURATION_MIN_SEC = 90.0
RELEASE_DURATION_MAX_SEC = 240.0
PEAK_HEADROOM_LIMIT = 0.98
MIN_SIGNAL_RMS = 0.01
MIN_DYNAMIC_RANGE_DB = 3.0


def cap_for_short_duration(score: float, duration_sec: float, cap: float) -> float:
    return min(score, cap) if duration_sec < MIN_REVIEWABLE_DURATION_SEC else score


def duration_evidence(duration_sec: float) -> str:
    if duration_sec < MIN_REVIEWABLE_DURATION_SEC:
        return "duration_too_short_for_music_judgment"
    if duration_sec < MIN_FULL_TRACK_DURATION_SEC:
        return "duration_demo_length"
    if RELEASE_DURATION_MIN_SEC <= duration_sec <= RELEASE_DURATION_MAX_SEC:
        return "duration_release_window"
    return "duration_measurable"
