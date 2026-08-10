"""
Phoenix Voice Studio
Vocal Phrase Detector

Detects continuous vocal phrases from the Master Pitch Timeline.
"""

from dataclasses import dataclass, field
from statistics import median
from typing import Any, List


@dataclass
class VocalPhrase:
    index: int
    start_time: float
    end_time: float
    duration: float

    frame_count: int
    voiced_frames: int
    unvoiced_frames: int
    voiced_coverage: float

    start_f0_hz: float
    end_f0_hz: float
    pitch_center_hz: float
    pitch_min_hz: float
    pitch_max_hz: float
    pitch_range_semitones: float

    start_midi: float
    end_midi: float
    pitch_center_midi: float

    average_confidence: float
    note_count: int

    note_names: List[str] = field(default_factory=list)
    frames: List[Any] = field(default_factory=list)
    segments: List[Any] = field(default_factory=list)

    def to_dict(self):
        return {
            "index": self.index,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "frame_count": self.frame_count,
            "voiced_frames": self.voiced_frames,
            "unvoiced_frames": self.unvoiced_frames,
            "voiced_coverage": self.voiced_coverage,
            "start_f0_hz": self.start_f0_hz,
            "end_f0_hz": self.end_f0_hz,
            "pitch_center_hz": self.pitch_center_hz,
            "pitch_min_hz": self.pitch_min_hz,
            "pitch_max_hz": self.pitch_max_hz,
            "pitch_range_semitones": self.pitch_range_semitones,
            "start_midi": self.start_midi,
            "end_midi": self.end_midi,
            "pitch_center_midi": self.pitch_center_midi,
            "average_confidence": self.average_confidence,
            "note_count": self.note_count,
            "note_names": list(self.note_names),
            "frames": [
                frame.to_dict() if hasattr(frame, "to_dict") else frame
                for frame in self.frames
            ],
            "segments": [
                segment.to_dict() if hasattr(segment, "to_dict") else segment
                for segment in self.segments
            ],
        }


@dataclass
class VocalPhraseReport:
    file_name: str
    duration: float
    total_frames: int

    phrase_count: int
    total_phrase_duration: float
    phrase_coverage: float
    average_phrase_duration: float

    phrases: List[VocalPhrase] = field(default_factory=list)

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "duration": self.duration,
            "total_frames": self.total_frames,
            "phrase_count": self.phrase_count,
            "total_phrase_duration": self.total_phrase_duration,
            "phrase_coverage": self.phrase_coverage,
            "average_phrase_duration": self.average_phrase_duration,
            "phrases": [phrase.to_dict() for phrase in self.phrases],
        }


