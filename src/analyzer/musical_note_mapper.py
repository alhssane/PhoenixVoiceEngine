"""
Phoenix Voice Studio
Musical Note Mapper

Converts cleaned F0 frames into musical note information.

Pipeline:

    Clean F0
       ↓
    Hz → MIDI
       ↓
    MIDI → Note Name
       ↓
    Temporal Grouping
       ↓
    Musical Note Timeline
"""

from dataclasses import dataclass
from typing import Any

import math


# ============================================================
# DATA MODELS
# ============================================================


@dataclass
class MusicalNote:

    index: int

    start_time: float
    end_time: float
    duration: float

    midi: float
    note_name: str

    octave: int

    frequency_hz: float

    confidence: float

    voiced_ratio: float

    source_frames: int

    corrected_frames: int

    def to_dict(self) -> dict[str, Any]:

        return {
            "index": self.index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "midi": self.midi,
            "note_name": self.note_name,
            "octave": self.octave,
            "frequency_hz": self.frequency_hz,
            "confidence": self.confidence,
            "voiced_ratio": self.voiced_ratio,
            "source_frames": self.source_frames,
            "corrected_frames": self.corrected_frames,
        }


@dataclass
class PitchTimeline:

    file_name: str
    duration: float

    notes: list[MusicalNote]

    total_notes: int

    voiced_duration: float

    voiced_coverage: float

    average_confidence: float

    pitch_min_midi: float
    pitch_max_midi: float

    pitch_center_midi: float

    def to_dict(self) -> dict[str, Any]:

        return {
            "file_name": self.file_name,
            "duration": self.duration,
            "total_notes": self.total_notes,
            "voiced_duration": self.voiced_duration,
            "voiced_coverage": self.voiced_coverage,
            "average_confidence": self.average_confidence,
            "pitch_min_midi": self.pitch_min_midi,
            "pitch_max_midi": self.pitch_max_midi,
            "pitch_center_midi": self.pitch_center_midi,
            "notes": [
                note.to_dict()
                for note in self.notes
            ],
        }


# ============================================================
# MAPPER
# ============================================================


