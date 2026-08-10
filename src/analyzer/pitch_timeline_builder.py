"""
Phoenix Voice Studio
Pitch Timeline Builder

Builds a continuous musical pitch timeline from:

    Pitch Cleanup Report
            +
    Musical Note Timeline

The builder preserves frame-level pitch information while
associating every frame with its musical note.

This is a read-only analysis stage.
The original audio is never modified.
"""

from dataclasses import dataclass
from typing import Any
import math


# ============================================================
# DATA MODELS
# ============================================================


@dataclass
class PitchTimelineFrame:

    index: int

    time: float

    f0_hz: float

    midi: float

    note_name: str

    octave: int

    confidence: float

    voiced: bool

    corrected: bool

    correction_type: str

    note_index: int | None

    note_start: float | None

    note_end: float | None

    note_duration: float | None

    def to_dict(self) -> dict[str, Any]:

        return {
            "index": self.index,
            "time": self.time,
            "f0_hz": self.f0_hz,
            "midi": self.midi,
            "note_name": self.note_name,
            "octave": self.octave,
            "confidence": self.confidence,
            "voiced": self.voiced,
            "corrected": self.corrected,
            "correction_type": self.correction_type,
            "note_index": self.note_index,
            "note_start": self.note_start,
            "note_end": self.note_end,
            "note_duration": self.note_duration,
        }


@dataclass
class PitchTimelineSegment:

    index: int

    start_time: float

    end_time: float

    duration: float

    note_name: str

    octave: int

    midi_center: float

    f0_center_hz: float

    frame_count: int

    corrected_frames: int

    average_confidence: float

    frames: list[PitchTimelineFrame]

    def to_dict(self) -> dict[str, Any]:

        return {
            "index": self.index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "note_name": self.note_name,
            "octave": self.octave,
            "midi_center": self.midi_center,
            "f0_center_hz": self.f0_center_hz,
            "frame_count": self.frame_count,
            "corrected_frames": self.corrected_frames,
            "average_confidence": self.average_confidence,
            "frames": [
                frame.to_dict()
                for frame in self.frames
            ],
        }


@dataclass
class MasterPitchTimeline:

    file_name: str

    duration: float

    total_frames: int

    voiced_frames: int

    unvoiced_frames: int

    voiced_coverage: float

    average_confidence: float

    corrected_frames: int

    correction_coverage: float

    segments: list[PitchTimelineSegment]

    frames: list[PitchTimelineFrame]

    def to_dict(self) -> dict[str, Any]:

        return {
            "file_name": self.file_name,
            "duration": self.duration,
            "total_frames": self.total_frames,
            "voiced_frames": self.voiced_frames,
            "unvoiced_frames": self.unvoiced_frames,
            "voiced_coverage": self.voiced_coverage,
            "average_confidence": self.average_confidence,
            "corrected_frames": self.corrected_frames,
            "correction_coverage": self.correction_coverage,
            "segments": [
                segment.to_dict()
                for segment in self.segments
            ],
            "frames": [
                frame.to_dict()
                for frame in self.frames
            ],
        }


# ============================================================
# BUILDER
# ============================================================