class VocalPhraseDetector:
    """
    Detects vocal phrases from a MasterPitchTimeline.

    Important:
    This version performs a safe boundary clamp so phrase end times
    can never extend beyond the real timeline duration.
    """

    def __init__(
        self,
        max_gap: float = 0.45,
        minimum_phrase_duration: float = 0.50,
        minimum_phrase_frames: int = 3,
        merge_gap: float = 0.20,
    ):
        if max_gap <= 0:
            raise ValueError("max_gap must be greater than zero.")

        if minimum_phrase_duration <= 0:
            raise ValueError(
                "minimum_phrase_duration must be greater than zero."
            )

        if minimum_phrase_frames < 1:
            raise ValueError(
                "minimum_phrase_frames must be at least 1."
            )

        if merge_gap < 0:
            raise ValueError("merge_gap cannot be negative.")

        self.max_gap = float(max_gap)
        self.minimum_phrase_duration = float(
            minimum_phrase_duration
        )
        self.minimum_phrase_frames = int(
            minimum_phrase_frames
        )
        self.merge_gap = float(merge_gap)

    def analyze(
        self,
        timeline,
        activity_segments=None,
    ) -> VocalPhraseReport:

        frames = list(
            getattr(timeline, "frames", [])
        )

        duration = max(
            0.0,
            float(getattr(timeline, "duration", 0.0)),
        )

        file_name = str(
            getattr(timeline, "file_name", "unknown")
        )

        if not frames:
            return VocalPhraseReport(
                file_name=file_name,
                duration=round(duration, 3),
                total_frames=0,
                phrase_count=0,
                total_phrase_duration=0.0,
                phrase_coverage=0.0,
                average_phrase_duration=0.0,
                phrases=[],
            )

        voiced_frames = [
            frame
            for frame in frames
            if self._is_voiced(frame)
        ]

        voiced_frames.sort(
            key=self._frame_time
        )

        if not voiced_frames:
            return VocalPhraseReport(
                file_name=file_name,
                duration=round(duration, 3),
                total_frames=len(frames),
                phrase_count=0,
                total_phrase_duration=0.0,
                phrase_coverage=0.0,
                average_phrase_duration=0.0,
                phrases=[],
            )

        groups = self._split_into_groups(
            voiced_frames,
            activity_segments,
        )

        groups = self._filter_small_groups(groups)
        groups = self._merge_close_groups(groups)

        phrases = []

        for index, group in enumerate(groups, start=1):
            phrase = self._build_phrase(
                index=index,
                frames=group,
                timeline=timeline,
            )

            if phrase is not None:
                phrases.append(phrase)

        # Re-index after filtering/merging.
        for index, phrase in enumerate(
            phrases,
            start=1,
        ):
            phrase.index = index

        total_phrase_duration = sum(
            phrase.duration
            for phrase in phrases
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # Phrase intervals are now guaranteed to be inside the
        # timeline. This makes coverage mathematically bounded
        # by 100% (apart from negligible floating-point noise).
        # ----------------------------------------------------
        total_phrase_duration = min(
            total_phrase_duration,
            duration,
        )

        phrase_coverage = (
            total_phrase_duration
            / duration
            * 100.0
            if duration > 0
            else 0.0
        )

        phrase_coverage = min(
            100.0,
            max(0.0, phrase_coverage),
        )

        average_phrase_duration = (
            total_phrase_duration / len(phrases)
            if phrases
            else 0.0
        )

        return VocalPhraseReport(
            file_name=file_name,
            duration=round(duration, 3),
            total_frames=len(frames),
            phrase_count=len(phrases),
            total_phrase_duration=round(
                total_phrase_duration,
                3,
            ),
            phrase_coverage=round(
                phrase_coverage,
                2,
            ),
            average_phrase_duration=round(
                average_phrase_duration,
                3,
            ),
            phrases=phrases,
        )

    # ========================================================
    # FRAME HELPERS
    # ========================================================

    @staticmethod
    def _frame_time(frame):
        return float(
            getattr(frame, "time", 0.0)
        )

    @staticmethod
    def _f0(frame):
        if hasattr(frame, "f0_hz"):
            return float(
                getattr(frame, "f0_hz", 0.0)
            )

        return float(
            getattr(frame, "f0", 0.0)
        )

    @classmethod
    def _is_voiced(cls, frame):
        return bool(
            getattr(frame, "voiced", False)
        ) and cls._f0(frame) > 0

    @staticmethod
    def _confidence(frame):
        value = float(
            getattr(frame, "confidence", 0.0)
        )

        if value > 1.0:
            value /= 100.0

        return max(
            0.0,
            min(1.0, value),
        )

    # ========================================================
    # GROUPING
    # ========================================================

    def _split_into_groups(
        self,
        frames,
        activity_segments,
    ):
        if not frames:
            return []

        groups = [[frames[0]]]

        for previous, current in zip(
            frames,
            frames[1:],
        ):
            previous_time = self._frame_time(previous)
            current_time = self._frame_time(current)

            gap = current_time - previous_time

            should_split = (
                gap > self.max_gap
            )

            if (
                not should_split
                and activity_segments
                and self._crosses_activity_boundary(
                    previous_time,
                    current_time,
                    activity_segments,
                )
            ):
                should_split = True

            if should_split:
                groups.append([current])
            else:
                groups[-1].append(current)

        return groups

    @staticmethod
    def _crosses_activity_boundary(
        start,
        end,
        activity_segments,
    ):
        for segment in activity_segments:
            segment_start = float(
                getattr(
                    segment,
                    "start",
                    getattr(
                        segment,
                        "start_time",
                        0.0,
                    ),
                )
            )

            segment_end = float(
                getattr(
                    segment,
                    "end",
                    getattr(
                        segment,
                        "end_time",
                        0.0,
                    ),
                )
            )

            if (
                segment_start <= start
                and end <= segment_end
            ):
                return False

        return True

    def _filter_small_groups(self, groups):
        result = []

        for group in groups:
            if not group:
                continue

            start = self._frame_time(group[0])
            end = self._frame_time(group[-1])

            duration = end - start

            if (
                duration >= self.minimum_phrase_duration
                or len(group) >= self.minimum_phrase_frames
            ):
                result.append(group)

        return result

    def _merge_close_groups(self, groups):
        if len(groups) <= 1:
            return groups

        merged = [list(groups[0])]

        for group in groups[1:]:
            previous = merged[-1]

            previous_end = self._frame_time(
                previous[-1]
            )

            current_start = self._frame_time(
                group[0]
            )

            gap = current_start - previous_end

            if gap <= self.merge_gap:
                previous.extend(group)
            else:
                merged.append(list(group))

        return merged

    # ========================================================
    # PHRASE BUILDING
    # ========================================================

    def _build_phrase(
        self,
        index,
        frames,
        timeline,
    ):
        if not frames:
            return None

        frames = sorted(
            frames,
            key=self._frame_time,
        )

        timeline_duration = max(
            0.0,
            float(
                getattr(
                    timeline,
                    "duration",
                    0.0,
                )
            ),
        )

        start_time = max(
            0.0,
            self._frame_time(frames[0]),
        )

        last_time = max(
            start_time,
            self._frame_time(frames[-1]),
        )

        frame_duration = self._estimate_frame_duration(
            timeline
        )

        # ----------------------------------------------------
        # FIX:
        # Never allow a phrase to extend past the actual
        # audio/timeline duration.
        # ----------------------------------------------------
        end_time = min(
            timeline_duration,
            last_time + frame_duration,
        )

        # A final frame can land exactly at the duration.
        if end_time <= start_time:
            end_time = min(
                timeline_duration,
                start_time + frame_duration,
            )

        if end_time <= start_time:
            return None

        duration = end_time - start_time

        voiced = [
            frame
            for frame in frames
            if self._is_voiced(frame)
        ]

        if not voiced:
            return None

        f0_values = [
            self._f0(frame)
            for frame in voiced
            if self._f0(frame) > 0
        ]

        if not f0_values:
            return None

        confidence_values = [
            self._confidence(frame)
            for frame in voiced
        ]

        pitch_min = min(f0_values)
        pitch_max = max(f0_values)
        pitch_center = median(f0_values)

        start_f0 = f0_values[0]
        end_f0 = f0_values[-1]

        segments = self._find_segments(
            timeline,
            start_time,
            end_time,
        )

        note_names = []

        for segment in segments:
            name = getattr(
                segment,
                "note_name",
                "",
            )

            octave = getattr(
                segment,
                "octave",
                None,
            )

            if not name:
                continue

            value = (
                f"{name}{octave}"
                if octave is not None
                else str(name)
            )

            if value not in note_names:
                note_names.append(value)

        return VocalPhrase(
            index=index,
            start_time=round(
                start_time,
                6,
            ),
            end_time=round(
                end_time,
                6,
            ),
            duration=round(
                duration,
                6,
            ),
            frame_count=len(frames),
            voiced_frames=len(voiced),
            unvoiced_frames=(
                len(frames) - len(voiced)
            ),
            voiced_coverage=round(
                len(voiced)
                / len(frames)
                * 100.0,
                2,
            ),
            start_f0_hz=round(
                start_f0,
                3,
            ),
            end_f0_hz=round(
                end_f0,
                3,
            ),
            pitch_center_hz=round(
                pitch_center,
                3,
            ),
            pitch_min_hz=round(
                pitch_min,
                3,
            ),
            pitch_max_hz=round(
                pitch_max,
                3,
            ),
            pitch_range_semitones=round(
                self._hz_to_semitones(
                    pitch_min,
                    pitch_max,
                ),
                3,
            ),
            start_midi=round(
                self._hz_to_midi(start_f0),
                3,
            ),
            end_midi=round(
                self._hz_to_midi(end_f0),
                3,
            ),
            pitch_center_midi=round(
                self._hz_to_midi(pitch_center),
                3,
            ),
            average_confidence=round(
                (
                    sum(confidence_values)
                    / len(confidence_values)
                    * 100.0
                ),
                2,
            ),
            note_count=len(segments),
            note_names=note_names,
            frames=list(frames),
            segments=segments,
        )

    # ========================================================
    # SEGMENTS
    # ========================================================

    @staticmethod
    def _find_segments(
        timeline,
        start,
        end,
    ):
        segments = list(
            getattr(
                timeline,
                "segments",
                [],
            )
        )

        result = []

        for segment in segments:
            segment_start = float(
                getattr(
                    segment,
                    "start_time",
                    0.0,
                )
            )

            segment_end = float(
                getattr(
                    segment,
                    "end_time",
                    0.0,
                )
            )

            if (
                segment_end > start
                and segment_start < end
            ):
                result.append(segment)

        return result

    # ========================================================
    # FRAME DURATION
    # ========================================================

    def _estimate_frame_duration(
        self,
        timeline,
    ):
        frames = list(
            getattr(
                timeline,
                "frames",
                [],
            )
        )

        if len(frames) < 2:
            return 0.025

        times = sorted(
            self._frame_time(frame)
            for frame in frames
        )

        differences = [
            right - left
            for left, right in zip(
                times,
                times[1:],
            )
            if 0 < right - left < 0.2
        ]

        if not differences:
            return 0.025

        return float(
            median(differences)
        )

    # ========================================================
    # PITCH
    # ========================================================

    @staticmethod
    def _hz_to_midi(hz):
        import math

        if hz <= 0:
            return 0.0

        return (
            69.0
            + 12.0 * math.log2(
                hz / 440.0
            )
        )

    @classmethod
    def _hz_to_semitones(
        cls,
        minimum,
        maximum,
    ):
        if (
            minimum <= 0
            or maximum <= 0
        ):
            return 0.0

        return (
            cls._hz_to_midi(maximum)
            - cls._hz_to_midi(minimum)
        )