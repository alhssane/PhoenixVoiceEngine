"""
Phoenix Voice Studio
Pitch Cleanup Engine

Context-aware F0 cleanup layer.

Pipeline:

    Raw F0
       ↓
    Confidence Validation
       ↓
    Octave / Harmonic Detection
       ↓
    Pitch Spike Detection
       ↓
    Unstable Excursion Detection
       ↓
    Clean F0
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from src.analyzer.pitch_analyzer import PitchReport


# ============================================================
# DATA MODELS
# ============================================================


@dataclass
class CleanPitchFrame:
    """
    One cleaned pitch frame.
    """

    time: float
    f0: float
    confidence: float
    voiced: bool

    corrected: bool = False
    correction_type: str = "NONE"

    def to_dict(self) -> dict[str, Any]:

        return {
            "time": self.time,
            "f0": self.f0,
            "confidence": self.confidence,
            "voiced": self.voiced,
            "corrected": self.corrected,
            "correction_type": self.correction_type,
        }


@dataclass
class PitchCleanupReport:
    """
    Complete pitch cleanup report.
    """

    file_name: str
    duration: float

    original_frames: int
    cleaned_frames: int

    original_voiced_frames: int
    cleaned_voiced_frames: int

    corrected_frames: int

    octave_corrections: int
    spike_corrections: int
    unstable_corrections: int

    correction_ratio: float

    frames: list[CleanPitchFrame]

    status: str

    def to_dict(self) -> dict[str, Any]:

        return {
            "file_name": self.file_name,
            "duration": self.duration,
            "original_frames": self.original_frames,
            "cleaned_frames": self.cleaned_frames,
            "original_voiced_frames": (
                self.original_voiced_frames
            ),
            "cleaned_voiced_frames": (
                self.cleaned_voiced_frames
            ),
            "corrected_frames": (
                self.corrected_frames
            ),
            "octave_corrections": (
                self.octave_corrections
            ),
            "spike_corrections": (
                self.spike_corrections
            ),
            "unstable_corrections": (
                self.unstable_corrections
            ),
            "correction_ratio": (
                self.correction_ratio
            ),
            "frames": [
                frame.to_dict()
                for frame in self.frames
            ],
            "status": self.status,
        }


# ============================================================
# ENGINE
# ============================================================


class PitchCleanup:
    """
    Context-aware pitch cleanup engine.

    The cleanup operates only on F0 analysis data.
    The original audio is never modified.
    """

    def __init__(
        self,
        minimum_confidence: float = 0.20,

        context_radius: int = 4,

        octave_tolerance_semitones: float = 1.0,

        spike_threshold_semitones: float = 6.0,

        extreme_jump_semitones: float = 10.0,

        minimum_octave_support: int = 3,

        maximum_correction_duration: float = 0.20,
    ):

        self.minimum_confidence = (
            minimum_confidence
        )

        self.context_radius = (
            context_radius
        )

        self.octave_tolerance = (
            octave_tolerance_semitones
        )

        self.spike_threshold = (
            spike_threshold_semitones
        )

        self.extreme_jump = (
            extreme_jump_semitones
        )

        self.minimum_octave_support = (
            minimum_octave_support
        )

        self.maximum_correction_duration = (
            maximum_correction_duration
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def clean(
        self,
        pitch_report: PitchReport,
    ) -> PitchCleanupReport:

        raw_frames = pitch_report.frames

        if not raw_frames:

            return PitchCleanupReport(
                file_name=pitch_report.file_name,
                duration=pitch_report.duration,
                original_frames=0,
                cleaned_frames=0,
                original_voiced_frames=0,
                cleaned_voiced_frames=0,
                corrected_frames=0,
                octave_corrections=0,
                spike_corrections=0,
                unstable_corrections=0,
                correction_ratio=0.0,
                frames=[],
                status="EMPTY",
            )

        original_voiced = sum(
            1
            for frame in raw_frames
            if frame.voiced
            and frame.f0 > 0
        )

        cleaned = []

        octave_count = 0
        spike_count = 0
        unstable_count = 0

        # ----------------------------------------------------
        # Process every frame.
        # ----------------------------------------------------

        for index, frame in enumerate(
            raw_frames
        ):

            # ------------------------------------------------
            # Unvoiced frame
            # ------------------------------------------------

            if (
                not frame.voiced
                or frame.f0 <= 0
            ):

                cleaned.append(
                    CleanPitchFrame(
                        time=frame.time,
                        f0=0.0,
                        confidence=frame.confidence,
                        voiced=False,
                    )
                )

                continue

            original_f0 = float(
                frame.f0
            )

            f0 = original_f0

            corrected = False
            correction_type = "NONE"

            # =================================================
            # STEP 1
            # LOW CONFIDENCE
            # =================================================

            if (
                frame.confidence
                < self.minimum_confidence
            ):

                replacement = (
                    self._context_median(
                        raw_frames,
                        index,
                    )
                )

                if (
                    replacement > 0
                    and self._is_safe_replacement(
                        raw_frames,
                        index,
                        replacement,
                    )
                ):

                    f0 = replacement

                    corrected = True

                    correction_type = (
                        "LOW_CONFIDENCE"
                    )

            # =================================================
            # STEP 2
            # OCTAVE / HARMONIC
            #
            # Highest correction priority.
            #
            # Once OCTAVE is accepted, lower-priority
            # detectors MUST NOT overwrite the classification.
            # =================================================

            if not corrected:

                octave_result = (
                    self._detect_octave_correction(
                        raw_frames,
                        index,
                    )
                )

                if octave_result is not None:

                    replacement = octave_result

                    if (
                        replacement > 0
                        and self._is_safe_replacement(
                            raw_frames,
                            index,
                            replacement,
                        )
                    ):

                        f0 = replacement

                        corrected = True

                        correction_type = (
                            "OCTAVE"
                        )

                        octave_count += 1

            # =================================================
            # STEP 3
            # PITCH SPIKE
            #
            # Second priority.
            #
            # A frame already corrected as OCTAVE must never
            # be reclassified as SPIKE.
            # =================================================

            if not corrected:

                if self._is_pitch_spike(
                    raw_frames,
                    index,
                ):

                    replacement = (
                        self._context_median(
                            raw_frames,
                            index,
                        )
                    )

                    if (
                        replacement > 0
                        and self._is_safe_replacement(
                            raw_frames,
                            index,
                            replacement,
                        )
                    ):

                        f0 = replacement

                        corrected = True

                        correction_type = (
                            "SPIKE"
                        )

                        spike_count += 1

            # =================================================
            # STEP 4
            # UNSTABLE EXCURSION
            #
            # Lowest priority.
            #
            # It must never overwrite OCTAVE or SPIKE.
            # =================================================

            if not corrected:

                if self._is_unstable_excursion(
                    raw_frames,
                    index,
                ):

                    replacement = (
                        self._context_median(
                            raw_frames,
                            index,
                        )
                    )

                    if (
                        replacement > 0
                        and self._is_safe_replacement(
                            raw_frames,
                            index,
                            replacement,
                        )
                    ):

                        f0 = replacement

                        corrected = True

                        correction_type = (
                            "UNSTABLE"
                        )

                        unstable_count += 1

            cleaned.append(
                CleanPitchFrame(
                    time=frame.time,
                    f0=round(
                        f0,
                        4,
                    ),
                    confidence=frame.confidence,
                    voiced=True,
                    corrected=corrected,
                    correction_type=(
                        correction_type
                    ),
                )
            )

        # ====================================================
        # FINAL STATISTICS
        # ====================================================

        cleaned_voiced = sum(
            1
            for frame in cleaned
            if frame.voiced
            and frame.f0 > 0
        )

        corrected_total = sum(
            1
            for frame in cleaned
            if frame.corrected
        )

        correction_ratio = (
            corrected_total
            / max(
                original_voiced,
                1,
            )
            * 100.0
        )

        # ----------------------------------------------------
        # Status
        # ----------------------------------------------------

        if corrected_total == 0:

            status = "CLEAN"

        elif correction_ratio < 5.0:

            status = "CLEANED"

        elif correction_ratio < 15.0:

            status = (
                "SIGNIFICANT_CORRECTIONS"
            )

        else:

            status = "HEAVY_CORRECTIONS"

        return PitchCleanupReport(
            file_name=pitch_report.file_name,
            duration=pitch_report.duration,
            original_frames=len(raw_frames),
            cleaned_frames=len(cleaned),
            original_voiced_frames=(
                original_voiced
            ),
            cleaned_voiced_frames=(
                cleaned_voiced
            ),
            corrected_frames=(
                corrected_total
            ),
            octave_corrections=(
                octave_count
            ),
            spike_corrections=(
                spike_count
            ),
            unstable_corrections=(
                unstable_count
            ),
            correction_ratio=round(
                correction_ratio,
                2,
            ),
            frames=cleaned,
            status=status,
        )

    # ========================================================
    # CONTEXT VALUES
    # ========================================================

    def _get_context(
        self,
        frames,
        index: int,
    ) -> list[float]:

        start = max(
            0,
            index - self.context_radius,
        )

        end = min(
            len(frames),
            index
            + self.context_radius
            + 1,
        )

        values = []

        for position in range(
            start,
            end,
        ):

            if position == index:
                continue

            frame = frames[
                position
            ]

            if (
                frame.voiced
                and frame.f0 > 0
                and frame.confidence
                >= self.minimum_confidence
            ):

                values.append(
                    float(frame.f0)
                )

        return values

    # ========================================================
    # CONTEXT MEDIAN
    # ========================================================

    def _context_median(
        self,
        frames,
        index: int,
    ) -> float:

        values = self._get_context(
            frames,
            index,
        )

        if not values:

            return 0.0

        return float(
            np.median(values)
        )

    # ========================================================
    # OCTAVE DETECTION V3
    # ========================================================

    def _detect_octave_correction(
        self,
        frames,
        index: int,
    ) -> float | None:

        """
        Detect octave / harmonic tracking errors.

        Instead of asking:

            "Is the current frame an outlier?"

        we ask:

            "Does the surrounding pitch contain strong
             evidence for the current pitch being approximately
             one octave above or below the dominant pitch?"

        This allows the detector to catch multiple consecutive
        erroneous frames.
        """

        current = frames[index]

        if (
            not current.voiced
            or current.f0 <= 0
        ):

            return None

        context = self._get_context(
            frames,
            index,
        )

        if (
            len(context)
            < self.minimum_octave_support
        ):

            return None

        current_f0 = float(
            current.f0
        )

        # ----------------------------------------------------
        # Candidate lower pitch.
        #
        # Example:
        #
        # 400 Hz → approximately 200 Hz
        # ----------------------------------------------------

        lower_candidate = (
            current_f0 / 2.0
        )

        lower_support = 0

        lower_values = []

        for value in context:

            distance = abs(
                self._semitones(
                    lower_candidate,
                    value,
                )
            )

            if (
                distance
                <= self.octave_tolerance
            ):

                lower_support += 1

                lower_values.append(
                    value
                )

        # ----------------------------------------------------
        # Candidate upper pitch.
        #
        # Example:
        #
        # 200 Hz → approximately 400 Hz
        # ----------------------------------------------------

        upper_candidate = (
            current_f0 * 2.0
        )

        upper_support = 0

        upper_values = []

        for value in context:

            distance = abs(
                self._semitones(
                    upper_candidate,
                    value,
                )
            )

            if (
                distance
                <= self.octave_tolerance
            ):

                upper_support += 1

                upper_values.append(
                    value
                )

        # ----------------------------------------------------
        # Strong lower-pitch support.
        #
        # Current pitch is approximately one octave above
        # surrounding pitch.
        # ----------------------------------------------------

        if (
            lower_support
            >= self.minimum_octave_support
        ):

            replacement = float(
                np.median(
                    lower_values
                )
            )

            if self._octave_context_is_consistent(
                context,
                replacement,
            ):

                return replacement

        # ----------------------------------------------------
        # Strong upper-pitch support.
        #
        # Current pitch is approximately one octave below
        # surrounding pitch.
        # ----------------------------------------------------

        if (
            upper_support
            >= self.minimum_octave_support
        ):

            replacement = float(
                np.median(
                    upper_values
                )
            )

            if self._octave_context_is_consistent(
                context,
                replacement,
            ):

                return replacement

        return None

    # ========================================================
    # OCTAVE CONTEXT CONSISTENCY
    # ========================================================

    def _octave_context_is_consistent(
        self,
        context: list[float],
        reference: float,
    ) -> bool:

        if (
            reference <= 0
            or not context
        ):

            return False

        close_count = 0

        for value in context:

            distance = abs(
                self._semitones(
                    reference,
                    value,
                )
            )

            # Normal pitch neighborhood.
            if distance <= 2.0:

                close_count += 1

        required = max(
            3,
            int(
                len(context)
                * 0.50
            ),
        )

        return (
            close_count
            >= required
        )

    # ========================================================
    # PITCH SPIKE
    # ========================================================

    def _is_pitch_spike(
        self,
        frames,
        index: int,
    ) -> bool:

        current = frames[index]

        if (
            not current.voiced
            or current.f0 <= 0
        ):

            return False

        context = self._get_context(
            frames,
            index,
        )

        if len(context) < 4:

            return False

        reference = float(
            np.median(context)
        )

        if reference <= 0:

            return False

        distance = abs(
            self._semitones(
                reference,
                current.f0,
            )
        )

        if (
            distance
            < self.spike_threshold
        ):

            return False

        close_count = 0

        for value in context:

            if (
                abs(
                    self._semitones(
                        reference,
                        value,
                    )
                )
                <= 2.0
            ):

                close_count += 1

        required = max(
            3,
            int(
                len(context)
                * 0.60
            ),
        )

        return (
            close_count
            >= required
        )

    # ========================================================
    # UNSTABLE EXCURSION
    # ========================================================

    def _is_unstable_excursion(
        self,
        frames,
        index: int,
    ) -> bool:

        if index < 1:

            return False

        if index >= len(frames) - 1:

            return False

        current = frames[
            index
        ]

        previous = frames[
            index - 1
        ]

        following = frames[
            index + 1
        ]

        if not (
            current.voiced
            and previous.voiced
            and following.voiced
        ):

            return False

        if (
            current.f0 <= 0
            or previous.f0 <= 0
            or following.f0 <= 0
        ):

            return False

        incoming = (
            self._semitones(
                previous.f0,
                current.f0,
            )
        )

        outgoing = (
            self._semitones(
                current.f0,
                following.f0,
            )
        )

        # ----------------------------------------------------
        # Direction must reverse.
        # ----------------------------------------------------

        reversed_direction = (
            np.sign(incoming)
            != np.sign(outgoing)
        )

        if not reversed_direction:

            return False

        # ----------------------------------------------------
        # Both movements must be substantial.
        # ----------------------------------------------------

        if (
            abs(incoming)
            < self.extreme_jump
        ):

            return False

        if (
            abs(outgoing)
            < self.extreme_jump
        ):

            return False

        # ----------------------------------------------------
        # Compare with wider context.
        # ----------------------------------------------------

        context = self._get_context(
            frames,
            index,
        )

        if len(context) < 4:

            return False

        reference = float(
            np.median(context)
        )

        if reference <= 0:

            return False

        distance = abs(
            self._semitones(
                reference,
                current.f0,
            )
        )

        return (
            distance
            >= self.extreme_jump
        )

    # ========================================================
    # SAFE REPLACEMENT
    # ========================================================

    def _is_safe_replacement(
        self,
        frames,
        index: int,
        replacement: float,
    ) -> bool:

        if replacement <= 0:

            return False

        current = frames[
            index
        ]

        if current.f0 <= 0:

            return False

        difference = abs(
            self._semitones(
                current.f0,
                replacement,
            )
        )

        # If the correction is extremely small,
        # there is no reason to modify the value.
        if difference < 1.0:

            return False

        return True

    # ========================================================
    # SEMITONE DISTANCE
    # ========================================================

    @staticmethod
    def _semitones(
        reference: float,
        value: float,
    ) -> float:

        if (
            reference <= 0
            or value <= 0
        ):

            return 0.0

        return float(
            12.0
            * np.log2(
                value
                / reference
            )
        )