class MusicalNoteMapper:
    """
    Converts cleaned pitch frames into a musical timeline.

    Important:

    This stage does NOT alter the original audio.

    It only creates a structured musical representation.
    """

    NOTE_NAMES = (
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    )

    def __init__(
        self,
        minimum_confidence: float = 0.20,
        minimum_note_duration: float = 0.075,
        merge_tolerance_semitones: float = 0.50,
        gap_tolerance: float = 0.075,
    ):

        self.minimum_confidence = (
            minimum_confidence
        )

        self.minimum_note_duration = (
            minimum_note_duration
        )

        self.merge_tolerance = (
            merge_tolerance_semitones
        )

        self.gap_tolerance = (
            gap_tolerance
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def map(
        self,
        cleanup_report,
    ) -> PitchTimeline:

        frames = cleanup_report.frames

        if not frames:

            return PitchTimeline(
                file_name=cleanup_report.file_name,
                duration=cleanup_report.duration,
                notes=[],
                total_notes=0,
                voiced_duration=0.0,
                voiced_coverage=0.0,
                average_confidence=0.0,
                pitch_min_midi=0.0,
                pitch_max_midi=0.0,
                pitch_center_midi=0.0,
            )

        # ----------------------------------------------------
        # Convert valid frames to pitch points.
        # ----------------------------------------------------

        points = []

        for frame in frames:

            if (
                not frame.voiced
                or frame.f0 <= 0
                or frame.confidence
                < self.minimum_confidence
            ):

                continue

            midi = self.hz_to_midi(
                frame.f0
            )

            points.append(
                {
                    "time": float(
                        frame.time
                    ),
                    "midi": midi,
                    "f0": float(
                        frame.f0
                    ),
                    "confidence": float(
                        frame.confidence
                    ),
                    "corrected": bool(
                        getattr(
                            frame,
                            "corrected",
                            False,
                        )
                    ),
                }
            )

        if not points:

            return PitchTimeline(
                file_name=cleanup_report.file_name,
                duration=cleanup_report.duration,
                notes=[],
                total_notes=0,
                voiced_duration=0.0,
                voiced_coverage=0.0,
                average_confidence=0.0,
                pitch_min_midi=0.0,
                pitch_max_midi=0.0,
                pitch_center_midi=0.0,
            )

        # ----------------------------------------------------
        # Group frames into musical notes.
        # ----------------------------------------------------

        groups = self._group_pitch_points(
            points
        )

        notes = []

        for index, group in enumerate(
            groups,
            start=1,
        ):

            note = self._build_note(
                index,
                group,
            )

            if note is not None:

                notes.append(
                    note
                )

        # ----------------------------------------------------
        # Statistics.
        # ----------------------------------------------------

        voiced_duration = sum(
            note.duration
            for note in notes
        )

        voiced_coverage = (
            voiced_duration
            / max(
                cleanup_report.duration,
                0.001,
            )
            * 100.0
        )

        all_midi = [
            point["midi"]
            for point in points
        ]

        all_confidence = [
            point["confidence"]
            for point in points
        ]

        return PitchTimeline(
            file_name=(
                cleanup_report.file_name
            ),

            duration=(
                cleanup_report.duration
            ),

            notes=notes,

            total_notes=len(notes),

            voiced_duration=round(
                voiced_duration,
                3,
            ),

            voiced_coverage=round(
                voiced_coverage,
                2,
            ),

            average_confidence=round(
                sum(all_confidence)
                / len(all_confidence)
                * 100.0,
                2,
            ),

            pitch_min_midi=round(
                min(all_midi),
                2,
            ),

            pitch_max_midi=round(
                max(all_midi),
                2,
            ),

            pitch_center_midi=round(
                self._median(
                    all_midi
                ),
                2,
            ),
        )

    # ========================================================
    # GROUP PITCH POINTS
    # ========================================================

    def _group_pitch_points(
        self,
        points,
    ):

        groups = []

        current = []

        for point in points:

            if not current:

                current = [
                    point
                ]

                continue

            previous = current[-1]

            time_gap = (
                point["time"]
                - previous["time"]
            )

            pitch_difference = abs(
                point["midi"]
                - previous["midi"]
            )

            # ------------------------------------------------
            # Continue same note.
            # ------------------------------------------------

            if (
                time_gap
                <= self.gap_tolerance
                and pitch_difference
                <= self.merge_tolerance
            ):

                current.append(
                    point
                )

                continue

            # ------------------------------------------------
            # Finish current note.
            # ------------------------------------------------

            groups.append(
                current
            )

            current = [
                point
            ]

        if current:

            groups.append(
                current
            )

        return groups

    # ========================================================
    # BUILD NOTE
    # ========================================================

    def _build_note(
        self,
        index: int,
        points,
    ) -> MusicalNote | None:

        if not points:

            return None

        start_time = (
            points[0]["time"]
        )

        end_time = (
            points[-1]["time"]
        )

        # Estimate the final frame duration
        # from neighboring pitch frames.
        if len(points) >= 2:

            frame_duration = (
                points[-1]["time"]
                - points[-2]["time"]
            )

            if frame_duration <= 0:

                frame_duration = 0.025

        else:

            frame_duration = 0.025

        end_time += frame_duration

        duration = (
            end_time
            - start_time
        )

        if (
            duration
            < self.minimum_note_duration
        ):

            return None

        midi_values = [
            point["midi"]
            for point in points
        ]

        frequency_values = [
            point["f0"]
            for point in points
        ]

        confidence_values = [
            point["confidence"]
            for point in points
        ]

        corrected_count = sum(
            1
            for point in points
            if point["corrected"]
        )

        # ----------------------------------------------------
        # Use median MIDI instead of mean.
        #
        # This protects against occasional pitch estimation
        # noise inside a note.
        # ----------------------------------------------------

        midi = self._median(
            midi_values
        )

        frequency = self.midi_to_hz(
            midi
        )

        note_name, octave = (
            self.midi_to_note(
                midi
            )
        )

        confidence = (
            sum(
                confidence_values
            )
            / len(
                confidence_values
            )
            * 100.0
        )

        return MusicalNote(
            index=index,

            start_time=round(
                start_time,
                3,
            ),

            end_time=round(
                end_time,
                3,
            ),

            duration=round(
                duration,
                3,
            ),

            midi=round(
                midi,
                3,
            ),

            note_name=note_name,

            octave=octave,

            frequency_hz=round(
                frequency,
                3,
            ),

            confidence=round(
                confidence,
                2,
            ),

            voiced_ratio=100.0,

            source_frames=len(
                points
            ),

            corrected_frames=(
                corrected_count
            ),
        )

    # ========================================================
    # HZ → MIDI
    # ========================================================

    @staticmethod
    def hz_to_midi(
        frequency: float,
    ) -> float:

        if frequency <= 0:

            return 0.0

        return (
            69.0
            + 12.0
            * math.log2(
                frequency
                / 440.0
            )
        )

    # ========================================================
    # MIDI → HZ
    # ========================================================

    @staticmethod
    def midi_to_hz(
        midi: float,
    ) -> float:

        return (
            440.0
            * 2.0
            ** (
                (
                    midi
                    - 69.0
                )
                / 12.0
            )
        )

    # ========================================================
    # MIDI → NOTE
    # ========================================================

    def midi_to_note(
        self,
        midi: float,
    ):

        rounded_midi = int(
            round(midi)
        )

        note_index = (
            rounded_midi
            % 12
        )

        octave = (
            rounded_midi
            // 12
            - 1
        )

        note_name = (
            self.NOTE_NAMES[
                note_index
            ]
        )

        return (
            note_name,
            octave,
        )

    # ========================================================
    # MEDIAN
    # ========================================================

    @staticmethod
    def _median(
        values,
    ) -> float:

        if not values:

            return 0.0

        ordered = sorted(
            values
        )

        middle = len(
            ordered
        ) // 2

        if (
            len(ordered)
            % 2
            == 0
        ):

            return (
                ordered[middle - 1]
                + ordered[middle]
            ) / 2.0

        return ordered[
            middle
        ]