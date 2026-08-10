"""
Phoenix Voice Studio
Vocal Performance Analyzer - Version 2

Analyzes the cleaned pitch contour produced by PitchAnalyzer.

Important:
This module analyzes vocal performance data.
It does NOT train a model and does NOT modify the source audio.

Main goals:
- Stable pitch regions
- Genuine pitch movements
- Pitch center
- Pitch range
- Pitch stability
- Confidence
- Conservative vibrato estimation
- Performance data suitable for later note/phrase extraction
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from src.analyzer.pitch_analyzer import (
    PitchAnalyzer,
    PitchReport,
)


# ============================================================
# DATA MODELS
# ============================================================


@dataclass
class PitchTransition:
    """A confirmed pitch movement."""

    start_time: float
    end_time: float

    start_f0: float
    end_f0: float

    semitone_change: float
    direction: str

    duration: float

    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VibratoReport:
    """Conservative vibrato analysis."""

    detected: bool

    rate_hz: float
    depth_semitones: float

    duration: float
    coverage: float

    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StablePitchRegion:
    """
    A region where pitch remains reasonably stable.

    These regions will later be useful for note extraction.
    """

    start_time: float
    end_time: float

    duration: float

    mean_f0: float
    median_f0: float

    min_f0: float
    max_f0: float

    variation_semitones: float

    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VocalPerformanceReport:
    """Complete vocal performance report."""

    file_name: str
    duration: float

    voiced_duration: float
    voiced_coverage: float

    pitch_center_hz: float
    pitch_center_midi: float

    pitch_min_hz: float
    pitch_max_hz: float

    pitch_range_semitones: float

    pitch_stability: float

    average_confidence: float

    pitch_movement_count: int

    upward_movements: int
    downward_movements: int

    transitions: list[PitchTransition]

    stable_regions: list[StablePitchRegion]

    vibrato: VibratoReport

    performance_score: float

    status: str

    def to_dict(self) -> dict[str, Any]:

        data = asdict(self)

        data["transitions"] = [
            transition.to_dict()
            for transition in self.transitions
        ]

        data["stable_regions"] = [
            region.to_dict()
            for region in self.stable_regions
        ]

        data["vibrato"] = (
            self.vibrato.to_dict()
        )

        return data


# ============================================================
# INTERNAL FRAME
# ============================================================


@dataclass
class _PitchPoint:
    time: float
    f0: float
    confidence: float


# ============================================================
# ANALYZER
# ============================================================


class VocalPerformanceAnalyzer:
    """
    Conservative vocal performance analyzer.

    Processing:

        PitchReport
            ↓
        Clean voiced points
            ↓
        Stable pitch regions
            ↓
        Genuine pitch transitions
            ↓
        Vibrato estimation
            ↓
        Performance metrics
    """

    def __init__(
        self,
        pitch_analyzer: PitchAnalyzer | None = None,

        movement_threshold_semitones: float = 2.0,

        transition_threshold_semitones: float = 3.0,

        minimum_transition_duration: float = 0.075,

        minimum_region_duration: float = 0.100,

        stable_variation_semitones: float = 1.5,

        vibrato_min_rate_hz: float = 4.0,

        vibrato_max_rate_hz: float = 8.0,
    ):

        self.pitch_analyzer = (
            pitch_analyzer
            or PitchAnalyzer()
        )

        self.movement_threshold = (
            movement_threshold_semitones
        )

        self.transition_threshold = (
            transition_threshold_semitones
        )

        self.minimum_transition_duration = (
            minimum_transition_duration
        )

        self.minimum_region_duration = (
            minimum_region_duration
        )

        self.stable_variation = (
            stable_variation_semitones
        )

        self.vibrato_min_rate = (
            vibrato_min_rate_hz
        )

        self.vibrato_max_rate = (
            vibrato_max_rate_hz
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def analyze(
        self,
        audio_path: str,
    ) -> VocalPerformanceReport:

        path = Path(audio_path)

        if not path.exists():

            raise FileNotFoundError(
                f"Audio file not found:\n{audio_path}"
            )

        pitch_report = (
            self.pitch_analyzer.analyze(
                str(path)
            )
        )

        return self.analyze_pitch_report(
            pitch_report
        )

    def analyze_pitch_report(
        self,
        pitch_report: PitchReport,
    ) -> VocalPerformanceReport:
        """
        Analyze an existing PitchReport.

        This prevents PitchAnalyzer from being executed twice.
        """

        points = self._prepare_points(
            pitch_report
        )

        if not points:

            return self._empty_report(
                pitch_report
            )

        f0_values = np.asarray(
            [
                point.f0
                for point in points
            ],
            dtype=np.float64,
        )

        confidence_values = np.asarray(
            [
                point.confidence
                for point in points
            ],
            dtype=np.float64,
        )

        # ----------------------------------------------------
        # Pitch Center
        # ----------------------------------------------------

        pitch_center_hz = float(
            np.median(
                f0_values
            )
        )

        pitch_center_midi = (
            self._hz_to_midi(
                pitch_center_hz
            )
        )

        # ----------------------------------------------------
        # Robust range
        # ----------------------------------------------------

        pitch_min_hz = float(
            np.percentile(
                f0_values,
                2,
            )
        )

        pitch_max_hz = float(
            np.percentile(
                f0_values,
                98,
            )
        )

        pitch_range = (
            self._pitch_distance(
                pitch_min_hz,
                pitch_max_hz,
            )
        )

        # ----------------------------------------------------
        # Confidence
        # ----------------------------------------------------

        average_confidence = float(
            np.mean(
                confidence_values
            )
        )

        # ----------------------------------------------------
        # Stable regions
        # ----------------------------------------------------

        stable_regions = (
            self._detect_stable_regions(
                points
            )
        )

        # ----------------------------------------------------
        # Genuine transitions
        # ----------------------------------------------------

        transitions = (
            self._detect_transitions(
                points
            )
        )

        upward_movements = sum(
            1
            for transition in transitions
            if transition.direction
            == "UP"
        )

        downward_movements = sum(
            1
            for transition in transitions
            if transition.direction
            == "DOWN"
        )

        # ----------------------------------------------------
        # Vibrato
        # ----------------------------------------------------

        vibrato = (
            self._analyze_vibrato(
                points
            )
        )

        # ----------------------------------------------------
        # Performance score
        # ----------------------------------------------------

        performance_score = (
            self._calculate_performance_score(
                pitch_report=pitch_report,
                average_confidence=(
                    average_confidence
                ),
                stable_regions=(
                    stable_regions
                ),
                transitions=(
                    transitions
                ),
            )
        )

        if performance_score >= 85:

            status = "EXCELLENT"

        elif performance_score >= 70:

            status = "GOOD"

        elif performance_score >= 50:

            status = "ACCEPTABLE"

        else:

            status = "NEEDS_REVIEW"

        return VocalPerformanceReport(

            file_name=(
                pitch_report.file_name
            ),

            duration=(
                pitch_report.duration
            ),

            voiced_duration=(
                pitch_report.voiced_duration
            ),

            voiced_coverage=(
                pitch_report.voiced_coverage
            ),

            pitch_center_hz=round(
                pitch_center_hz,
                2,
            ),

            pitch_center_midi=round(
                pitch_center_midi,
                2,
            ),

            pitch_min_hz=round(
                pitch_min_hz,
                2,
            ),

            pitch_max_hz=round(
                pitch_max_hz,
                2,
            ),

            pitch_range_semitones=round(
                pitch_range,
                2,
            ),

            pitch_stability=round(
                pitch_report.pitch_stability,
                2,
            ),

            average_confidence=round(
                average_confidence * 100.0,
                2,
            ),

            pitch_movement_count=len(
                transitions
            ),

            upward_movements=(
                upward_movements
            ),

            downward_movements=(
                downward_movements
            ),

            transitions=transitions,

            stable_regions=stable_regions,

            vibrato=vibrato,

            performance_score=round(
                performance_score,
                2,
            ),

            status=status,
        )

    # ========================================================
    # PREPARE POINTS
    # ========================================================

    @staticmethod
    def _prepare_points(
        pitch_report: PitchReport,
    ) -> list[_PitchPoint]:

        points = []

        for frame in pitch_report.frames:

            if (
                not frame.voiced
                or frame.f0 <= 0
            ):
                continue

            points.append(
                _PitchPoint(
                    time=frame.time,
                    f0=frame.f0,
                    confidence=frame.confidence,
                )
            )

        return points

    # ========================================================
    # STABLE PITCH REGIONS
    # ========================================================

    def _detect_stable_regions(
        self,
        points: list[_PitchPoint],
    ) -> list[StablePitchRegion]:
        """
        Detect regions where pitch remains stable.

        A region is only accepted when:
        - It has enough duration.
        - Pitch variation is reasonably small.
        - Confidence is acceptable.
        """

        if len(points) < 3:

            return []

        regions = []

        current = [
            points[0]
        ]

        for point in points[1:]:

            previous = current[-1]

            distance = (
                self._pitch_distance(
                    previous.f0,
                    point.f0,
                )
            )

            time_gap = (
                point.time
                - previous.time
            )

            # Large time gaps indicate separate phrases.
            if time_gap > 0.100:

                self._append_region_if_valid(
                    regions,
                    current,
                )

                current = [
                    point
                ]

                continue

            if (
                distance
                <= self.stable_variation
            ):

                current.append(
                    point
                )

            else:

                self._append_region_if_valid(
                    regions,
                    current,
                )

                current = [
                    point
                ]

        self._append_region_if_valid(
            regions,
            current,
        )

        return regions

    def _append_region_if_valid(
        self,
        regions: list[StablePitchRegion],
        points: list[_PitchPoint],
    ):

        if len(points) < 2:

            return

        start = points[0].time
        end = points[-1].time

        duration = (
            end - start
        )

        if (
            duration
            < self.minimum_region_duration
        ):

            return

        values = np.asarray(
            [
                point.f0
                for point in points
            ],
            dtype=np.float64,
        )

        confidence = float(
            np.mean(
                [
                    point.confidence
                    for point in points
                ]
            )
        )

        low = float(
            np.percentile(
                values,
                5,
            )
        )

        high = float(
            np.percentile(
                values,
                95,
            )
        )

        variation = (
            self._pitch_distance(
                low,
                high,
            )
        )

        regions.append(
            StablePitchRegion(

                start_time=round(
                    start,
                    4,
                ),

                end_time=round(
                    end,
                    4,
                ),

                duration=round(
                    duration,
                    4,
                ),

                mean_f0=round(
                    float(
                        np.mean(values)
                    ),
                    2,
                ),

                median_f0=round(
                    float(
                        np.median(values)
                    ),
                    2,
                ),

                min_f0=round(
                    float(
                        np.min(values)
                    ),
                    2,
                ),

                max_f0=round(
                    float(
                        np.max(values)
                    ),
                    2,
                ),

                variation_semitones=round(
                    variation,
                    2,
                ),

                confidence=round(
                    confidence * 100.0,
                    2,
                ),
            )
        )

    # ========================================================
    # TRANSITIONS
    # ========================================================

    def _detect_transitions(
        self,
        points: list[_PitchPoint],
    ) -> list[PitchTransition]:
        """
        Detect genuine pitch movements.

        A movement must survive temporal confirmation.

        This prevents short harmonic/pitch-tracking spikes
        from being reported as real musical transitions.
        """

        transitions = []

        if len(points) < 3:

            return transitions

        for index in range(
            1,
            len(points) - 1,
        ):

            previous = points[
                index - 1
            ]

            current = points[
                index
            ]

            following = points[
                index + 1
            ]

            current_change = (
                self._signed_pitch_distance(
                    previous.f0,
                    current.f0,
                )
            )

            following_change = (
                self._signed_pitch_distance(
                    current.f0,
                    following.f0,
                )
            )

            # Current frame must move sufficiently.
            if (
                abs(current_change)
                < self.transition_threshold
            ):
                continue

            # The next frame must support the same direction.
            if (
                np.sign(
                    current_change
                )
                != np.sign(
                    following_change
                )
            ):
                continue

            # The movement must persist.
            persistence_end = index + 1

            while (
                persistence_end + 1
                < len(points)
            ):

                a = points[
                    persistence_end
                ]

                b = points[
                    persistence_end + 1
                ]

                movement = (
                    self._signed_pitch_distance(
                        a.f0,
                        b.f0,
                    )
                )

                if (
                    np.sign(
                        movement
                    )
                    != np.sign(
                        current_change
                    )
                ):

                    break

                persistence_end += 1

            end_point = points[
                persistence_end
            ]

            duration = (
                end_point.time
                - previous.time
            )

            if (
                duration
                < self.minimum_transition_duration
            ):
                continue

            total_change = (
                self._signed_pitch_distance(
                    previous.f0,
                    end_point.f0,
                )
            )

            if (
                abs(total_change)
                < self.transition_threshold
            ):
                continue

            if total_change > 0:

                direction = "UP"

            else:

                direction = "DOWN"

            confidence = float(
                np.mean(
                    [
                        point.confidence
                        for point in points[
                            index - 1:
                            persistence_end + 1
                        ]
                    ]
                )
            )

            transitions.append(
                PitchTransition(

                    start_time=round(
                        previous.time,
                        4,
                    ),

                    end_time=round(
                        end_point.time,
                        4,
                    ),

                    start_f0=round(
                        previous.f0,
                        2,
                    ),

                    end_f0=round(
                        end_point.f0,
                        2,
                    ),

                    semitone_change=round(
                        total_change,
                        2,
                    ),

                    direction=direction,

                    duration=round(
                        duration,
                        4,
                    ),

                    confidence=round(
                        confidence * 100.0,
                        2,
                    ),
                )
            )

        return self._deduplicate_transitions(
            transitions
        )

    # ========================================================
    # TRANSITION DEDUPLICATION
    # ========================================================

    @staticmethod
    def _deduplicate_transitions(
        transitions: list[PitchTransition],
    ) -> list[PitchTransition]:

        if not transitions:

            return []

        result = [
            transitions[0]
        ]

        for transition in transitions[1:]:

            previous = result[-1]

            if (
                transition.start_time
                <= previous.end_time
            ):

                if (
                    abs(
                        transition.semitone_change
                    )
                    > abs(
                        previous.semitone_change
                    )
                ):

                    result[-1] = transition

            else:

                result.append(
                    transition
                )

        return result

    # ========================================================
    # VIBRATO
    # ========================================================

    def _analyze_vibrato(
        self,
        points: list[_PitchPoint],
    ) -> VibratoReport:
        """
        Conservative vibrato detector.

        If vibrato is not confidently detected, confidence is
        explicitly returned as 0.
        """

        if len(points) < 40:

            return self._no_vibrato()

        times = np.asarray(
            [
                point.time
                for point in points
            ],
            dtype=np.float64,
        )

        f0 = np.asarray(
            [
                point.f0
                for point in points
            ],
            dtype=np.float64,
        )

        if np.any(f0 <= 0):

            return self._no_vibrato()

        time_diffs = np.diff(
            times
        )

        if time_diffs.size == 0:

            return self._no_vibrato()

        step = float(
            np.median(
                time_diffs
            )
        )

        if step <= 0:

            return self._no_vibrato()

        # Convert to MIDI.
        midi = (
            69.0
            + 12.0
            * np.log2(
                f0 / 440.0
            )
        )

        # Remove slow pitch movement.
        window = 41

        if window >= len(midi):

            window = (
                len(midi) // 2
            ) * 2 + 1

        if window < 9:

            return self._no_vibrato()

        kernel = (
            np.ones(
                window,
                dtype=np.float64,
            )
            / window
        )

        trend = np.convolve(
            midi,
            kernel,
            mode="same",
        )

        residual = (
            midi - trend
        )

        residual -= np.mean(
            residual
        )

        sample_rate = (
            1.0 / step
        )

        spectrum = np.fft.rfft(
            residual
        )

        frequencies = (
            np.fft.rfftfreq(
                len(residual),
                d=step,
            )
        )

        magnitude = np.abs(
            spectrum
        )

        valid = (
            (frequencies
             >= self.vibrato_min_rate)
            &
            (frequencies
             <= self.vibrato_max_rate)
        )

        indices = np.where(
            valid
        )[0]

        if indices.size == 0:

            return self._no_vibrato()

        best_index = indices[
            np.argmax(
                magnitude[
                    indices
                ]
            )
        ]

        rate = float(
            frequencies[
                best_index
            ]
        )

        amplitude = float(
            np.std(
                residual
            )
            * 2.0
        )

        if (
            amplitude < 0.12
            or amplitude > 2.5
        ):

            return self._no_vibrato()

        peak_strength = float(
            magnitude[
                best_index
            ]
        )

        average_band = float(
            np.mean(
                magnitude[
                    indices
                ]
            )
        )

        if average_band <= 1e-9:

            return self._no_vibrato()

        spectral_ratio = (
            peak_strength
            / average_band
        )

        if spectral_ratio < 2.0:

            return self._no_vibrato()

        duration = (
            times[-1]
            - times[0]
        )

        coverage = min(
            100.0,
            (
                duration
                / max(
                    duration,
                    1e-9,
                )
            )
            * 100.0,
        )

        confidence = np.clip(
            (
                min(
                    spectral_ratio
                    / 5.0,
                    1.0,
                )
                * 0.55
                +
                min(
                    amplitude
                    / 1.0,
                    1.0,
                )
                * 0.45
            ),
            0.0,
            1.0,
        )

        if confidence < 0.40:

            return self._no_vibrato()

        return VibratoReport(

            detected=True,

            rate_hz=round(
                rate,
                2,
            ),

            depth_semitones=round(
                amplitude,
                2,
            ),

            duration=round(
                duration,
                2,
            ),

            coverage=round(
                coverage,
                2,
            ),

            confidence=round(
                confidence * 100.0,
                2,
            ),
        )

    # ========================================================
    # NO VIBRATO
    # ========================================================

    @staticmethod
    def _no_vibrato() -> VibratoReport:

        return VibratoReport(
            detected=False,
            rate_hz=0.0,
            depth_semitones=0.0,
            duration=0.0,
            coverage=0.0,
            confidence=0.0,
        )

    # ========================================================
    # PERFORMANCE SCORE
    # ========================================================

    @staticmethod
    def _calculate_performance_score(
        pitch_report: PitchReport,
        average_confidence: float,
        stable_regions: list[StablePitchRegion],
        transitions: list[PitchTransition],
    ) -> float:
        """
        Calculate a conservative data-quality score.

        This is NOT a judgment of the singer.

        It estimates how coherent the extracted vocal
        performance data is for downstream processing.
        """

        coverage_score = min(
            100.0,
            pitch_report.voiced_coverage,
        )

        stability_score = (
            pitch_report.pitch_stability
        )

        confidence_score = (
            average_confidence
            * 100.0
        )

        # Stable regions are useful for note extraction.
        if stable_regions:

            stable_duration = sum(
                region.duration
                for region in stable_regions
            )

            stable_ratio = (
                stable_duration
                / max(
                    pitch_report.voiced_duration,
                    1e-9,
                )
            )

            region_score = min(
                100.0,
                stable_ratio * 100.0,
            )

        else:

            region_score = 0.0

        # Excessive short transitions indicate possible
        # pitch tracking instability.
        transition_density = (
            len(transitions)
            / max(
                pitch_report.voiced_duration,
                1.0,
            )
        )

        if transition_density <= 0.20:

            transition_score = 100.0

        elif transition_density >= 1.0:

            transition_score = 40.0

        else:

            transition_score = (
                100.0
                - (
                    transition_density
                    - 0.20
                )
                / 0.80
                * 60.0
            )

        score = (
            coverage_score * 0.20
            + stability_score * 0.35
            + confidence_score * 0.25
            + region_score * 0.15
            + transition_score * 0.05
        )

        return float(
            np.clip(
                score,
                0.0,
                100.0,
            )
        )

    # ========================================================
    # EMPTY REPORT
    # ========================================================

    @staticmethod
    def _empty_report(
        pitch_report: PitchReport,
    ) -> VocalPerformanceReport:

        return VocalPerformanceReport(

            file_name=(
                pitch_report.file_name
            ),

            duration=(
                pitch_report.duration
            ),

            voiced_duration=0.0,
            voiced_coverage=0.0,

            pitch_center_hz=0.0,
            pitch_center_midi=0.0,

            pitch_min_hz=0.0,
            pitch_max_hz=0.0,

            pitch_range_semitones=0.0,

            pitch_stability=0.0,

            average_confidence=0.0,

            pitch_movement_count=0,

            upward_movements=0,
            downward_movements=0,

            transitions=[],

            stable_regions=[],

            vibrato=(
                VocalPerformanceAnalyzer
                ._no_vibrato()
            ),

            performance_score=0.0,

            status="NEEDS_REVIEW",
        )

    # ========================================================
    # UTILITIES
    # ========================================================

    @staticmethod
    def _hz_to_midi(
        frequency: float,
    ) -> float:

        if frequency <= 0:

            return 0.0

        return float(
            69.0
            + 12.0
            * np.log2(
                frequency
                / 440.0
            )
        )

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

        return float(
            abs(
                12.0
                * np.log2(
                    f0_a
                    / f0_b
                )
            )
        )

    @staticmethod
    def _signed_pitch_distance(
        f0_a: float,
        f0_b: float,
    ) -> float:

        if (
            f0_a <= 0
            or f0_b <= 0
        ):

            return 0.0

        return float(
            12.0
            * np.log2(
                f0_b
                / f0_a
            )
        )