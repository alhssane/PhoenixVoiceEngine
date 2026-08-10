"""
Phoenix Voice Studio
Pitch Analyzer - Version 3

Robust F0 / Pitch Tracking Engine.

Pipeline:

    Audio
      ↓
    Frame Analysis
      ↓
    F0 Candidates
      ↓
    Confidence Filtering
      ↓
    Temporal Pitch Tracking
      ↓
    Octave Correction
      ↓
    Outlier Rejection
      ↓
    Robust Pitch Statistics
      ↓
    Pitch Report

Designed for clean vocal input.

The original audio is never modified.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf


# ============================================================
# DATA MODELS
# ============================================================


@dataclass
class PitchFrame:
    """Final pitch information for one frame."""

    time: float
    f0: float
    confidence: float
    voiced: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PitchReport:
    """Complete pitch analysis report."""

    file_name: str
    duration: float

    voiced_duration: float
    unvoiced_duration: float
    voiced_coverage: float

    min_f0: float
    max_f0: float
    mean_f0: float
    median_f0: float

    pitch_range_semitones: float
    pitch_stability: float

    frame_count: int
    voiced_frame_count: int

    frames: list[PitchFrame]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)

        data["frames"] = [
            frame.to_dict()
            for frame in self.frames
        ]

        return data


@dataclass
class _PitchCandidate:
    """Internal pitch candidate."""

    f0: float
    confidence: float


@dataclass
class _TrackedFrame:
    """Internal frame used during tracking."""

    time: float
    f0: float
    confidence: float
    voiced: bool


# ============================================================
# PITCH ANALYZER
# ============================================================


class PitchAnalyzer:
    """
    Robust F0 analyzer.

    This version focuses on temporal continuity.

    It attempts to prevent isolated octave errors from
    contaminating the final pitch contour.
    """

    def __init__(
        self,
        frame_duration: float = 0.05,
        hop_duration: float = 0.025,
        min_f0: float = 70.0,
        max_f0: float = 600.0,
        confidence_threshold: float = 0.45,
        max_jump_semitones: float = 7.0,
        smoothing_window: int = 5,
    ):

        if frame_duration <= 0:
            raise ValueError(
                "frame_duration must be greater than zero."
            )

        if hop_duration <= 0:
            raise ValueError(
                "hop_duration must be greater than zero."
            )

        if min_f0 <= 0:
            raise ValueError(
                "min_f0 must be greater than zero."
            )

        if max_f0 <= min_f0:
            raise ValueError(
                "max_f0 must be greater than min_f0."
            )

        if not 0 <= confidence_threshold <= 1:
            raise ValueError(
                "confidence_threshold must be between 0 and 1."
            )

        if max_jump_semitones <= 0:
            raise ValueError(
                "max_jump_semitones must be greater than zero."
            )

        if smoothing_window < 1:
            raise ValueError(
                "smoothing_window must be odd and >= 1."
            )

        if smoothing_window % 2 == 0:
            raise ValueError(
                "smoothing_window must be odd."
            )

        self.frame_duration = frame_duration
        self.hop_duration = hop_duration

        self.min_f0 = min_f0
        self.max_f0 = max_f0

        self.confidence_threshold = (
            confidence_threshold
        )

        self.max_jump_semitones = (
            max_jump_semitones
        )

        self.smoothing_window = (
            smoothing_window
        )

    # ========================================================
    # PUBLIC
    # ========================================================

    def analyze(
        self,
        audio_path: str,
    ) -> PitchReport:

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found:\n{audio_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Audio path is not a file:\n{audio_path}"
            )

        audio, sample_rate = sf.read(
            str(path),
            always_2d=False,
        )

        if audio.size == 0:
            raise ValueError(
                "Audio file contains no samples."
            )

        mono = self._to_mono(audio)

        duration = (
            len(mono) / sample_rate
        )

        frame_size = max(
            512,
            int(
                self.frame_duration
                * sample_rate
            ),
        )

        hop_size = max(
            1,
            int(
                self.hop_duration
                * sample_rate
            ),
        )

        # ----------------------------------------------------
        # 1. Extract candidates
        # ----------------------------------------------------

        candidate_frames = (
            self._extract_candidates(
                mono,
                sample_rate,
                frame_size,
                hop_size,
            )
        )

        # ----------------------------------------------------
        # 2. Select a temporally consistent path
        # ----------------------------------------------------

        tracked_frames = (
            self._track_pitch(
                candidate_frames
            )
        )

        # ----------------------------------------------------
        # 3. Remove isolated outliers
        # ----------------------------------------------------

        tracked_frames = (
            self._remove_outliers(
                tracked_frames
            )
        )

        # ----------------------------------------------------
        # 4. Smooth final contour
        # ----------------------------------------------------

        tracked_frames = (
            self._smooth_pitch(
                tracked_frames
            )
        )

        # ----------------------------------------------------
        # 5. Convert to public frames
        # ----------------------------------------------------

        frames = [
            PitchFrame(
                time=round(
                    frame.time,
                    4,
                ),
                f0=round(
                    frame.f0,
                    2,
                ),
                confidence=round(
                    frame.confidence,
                    3,
                ),
                voiced=frame.voiced,
            )
            for frame in tracked_frames
        ]

        voiced_frames = [
            frame
            for frame in frames
            if frame.voiced
            and frame.f0 > 0
        ]

        voiced_frame_count = len(
            voiced_frames
        )

        voiced_duration = min(
            voiced_frame_count
            * self.hop_duration,
            duration,
        )

        unvoiced_duration = max(
            0.0,
            duration
            - voiced_duration,
        )

        voiced_coverage = (
            voiced_duration
            / duration
            * 100.0
            if duration > 0
            else 0.0
        )

        f0_values = np.asarray(
            [
                frame.f0
                for frame in voiced_frames
                if frame.f0 > 0
            ],
            dtype=np.float64,
        )

        if f0_values.size == 0:

            min_f0 = 0.0
            max_f0 = 0.0
            mean_f0 = 0.0
            median_f0 = 0.0
            pitch_range = 0.0
            pitch_stability = 0.0

        else:

            # Robust range instead of raw min/max.
            robust_low = float(
                np.percentile(
                    f0_values,
                    2,
                )
            )

            robust_high = float(
                np.percentile(
                    f0_values,
                    98,
                )
            )

            min_f0 = robust_low
            max_f0 = robust_high

            mean_f0 = float(
                np.mean(f0_values)
            )

            median_f0 = float(
                np.median(f0_values)
            )

            pitch_range = (
                self._pitch_range(
                    robust_low,
                    robust_high,
                )
            )

            pitch_stability = (
                self._pitch_stability(
                    f0_values
                )
            )

        return PitchReport(
            file_name=path.name,
            duration=round(
                duration,
                2,
            ),
            voiced_duration=round(
                voiced_duration,
                2,
            ),
            unvoiced_duration=round(
                unvoiced_duration,
                2,
            ),
            voiced_coverage=round(
                voiced_coverage,
                2,
            ),
            min_f0=round(
                min_f0,
                2,
            ),
            max_f0=round(
                max_f0,
                2,
            ),
            mean_f0=round(
                mean_f0,
                2,
            ),
            median_f0=round(
                median_f0,
                2,
            ),
            pitch_range_semitones=round(
                pitch_range,
                2,
            ),
            pitch_stability=round(
                pitch_stability,
                2,
            ),
            frame_count=len(frames),
            voiced_frame_count=(
                voiced_frame_count
            ),
            frames=frames,
        )

    # ========================================================
    # AUDIO
    # ========================================================

    @staticmethod
    def _to_mono(
        audio: np.ndarray,
    ) -> np.ndarray:

        if audio.ndim == 1:

            return audio.astype(
                np.float64
            )

        if audio.ndim == 2:

            return np.mean(
                audio.astype(
                    np.float64
                ),
                axis=1,
            )

        raise ValueError(
            f"Unsupported audio dimensions: "
            f"{audio.ndim}"
        )

    # ========================================================
    # CANDIDATE EXTRACTION
    # ========================================================

    def _extract_candidates(
        self,
        audio: np.ndarray,
        sample_rate: int,
        frame_size: int,
        hop_size: int,
    ) -> list[list[_PitchCandidate]]:

        results = []

        if len(audio) < frame_size:

            audio = np.pad(
                audio,
                (
                    0,
                    frame_size
                    - len(audio),
                ),
            )

        for start in range(
            0,
            max(
                1,
                len(audio)
                - frame_size
                + 1,
            ),
            hop_size,
        ):

            frame = audio[
                start:
                start + frame_size
            ]

            if len(frame) < frame_size:

                frame = np.pad(
                    frame,
                    (
                        0,
                        frame_size
                        - len(frame),
                    ),
                )

            candidates = (
                self._estimate_candidates(
                    frame,
                    sample_rate,
                )
            )

            results.append(
                candidates
            )

        return results

    # ========================================================
    # AUTOCORRELATION CANDIDATES
    # ========================================================

    def _estimate_candidates(
        self,
        frame: np.ndarray,
        sample_rate: int,
    ) -> list[_PitchCandidate]:

        frame = (
            frame
            - np.mean(frame)
        )

        rms = np.sqrt(
            np.mean(
                frame ** 2
            )
        )

        if rms <= 1e-8:

            return []

        window = np.hanning(
            len(frame)
        )

        signal = (
            frame * window
        )

        fft_size = 1

        target = (
            len(signal) * 2
        )

        while fft_size < target:

            fft_size *= 2

        spectrum = np.fft.rfft(
            signal,
            n=fft_size,
        )

        autocorrelation = np.fft.irfft(
            np.abs(spectrum) ** 2,
            n=fft_size,
        )

        if (
            autocorrelation.size == 0
            or autocorrelation[0] <= 1e-12
        ):

            return []

        autocorrelation /= (
            autocorrelation[0]
        )

        min_lag = max(
            1,
            int(
                sample_rate
                / self.max_f0
            ),
        )

        max_lag = min(
            len(frame) // 2,
            int(
                sample_rate
                / self.min_f0
            ),
        )

        if max_lag <= min_lag:

            return []

        region = autocorrelation[
            min_lag:
            max_lag + 1
        ]

        peaks = []

        for index in range(
            1,
            len(region) - 1,
        ):

            if (
                region[index]
                >= region[index - 1]
                and region[index]
                >= region[index + 1]
            ):

                peaks.append(
                    index
                )

        if not peaks:

            peaks = [
                int(
                    np.argmax(region)
                )
            ]

        peaks.sort(
            key=lambda index: region[index],
            reverse=True,
        )

        candidates = []

        for peak_index in peaks[:12]:

            confidence = float(
                np.clip(
                    region[peak_index],
                    0.0,
                    1.0,
                )
            )

            if (
                confidence
                < self.confidence_threshold
            ):
                continue

            lag = (
                min_lag
                + peak_index
            )

            # Parabolic refinement.
            refined_lag = float(
                lag
            )

            left = lag - 1
            right = lag + 1

            if (
                left >= 0
                and right
                < len(autocorrelation)
            ):

                y1 = autocorrelation[
                    left
                ]

                y2 = autocorrelation[
                    lag
                ]

                y3 = autocorrelation[
                    right
                ]

                denominator = (
                    y1
                    - 2.0 * y2
                    + y3
                )

                if abs(
                    denominator
                ) > 1e-12:

                    refined_lag += (
                        0.5
                        * (
                            y1 - y3
                        )
                        / denominator
                    )

            if refined_lag <= 0:
                continue

            f0 = (
                sample_rate
                / refined_lag
            )

            if (
                self.min_f0
                <= f0
                <= self.max_f0
            ):

                candidates.append(
                    _PitchCandidate(
                        f0=float(f0),
                        confidence=confidence,
                    )
                )

        return candidates

    # ========================================================
    # TEMPORAL TRACKING
    # ========================================================

    def _track_pitch(
        self,
        candidate_frames: list[
            list[_PitchCandidate]
        ],
    ) -> list[_TrackedFrame]:

        tracked = []

        previous_f0 = 0.0

        for index, candidates in enumerate(
            candidate_frames
        ):

            time = (
                index
                * self.hop_duration
            )

            if not candidates:

                tracked.append(
                    _TrackedFrame(
                        time=time,
                        f0=0.0,
                        confidence=0.0,
                        voiced=False,
                    )
                )

                continue

            # First voiced frame.
            if previous_f0 <= 0:

                best = max(
                    candidates,
                    key=lambda candidate:
                    candidate.confidence,
                )

                tracked.append(
                    _TrackedFrame(
                        time=time,
                        f0=best.f0,
                        confidence=best.confidence,
                        voiced=True,
                    )
                )

                previous_f0 = best.f0

                continue

            # ------------------------------------------------
            # Select candidate closest to previous pitch.
            # ------------------------------------------------

            scored = []

            for candidate in candidates:

                distance = (
                    self._pitch_distance(
                        candidate.f0,
                        previous_f0,
                    )
                )

                # Candidates within one octave are favored.
                if distance <= 24.0:

                    score = (
                        distance * 0.65
                        + (
                            1.0
                            - candidate.confidence
                        )
                        * 8.0
                    )

                    scored.append(
                        (
                            score,
                            candidate,
                        )
                    )

            if scored:

                scored.sort(
                    key=lambda item:
                    item[0]
                )

                best = scored[0][1]

                jump = (
                    self._pitch_distance(
                        best.f0,
                        previous_f0,
                    )
                )

                # ------------------------------------------------
                # Large isolated jump.
                # ------------------------------------------------

                if (
                    jump
                    > self.max_jump_semitones
                ):

                    # Try octave equivalents.
                    alternatives = [
                        best.f0 / 2.0,
                        best.f0 * 2.0,
                    ]

                    corrected = None

                    best_distance = jump

                    for alternative in alternatives:

                        if (
                            alternative
                            < self.min_f0
                            or alternative
                            > self.max_f0
                        ):
                            continue

                        alt_distance = (
                            self._pitch_distance(
                                alternative,
                                previous_f0,
                            )
                        )

                        if (
                            alt_distance
                            < best_distance
                        ):

                            corrected = (
                                alternative
                            )

                            best_distance = (
                                alt_distance
                            )

                    if corrected is not None:

                        best = _PitchCandidate(
                            f0=corrected,
                            confidence=best.confidence,
                        )

                        jump = (
                            best_distance
                        )

                # Still too large:
                # keep previous pitch rather than introducing
                # an isolated spike.
                if (
                    jump
                    > self.max_jump_semitones
                ):

                    tracked.append(
                        _TrackedFrame(
                            time=time,
                            f0=previous_f0,
                            confidence=(
                                best.confidence
                                * 0.75
                            ),
                            voiced=True,
                        )
                    )

                    continue

                tracked.append(
                    _TrackedFrame(
                        time=time,
                        f0=best.f0,
                        confidence=best.confidence,
                        voiced=True,
                    )
                )

                previous_f0 = best.f0

            else:

                tracked.append(
                    _TrackedFrame(
                        time=time,
                        f0=0.0,
                        confidence=0.0,
                        voiced=False,
                    )
                )

        return tracked

    # ========================================================
    # OUTLIER REMOVAL
    # ========================================================

    def _remove_outliers(
        self,
        frames: list[_TrackedFrame],
    ) -> list[_TrackedFrame]:

        if len(frames) < 3:

            return frames

        result = [
            _TrackedFrame(
                time=frame.time,
                f0=frame.f0,
                confidence=frame.confidence,
                voiced=frame.voiced,
            )
            for frame in frames
        ]

        for index in range(
            1,
            len(result) - 1,
        ):

            current = result[index]

            previous = result[
                index - 1
            ]

            following = result[
                index + 1
            ]

            if (
                not current.voiced
                or current.f0 <= 0
            ):
                continue

            if (
                not previous.voiced
                or previous.f0 <= 0
            ):
                continue

            if (
                not following.voiced
                or following.f0 <= 0
            ):
                continue

            distance_previous = (
                self._pitch_distance(
                    current.f0,
                    previous.f0,
                )
            )

            distance_following = (
                self._pitch_distance(
                    current.f0,
                    following.f0,
                )
            )

            neighbor_distance = (
                self._pitch_distance(
                    previous.f0,
                    following.f0,
                )
            )

            # Current frame is an isolated outlier if it is
            # far from both neighbors while the neighbors agree.
            if (
                distance_previous
                > self.max_jump_semitones
                and distance_following
                > self.max_jump_semitones
                and neighbor_distance
                <= self.max_jump_semitones
            ):

                result[index].f0 = (
                    (
                        previous.f0
                        + following.f0
                    )
                    / 2.0
                )

                result[index].confidence *= 0.9

        return result

    # ========================================================
    # SMOOTHING
    # ========================================================

    def _smooth_pitch(
        self,
        frames: list[_TrackedFrame],
    ) -> list[_TrackedFrame]:

        if len(frames) < 3:

            return frames

        result = [
            _TrackedFrame(
                time=frame.time,
                f0=frame.f0,
                confidence=frame.confidence,
                voiced=frame.voiced,
            )
            for frame in frames
        ]

        half = (
            self.smoothing_window
            // 2
        )

        for index in range(
            len(frames)
        ):

            current = frames[index]

            if (
                not current.voiced
                or current.f0 <= 0
            ):
                continue

            values = []

            start = max(
                0,
                index - half,
            )

            end = min(
                len(frames),
                index + half + 1,
            )

            for neighbor_index in range(
                start,
                end,
            ):

                neighbor = frames[
                    neighbor_index
                ]

                if (
                    neighbor.voiced
                    and neighbor.f0 > 0
                ):

                    values.append(
                        neighbor.f0
                    )

            if values:

                result[index].f0 = float(
                    np.median(values)
                )

        return result

    # ========================================================
    # PITCH DISTANCE
    # ========================================================

    @staticmethod
    def _pitch_distance(
        f0_a: float,
        f0_b: float,
    ) -> float:

        if (
            f0_a <= 0
            or f0_b <= 0
        ):

            return 999.0

        return abs(
            12.0
            * np.log2(
                f0_a
                / f0_b
            )
        )

    # ========================================================
    # ROBUST RANGE
    # ========================================================

    @staticmethod
    def _pitch_range(
        low_f0: float,
        high_f0: float,
    ) -> float:

        if (
            low_f0 <= 0
            or high_f0 <= 0
        ):

            return 0.0

        return float(
            12.0
            * np.log2(
                high_f0
                / low_f0
            )
        )

    # ========================================================
    # STABILITY
    # ========================================================

    @staticmethod
    def _pitch_stability(
        f0_values: np.ndarray,
    ) -> float:

        if f0_values.size < 2:

            return 0.0

        log_f0 = np.log2(
            f0_values
        )

        changes = (
            np.abs(
                np.diff(log_f0)
            )
            * 12.0
        )

        if changes.size == 0:

            return 100.0

        median_change = float(
            np.median(changes)
        )

        p90_change = float(
            np.percentile(
                changes,
                90,
            )
        )

        score = (
            100.0
            - median_change * 12.0
            - max(
                0.0,
                p90_change - 2.0,
            )
            * 4.0
        )

        return float(
            np.clip(
                score,
                0.0,
                100.0,
            )
        )