class PitchTimelineBuilder:
    """
    Builds the master pitch timeline.

    Responsibilities:

    1. Preserve every cleanup frame.
    2. Convert F0 to MIDI.
    3. Map frames to musical notes.
    4. Preserve correction metadata.
    5. Build note-level segments.
    6. Calculate timeline statistics.

    This class does NOT modify the audio.
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
        frame_tolerance: float = 0.08,
    ):

        self.frame_tolerance = (
            frame_tolerance
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def build(
        self,
        cleanup_report,
        note_timeline,
    ) -> MasterPitchTimeline:

        raw_frames = cleanup_report.frames

        if not raw_frames:

            return MasterPitchTimeline(
                file_name=cleanup_report.file_name,
                duration=cleanup_report.duration,
                total_frames=0,
                voiced_frames=0,
                unvoiced_frames=0,
                voiced_coverage=0.0,
                average_confidence=0.0,
                corrected_frames=0,
                correction_coverage=0.0,
                segments=[],
                frames=[],
            )

        timeline_frames = []

        for index, frame in enumerate(
            raw_frames
        ):

            f0 = float(
                getattr(
                    frame,
                    "f0",
                    0.0,
                )
            )

            confidence = float(
                getattr(
                    frame,
                    "confidence",
                    0.0,
                )
            )

            voiced = bool(
                getattr(
                    frame,
                    "voiced",
                    False,
                )
            )

            corrected = bool(
                getattr(
                    frame,
                    "corrected",
                    False,
                )
            )

            correction_type = str(
                getattr(
                    frame,
                    "correction_type",
                    "",
                )
                or ""
            )

            if voiced and f0 > 0:

                midi = (
                    self.hz_to_midi(
                        f0
                    )
                )

                note_name, octave = (
                    self.midi_to_note(
                        midi
                    )
                )

            else:

                midi = 0.0
                note_name = ""
                octave = -1

            note = self._find_note(
                frame.time,
                note_timeline.notes,
                voiced=voiced and f0 > 0,
            )

            if note is not None:

                note_index = (
                    note.index
                )

                note_start = (
                    note.start_time
                )

                note_end = (
                    note.end_time
                )

                note_duration = (
                    note.duration
                )

            else:

                note_index = None
                note_start = None
                note_end = None
                note_duration = None

            timeline_frame = (
                PitchTimelineFrame(
                    index=index,

                    time=round(
                        float(frame.time),
                        6,
                    ),

                    f0_hz=round(
                        f0,
                        6,
                    ),

                    midi=round(
                        midi,
                        6,
                    ),

                    note_name=note_name,

                    octave=octave,

                    confidence=round(
                        confidence,
                        6,
                    ),

                    voiced=voiced,

                    corrected=corrected,

                    correction_type=(
                        correction_type
                    ),

                    note_index=(
                        note_index
                    ),

                    note_start=(
                        note_start
                    ),

                    note_end=(
                        note_end
                    ),

                    note_duration=(
                        note_duration
                    ),
                )
            )

            timeline_frames.append(
                timeline_frame
            )

        segments = (
            self._build_segments(
                timeline_frames,
                note_timeline,
            )
        )

        total_frames = len(
            timeline_frames
        )

        voiced_frames = sum(
            1
            for frame in timeline_frames
            if frame.voiced
            and frame.f0_hz > 0
        )

        unvoiced_frames = (
            total_frames
            - voiced_frames
        )

        corrected_frames = sum(
            1
            for frame in timeline_frames
            if frame.corrected
        )

        voiced_coverage = (
            voiced_frames
            / max(
                total_frames,
                1,
            )
            * 100.0
        )

        corrected_coverage = (
            corrected_frames
            / max(
                voiced_frames,
                1,
            )
            * 100.0
        )

        voiced_confidences = [
            frame.confidence
            for frame in timeline_frames
            if frame.voiced
            and frame.f0_hz > 0
        ]

        average_confidence = (
            sum(
                voiced_confidences
            )
            / len(
                voiced_confidences
            )
            * 100.0
            if voiced_confidences
            else 0.0
        )

        return MasterPitchTimeline(
            file_name=(
                cleanup_report.file_name
            ),

            duration=(
                cleanup_report.duration
            ),

            total_frames=(
                total_frames
            ),

            voiced_frames=(
                voiced_frames
            ),

            unvoiced_frames=(
                unvoiced_frames
            ),

            voiced_coverage=round(
                voiced_coverage,
                2,
            ),

            average_confidence=round(
                average_confidence,
                2,
            ),

            corrected_frames=(
                corrected_frames
            ),

            correction_coverage=round(
                corrected_coverage,
                2,
            ),

            segments=segments,

            frames=timeline_frames,
        )

    # ========================================================
    # FIND NOTE
    # ========================================================

    def _find_note(
        self,
        time: float,
        notes,
        voiced: bool = False,
    ):
        """
        Find the musical note that owns a frame.

        Exact MusicalNoteMapper intervals always have priority.
        For voiced frames that fall inside a small timing gap between
        two notes, ownership is resolved using the midpoint between
        the adjacent note boundaries. This keeps the Master Timeline
        continuous without changing the detected musical notes.

        Unvoiced frames are never force-assigned to a musical note.
        """

        if not notes:
            return None

        ordered = sorted(
            list(notes),
            key=lambda note: (
                float(note.start_time),
                float(note.end_time),
                int(getattr(note, "index", 0)),
            ),
        )

        # --------------------------------------------------------
        # 1. Exact source-note ownership.
        # --------------------------------------------------------

        for index, note in enumerate(ordered):

            is_last = index == len(ordered) - 1

            if (
                float(note.start_time)
                <= time
                < float(note.end_time)
            ):
                return note

            if (
                is_last
                and float(note.start_time)
                <= time
                <= float(note.end_time)
            ):
                return note

        # Unvoiced frames are allowed to remain outside musical notes.
        if not voiced:
            return None

        # --------------------------------------------------------
        # 2. Resolve gaps between notes by midpoint ownership.
        #
        # Example:
        #     A: 10.0 -> 20.0
        #     B: 20.4 -> 30.0
        #
        # The gap is split at 20.2:
        #     A owns through 20.2
        #     B owns from 20.2
        # --------------------------------------------------------

        for index, note in enumerate(ordered):

            start = float(note.start_time)
            end = float(note.end_time)

            if index == 0:
                left = start
            else:
                previous = ordered[index - 1]
                previous_end = float(
                    previous.end_time
                )

                if previous_end <= start:
                    left = (
                        previous_end + start
                    ) / 2.0
                else:
                    left = start

            if index == len(ordered) - 1:
                right = end
            else:
                following = ordered[index + 1]
                following_start = float(
                    following.start_time
                )

                if end <= following_start:
                    right = (
                        end + following_start
                    ) / 2.0
                else:
                    right = following_start

            if (
                left <= time < right
            ):
                return note

            if (
                index == len(ordered) - 1
                and left <= time <= right
            ):
                return note

        # --------------------------------------------------------
        # 3. Floating-point fallback near a boundary.
        # --------------------------------------------------------

        nearest_note = None
        nearest_distance = float("inf")

        for note in ordered:

            distance_to_start = abs(
                time - float(note.start_time)
            )

            distance_to_end = abs(
                time - float(note.end_time)
            )

            distance = min(
                distance_to_start,
                distance_to_end,
            )

            if (
                distance <= self.frame_tolerance
                and distance < nearest_distance
            ):
                nearest_note = note
                nearest_distance = distance

        return nearest_note

    # ========================================================
    # BUILD SEGMENTS
    # ========================================================

    def _build_segments(
        self,
        frames,
        note_timeline,
    ):
        """
        Build non-overlapping note-level segments.

        Segment boundaries use the same midpoint ownership rule as
        _find_note(), so voiced frames located in gaps are represented
        by exactly one segment and segments never overlap.
        """

        segments = []

        notes = sorted(
            list(
                getattr(
                    note_timeline,
                    "notes",
                    [],
                )
                or []
            ),
            key=lambda note: (
                float(note.start_time),
                float(note.end_time),
                int(getattr(note, "index", 0)),
            ),
        )

        if not notes:
            return segments

        # --------------------------------------------------------
        # Calculate the exact ownership boundary of every note.
        # --------------------------------------------------------

        boundaries = []

        for index, note in enumerate(notes):

            start = float(note.start_time)
            end = float(note.end_time)

            if index == 0:
                left = start
            else:
                previous_end = float(
                    notes[index - 1].end_time
                )

                if previous_end <= start:
                    left = (
                        previous_end + start
                    ) / 2.0
                else:
                    left = start

            if index == len(notes) - 1:
                right = end
            else:
                next_start = float(
                    notes[index + 1].start_time
                )

                if end <= next_start:
                    right = (
                        end + next_start
                    ) / 2.0
                else:
                    right = next_start

            # Absolute safety against malformed note intervals.
            if right <= left:
                right = end

            boundaries.append(
                (
                    left,
                    right,
                )
            )

        previous_end = None

        for position, note in enumerate(notes):

            start_time, end_time = boundaries[
                position
            ]

            if previous_end is not None:
                start_time = max(
                    start_time,
                    previous_end,
                )

            if end_time <= start_time:
                continue

            note_index = getattr(
                note,
                "index",
                None,
            )

            note_frames = [
                frame
                for frame in frames
                if frame.note_index == note_index
                and start_time <= frame.time < end_time
            ]

            if position == len(notes) - 1:
                note_frames = [
                    frame
                    for frame in frames
                    if frame.note_index == note_index
                    and start_time <= frame.time <= end_time
                ]

            if not note_frames:
                previous_end = end_time
                continue

            voiced_frames = [
                frame
                for frame in note_frames
                if frame.voiced
                and frame.f0_hz > 0
            ]

            if not voiced_frames:
                previous_end = end_time
                continue

            midi_values = [
                frame.midi
                for frame in voiced_frames
                if frame.midi > 0
            ]

            f0_values = [
                frame.f0_hz
                for frame in voiced_frames
                if frame.f0_hz > 0
            ]

            confidence_values = [
                frame.confidence
                for frame in voiced_frames
            ]

            corrected_count = sum(
                1
                for frame in voiced_frames
                if frame.corrected
            )

            segment = PitchTimelineSegment(
                index=note_index,
                start_time=round(
                    start_time,
                    6,
                ),
                end_time=round(
                    end_time,
                    6,
                ),
                duration=round(
                    end_time - start_time,
                    6,
                ),
                note_name=note.note_name,
                octave=note.octave,
                midi_center=round(
                    self._median(midi_values),
                    6,
                ),
                f0_center_hz=round(
                    self._median(f0_values),
                    6,
                ),
                frame_count=len(note_frames),
                corrected_frames=corrected_count,
                average_confidence=round(
                    (
                        sum(confidence_values)
                        / len(confidence_values)
                        * 100.0
                    ),
                    2,
                ),
                frames=note_frames,
            )

            segments.append(segment)
            previous_end = end_time

        return segments

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

        return (
            self.NOTE_NAMES[
                note_index
            ],
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

        middle = (
            len(ordered)
            // 2
        )

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