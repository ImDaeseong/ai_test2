from __future__ import annotations

import math
from pathlib import Path
from xml.etree import ElementTree as ET

from app.core import EvaluationReport
from app.notation.transcription import NoteEvent, ScoreTranscriber, TranscriptionResult


class LeadSheetMusicXmlWriter:
    """Writes a MusicXML score from optional transcription plus analysis metadata."""

    KEY_FIFTHS = {
        "Cb": -7,
        "Gb": -6,
        "Db": -5,
        "Ab": -4,
        "Eb": -3,
        "Bb": -2,
        "F": -1,
        "C": 0,
        "G": 1,
        "D": 2,
        "A": 3,
        "E": 4,
        "B": 5,
        "F#": 6,
        "C#": 7,
    }
    DIVISIONS = 4
    BEATS = 4
    BEAT_TYPE = 4
    MEASURE_DURATION = DIVISIONS * BEATS

    def __init__(self, transcriber: ScoreTranscriber | None = None) -> None:
        self.transcriber = transcriber or ScoreTranscriber()

    def write(self, report: EvaluationReport, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "analysis_lead_sheet.musicxml"
        transcription = self.transcriber.transcribe(report.track.audio_path, report.audio.bpm)
        tree = ET.ElementTree(self._build_score(report, transcription))
        ET.indent(tree, space="  ")
        tree.write(path, encoding="utf-8", xml_declaration=True)
        return path

    def _build_score(self, report: EvaluationReport, transcription: TranscriptionResult) -> ET.Element:
        root = ET.Element("score-partwise", version="3.1")
        work = ET.SubElement(root, "work")
        ET.SubElement(work, "work-title").text = report.track.audio_path.stem
        identification = ET.SubElement(root, "identification")
        encoding = ET.SubElement(identification, "encoding")
        ET.SubElement(encoding, "software").text = "Music Insight Studio"
        ET.SubElement(encoding, "encoding-description").text = self._encoding_description(transcription)
        part_list = ET.SubElement(root, "part-list")
        score_part = ET.SubElement(part_list, "score-part", id="P1")
        ET.SubElement(score_part, "part-name").text = "Transcription Guide" if transcription.available else "Analysis Lead Sheet"
        part = ET.SubElement(root, "part", id="P1")
        if transcription.available:
            self._add_transcribed_measures(part, report, transcription)
        else:
            self._add_section_measures(part, report, transcription)
        return root

    @staticmethod
    def _encoding_description(transcription: TranscriptionResult) -> str:
        if transcription.available:
            return f"Generated from {transcription.provider} note events plus analysis metadata. Review before release."
        return "Generated from analysis metadata. This is a lead sheet/session chart, not exact transcription."

    def _add_transcribed_measures(self, part: ET.Element, report: EvaluationReport, transcription: TranscriptionResult) -> None:
        bpm = report.audio.bpm if report.audio.bpm > 0 else 120.0
        measure_sec = 60.0 / bpm * self.BEATS
        events_by_measure: dict[int, list[NoteEvent]] = {}
        for event in transcription.note_events:
            measure_number = max(1, int(event.start_sec // measure_sec) + 1)
            events_by_measure.setdefault(measure_number, []).append(event)
        last_measure = max(events_by_measure.keys(), default=1)
        for measure_number in range(1, last_measure + 1):
            measure = ET.SubElement(part, "measure", number=str(measure_number))
            if measure_number == 1:
                self._add_attributes(measure, report.audio.estimated_key)
                self._add_tempo(measure, report.audio.bpm)
                self._add_rehearsal(measure, "Transcription Guide")
                for warning in transcription.warnings:
                    self._add_words(measure, warning)
            self._add_notes_for_measure(measure, events_by_measure.get(measure_number, []), measure_number, measure_sec)
        self._add_limitations(part, last_measure + 1, transcription)

    def _add_notes_for_measure(self, measure: ET.Element, events: list[NoteEvent], measure_number: int, measure_sec: float) -> None:
        if not events:
            self._add_whole_rest(measure)
            return
        cursor = 0
        measure_start = (measure_number - 1) * measure_sec
        for event in sorted(events, key=lambda item: item.start_sec):
            start_units = self._time_to_divisions(event.start_sec - measure_start, measure_sec)
            if start_units > cursor:
                self._add_rest(measure, start_units - cursor)
                cursor = start_units
            duration_units = max(1, self._time_to_divisions(event.end_sec - event.start_sec, measure_sec))
            if cursor + duration_units > self.MEASURE_DURATION:
                duration_units = max(1, self.MEASURE_DURATION - cursor)
            self._add_pitched_note(measure, event, duration_units)
            cursor += duration_units
            if cursor >= self.MEASURE_DURATION:
                break
        if cursor < self.MEASURE_DURATION:
            self._add_rest(measure, self.MEASURE_DURATION - cursor)

    def _time_to_divisions(self, seconds: float, measure_sec: float) -> int:
        if measure_sec <= 0:
            return self.DIVISIONS
        return max(0, min(self.MEASURE_DURATION, int(round(seconds / measure_sec * self.MEASURE_DURATION))))

    def _add_section_measures(self, part: ET.Element, report: EvaluationReport, transcription: TranscriptionResult) -> None:
        sections = report.audio.section_energies or [None]
        for index, section in enumerate(sections, start=1):
            measure = ET.SubElement(part, "measure", number=str(index))
            if index == 1:
                self._add_attributes(measure, report.audio.estimated_key)
                self._add_tempo(measure, report.audio.bpm)
                for warning in transcription.warnings:
                    self._add_words(measure, warning)
            label = "Full Track" if section is None else f"{section.name} - {section.energy_label} energy"
            self._add_rehearsal(measure, label)
            self._add_whole_rest(measure)
            if section is not None:
                self._add_words(measure, f"{section.start_sec:.1f}s-{section.end_sec:.1f}s, RMS {section.mean_rms:.4f}")
        self._add_limitations(part, len(sections) + 1, transcription)

    def _add_attributes(self, measure: ET.Element, key_name: str) -> None:
        attributes = ET.SubElement(measure, "attributes")
        ET.SubElement(attributes, "divisions").text = str(self.DIVISIONS)
        key = ET.SubElement(attributes, "key")
        ET.SubElement(key, "fifths").text = str(self.KEY_FIFTHS.get(key_name, 0))
        time = ET.SubElement(attributes, "time")
        ET.SubElement(time, "beats").text = str(self.BEATS)
        ET.SubElement(time, "beat-type").text = str(self.BEAT_TYPE)
        clef = ET.SubElement(attributes, "clef")
        ET.SubElement(clef, "sign").text = "G"
        ET.SubElement(clef, "line").text = "2"

    @staticmethod
    def _add_tempo(measure: ET.Element, bpm: float) -> None:
        if bpm <= 0:
            return
        direction = ET.SubElement(measure, "direction", placement="above")
        direction_type = ET.SubElement(direction, "direction-type")
        metronome = ET.SubElement(direction_type, "metronome")
        ET.SubElement(metronome, "beat-unit").text = "quarter"
        ET.SubElement(metronome, "per-minute").text = f"{bpm:.0f}"
        sound = ET.SubElement(direction, "sound")
        sound.set("tempo", f"{bpm:.0f}")

    @staticmethod
    def _add_rehearsal(measure: ET.Element, label: str) -> None:
        direction = ET.SubElement(measure, "direction", placement="above")
        direction_type = ET.SubElement(direction, "direction-type")
        ET.SubElement(direction_type, "rehearsal").text = label

    @staticmethod
    def _add_words(measure: ET.Element, text: str) -> None:
        direction = ET.SubElement(measure, "direction", placement="below")
        direction_type = ET.SubElement(direction, "direction-type")
        ET.SubElement(direction_type, "words").text = text

    def _add_pitched_note(self, measure: ET.Element, event: NoteEvent, duration: int) -> None:
        note = ET.SubElement(measure, "note")
        pitch = ET.SubElement(note, "pitch")
        step, alter, octave = event.pitch_name
        ET.SubElement(pitch, "step").text = step
        if alter:
            ET.SubElement(pitch, "alter").text = str(alter)
        ET.SubElement(pitch, "octave").text = str(octave)
        ET.SubElement(note, "duration").text = str(duration)
        ET.SubElement(note, "type").text = self._duration_type(duration)

    def _add_rest(self, measure: ET.Element, duration: int) -> None:
        duration = max(1, duration)
        note = ET.SubElement(measure, "note")
        ET.SubElement(note, "rest")
        ET.SubElement(note, "duration").text = str(duration)
        ET.SubElement(note, "type").text = self._duration_type(duration)

    def _add_whole_rest(self, measure: ET.Element) -> None:
        self._add_rest(measure, self.MEASURE_DURATION)

    @staticmethod
    def _duration_type(duration: int) -> str:
        if duration >= 16:
            return "whole"
        if duration >= 8:
            return "half"
        if duration >= 4:
            return "quarter"
        if duration >= 2:
            return "eighth"
        return "16th"

    def _add_limitations(self, part: ET.Element, measure_number: int, transcription: TranscriptionResult) -> None:
        measure = ET.SubElement(part, "measure", number=str(measure_number))
        self._add_rehearsal(measure, "Limitations")
        if transcription.available:
            self._add_words(measure, "Automatic transcription guide only; verify melody, rhythm, chords, and lyrics by ear before publishing.")
        else:
            self._add_words(measure, "No melody/chord transcription; use as analysis guide only.")
        self._add_whole_rest(measure)

