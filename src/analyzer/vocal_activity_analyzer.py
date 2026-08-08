"""
Phoenix Voice Studio
Vocal Activity Analyzer

Detects active audio regions based on signal energy.

This module identifies useful audio activity regions.
It does NOT claim to separate vocals from music.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


@dataclass
class VocalSegment:
    """Represents one detected active audio segment."""

    index: int
    start: float
    end: float
    duration: float

    def to_dict(self) -> dict[str, Any]:
        """Convert segment to a dictionary."""

        return asdict(self)


@dataclass
class VocalActivityReport:
    """Complete vocal activity analysis result."""

    file_name: str
    total_duration: float

    active_duration: float
    silence_duration: float
    active_coverage: float

    segment_count: int
    segments: list[VocalSegment]

    threshold_dbfs: float
    minimum_segment_duration: float
    minimum_silence_duration: float

    def to_dict(self) -> dict[str, Any]:
        """Convert report to a dictionary."""

        data = asdict(self)

        data["segments"] = [
            segment.to_dict()
            for segment in self.segments
        ]

        return data


class VocalActivityAnalyzer:
    """
    Detect active audio regions using short-time RMS energy.

    The analyzer is intentionally conservative about terminology:
    an active region may contain singing, speech, music, or another
    audible signal. It is not a vocal separator.
    """

    def __init__(
        self,
        frame_duration: float = 0.05,
        threshold_dbfs: float = -40.0,
        minimum_segment_duration: float = 0.30,
        minimum_silence_duration: float = 0.20,
    ):

        if frame_duration <= 0:
            raise ValueError(
                "frame_duration must be greater than zero."
            )

        if minimum_segment_duration <= 0:
            raise ValueError(
                "minimum_segment_duration must be greater than zero."
            )

        if minimum_silence_duration < 0:
            raise ValueError(
                "minimum_silence_duration cannot be negative."
            )

        self.frame_duration = frame_duration
        self.threshold_dbfs = threshold_dbfs
        self.minimum_segment_duration = (
            minimum_segment_duration
        )
        self.minimum_silence_duration = (
            minimum_silence_duration
        )

    def analyze(
        self,
        audio_path: str,
    ) -> VocalActivityReport:
        """
        Analyze an audio file and detect active regions.
        """

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Audio path is not a file: {audio_path}"
            )

        audio, sample_rate = sf.read(
            str(path),
            always_2d=False,
        )

        if audio.size == 0:
            raise ValueError(
                "The audio file contains no samples."
            )

        mono_audio = self._to_mono(audio)

        total_duration = (
            len(mono_audio) / sample_rate
        )

        frame_size = max(
            1,
            int(
                round(
                    self.frame_duration
                    * sample_rate
                )
            ),
        )

        frame_energies = self._calculate_frame_energy(
            mono_audio,
            frame_size,
        )

        active_flags = (
            frame_energies
            >= self.threshold_dbfs
        )

        segments = self._build_segments(
            active_flags=active_flags,
            frame_size=frame_size,
            sample_rate=sample_rate,
            total_samples=len(mono_audio),
        )

        active_duration = sum(
            segment.duration
            for segment in segments
        )

        active_duration = min(
            active_duration,
            total_duration,
        )

        silence_duration = max(
            0.0,
            total_duration - active_duration,
        )

        active_coverage = (
            active_duration / total_duration
            if total_duration > 0
            else 0.0
        )

        return VocalActivityReport(
            file_name=path.name,
            total_duration=round(
                total_duration,
                2,
            ),
            active_duration=round(
                active_duration,
                2,
            ),
            silence_duration=round(
                silence_duration,
                2,
            ),
            active_coverage=round(
                active_coverage * 100,
                2,
            ),
            segment_count=len(segments),
            segments=segments,
            threshold_dbfs=self.threshold_dbfs,
            minimum_segment_duration=(
                self.minimum_segment_duration
            ),
            minimum_silence_duration=(
                self.minimum_silence_duration
            ),
        )

    @staticmethod
    def _to_mono(
        audio: np.ndarray,
    ) -> np.ndarray:
        """Convert audio to a mono analysis signal."""

        if audio.ndim == 1:
            return audio.astype(
                np.float64
            )

        if audio.ndim == 2:
            return np.mean(
                audio.astype(np.float64),
                axis=1,
            )

        raise ValueError(
            f"Unsupported audio dimensions: "
            f"{audio.ndim}"
        )

    @staticmethod
    def _calculate_frame_energy(
        audio: np.ndarray,
        frame_size: int,
    ) -> np.ndarray:
        """
        Calculate RMS energy for each frame.

        Returns values in dBFS.
        """

        frame_count = int(
            np.ceil(
                len(audio) / frame_size
            )
        )

        energies = np.empty(
            frame_count,
            dtype=np.float64,
        )

        for index in range(frame_count):

            start = index * frame_size
            end = min(
                start + frame_size,
                len(audio),
            )

            frame = audio[start:end]

            if frame.size == 0:
                energies[index] = -120.0
                continue

            rms = np.sqrt(
                np.mean(
                    np.square(frame)
                )
            )

            if rms <= 1e-12:
                energies[index] = -120.0
            else:
                energies[index] = (
                    20.0 * np.log10(rms)
                )

        return energies

    def _build_segments(
        self,
        active_flags: np.ndarray,
        frame_size: int,
        sample_rate: int,
        total_samples: int,
    ) -> list[VocalSegment]:
        """
        Convert active frames into clean segments.

        Short inactive gaps are merged.
        Very short active regions are removed.
        """

        if active_flags.size == 0:
            return []

        silence_frames = max(
            0,
            int(
                round(
                    self.minimum_silence_duration
                    / self.frame_duration
                )
            ),
        )

        active = active_flags.copy()

        # --------------------------------------------------
        # Fill short gaps between active regions.
        # --------------------------------------------------

        if silence_frames > 0:

            active = self._fill_short_gaps(
                active,
                silence_frames,
            )

        # --------------------------------------------------
        # Extract raw regions.
        # --------------------------------------------------

        raw_segments = []

        start_frame = None

        for index, is_active in enumerate(active):

            if is_active and start_frame is None:

                start_frame = index

            elif not is_active and start_frame is not None:

                raw_segments.append(
                    (
                        start_frame,
                        index,
                    )
                )

                start_frame = None

        if start_frame is not None:

            raw_segments.append(
                (
                    start_frame,
                    len(active),
                )
            )

        # --------------------------------------------------
        # Convert frames to time and filter short segments.
        # --------------------------------------------------

        segments = []

        for start_frame, end_frame in raw_segments:

            start_sample = (
                start_frame * frame_size
            )

            end_sample = min(
                end_frame * frame_size,
                total_samples,
            )

            start_time = (
                start_sample / sample_rate
            )

            end_time = (
                end_sample / sample_rate
            )

            duration = (
                end_time - start_time
            )

            if (
                duration
                < self.minimum_segment_duration
            ):
                continue

            segments.append(
                VocalSegment(
                    index=len(segments) + 1,
                    start=round(
                        start_time,
                        3,
                    ),
                    end=round(
                        end_time,
                        3,
                    ),
                    duration=round(
                        duration,
                        3,
                    ),
                )
            )

        return segments

    @staticmethod
    def _fill_short_gaps(
        active: np.ndarray,
        max_gap_frames: int,
    ) -> np.ndarray:
        """
        Fill inactive gaps that are shorter than the
        configured silence duration.
        """

        result = active.copy()

        if max_gap_frames <= 0:
            return result

        length = len(result)

        index = 0

        while index < length:

            if result[index]:

                index += 1
                continue

            gap_start = index

            while (
                index < length
                and not result[index]
            ):
                index += 1

            gap_end = index

            gap_length = (
                gap_end - gap_start
            )

            has_left = (
                gap_start > 0
                and result[gap_start - 1]
            )

            has_right = (
                gap_end < length
                and result[gap_end]
            )

            if (
                has_left
                and has_right
                and gap_length <= max_gap_frames
            ):

                result[
                    gap_start:gap_end
                ] = True

        return result