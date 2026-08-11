from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional


class MelodyAnalyzer:
    """
    PhoenixVoiceEngine
    Melody Analyzer V1.2.1 — Performance Classification

    V1.2.1 keeps the Contour-Aware melody segmentation from V1.2 and
    improves performance classification.

    Important design rule:
        Performance movement does NOT automatically create a new melody event.

    The event contains:
        - stable melodic identity
        - raw pitch contour
        - natural variation
        - vibrato
        - slide / glissando
        - true pitch-bend / ornament candidates
        - transition information
    """

    # Keep legacy version for V1.0 test compatibility.
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.2.1"

    DEFAULT_MIN_EVENT_DURATION = 0.08
    DEFAULT_MAX_GAP = 0.08
    DEFAULT_NOTE_CHANGE_SEMITONES = 0.75
    DEFAULT_MIN_VOICED_PROBABILITY = 0.50

    DEFAULT_MIN_EVENT_VOICED_RATIO = 0.20
    DEFAULT_MIN_EVENT_CONFIDENCE = 0.20

    DEFAULT_MELODY_TOLERANCE_SEMITONES = 0.75
    DEFAULT_CONTOUR_TOLERANCE_SEMITONES = 2.50
    DEFAULT_MAX_CONTOUR_DEVIATION_SEMITONES = 3.50
    DEFAULT_MIN_STABLE_FRAMES = 3

    # Performance classification.
    DEFAULT_NATURAL_VARIATION_SEMITONES = 0.35
    DEFAULT_VIBRATO_MIN_DEPTH_SEMITONES = 0.15
    DEFAULT_VIBRATO_MAX_DEPTH_SEMITONES = 1.50
    DEFAULT_VIBRATO_MIN_CYCLES = 1.5

    DEFAULT_SLIDE_MIN_RANGE_SEMITONES = 0.75
    DEFAULT_SLIDE_MIN_SLOPE = 0.80
    DEFAULT_SLIDE_MIN_DIRECTIONAL_RATIO = 0.65

    DEFAULT_ORNAMENT_MAX_DURATION = 0.45
    DEFAULT_ORNAMENT_MIN_RANGE_SEMITONES = 0.50
    DEFAULT_ORNAMENT_MAX_RANGE_SEMITONES = 3.50
    DEFAULT_ORNAMENT_RETURN_TOLERANCE = 0.45

    def __init__(
        self,
        min_event_duration: float = DEFAULT_MIN_EVENT_DURATION,
        max_gap: float = DEFAULT_MAX_GAP,
        note_change_semitones: float = DEFAULT_NOTE_CHANGE_SEMITONES,
        min_voiced_probability: float = DEFAULT_MIN_VOICED_PROBABILITY,
        min_event_voiced_ratio: float = DEFAULT_MIN_EVENT_VOICED_RATIO,
        min_event_confidence: float = DEFAULT_MIN_EVENT_CONFIDENCE,
        melody_tolerance_semitones: float = DEFAULT_MELODY_TOLERANCE_SEMITONES,
        contour_tolerance_semitones: float = DEFAULT_CONTOUR_TOLERANCE_SEMITONES,
        max_contour_deviation_semitones: float = DEFAULT_MAX_CONTOUR_DEVIATION_SEMITONES,
        min_stable_frames: int = DEFAULT_MIN_STABLE_FRAMES,
        natural_variation_semitones: float = DEFAULT_NATURAL_VARIATION_SEMITONES,
        vibrato_min_depth_semitones: float = DEFAULT_VIBRATO_MIN_DEPTH_SEMITONES,
        vibrato_max_depth_semitones: float = DEFAULT_VIBRATO_MAX_DEPTH_SEMITONES,
        vibrato_min_cycles: float = DEFAULT_VIBRATO_MIN_CYCLES,
        slide_min_range_semitones: float = DEFAULT_SLIDE_MIN_RANGE_SEMITONES,
        slide_min_slope: float = DEFAULT_SLIDE_MIN_SLOPE,
        slide_min_directional_ratio: float = DEFAULT_SLIDE_MIN_DIRECTIONAL_RATIO,
        ornament_max_duration: float = DEFAULT_ORNAMENT_MAX_DURATION,
        ornament_min_range_semitones: float = DEFAULT_ORNAMENT_MIN_RANGE_SEMITONES,
        ornament_max_range_semitones: float = DEFAULT_ORNAMENT_MAX_RANGE_SEMITONES,
        ornament_return_tolerance: float = DEFAULT_ORNAMENT_RETURN_TOLERANCE,
    ) -> None:
        positive = (
            ("min_event_duration", min_event_duration),
            ("note_change_semitones", note_change_semitones),
            ("melody_tolerance_semitones", melody_tolerance_semitones),
            ("contour_tolerance_semitones", contour_tolerance_semitones),
            ("max_contour_deviation_semitones", max_contour_deviation_semitones),
            ("natural_variation_semitones", natural_variation_semitones),
            ("vibrato_min_depth_semitones", vibrato_min_depth_semitones),
            ("vibrato_min_cycles", vibrato_min_cycles),
            ("slide_min_range_semitones", slide_min_range_semitones),
            ("slide_min_slope", slide_min_slope),
            ("ornament_max_duration", ornament_max_duration),
            ("ornament_min_range_semitones", ornament_min_range_semitones),
            ("ornament_max_range_semitones", ornament_max_range_semitones),
        )
        for name, value in positive:
            if float(value) <= 0:
                raise ValueError(f"{name} must be positive.")

        if max_gap < 0:
            raise ValueError("max_gap cannot be negative.")
        if not 0.0 <= min_voiced_probability <= 1.0:
            raise ValueError("min_voiced_probability must be between 0 and 1.")
        if not 0.0 <= min_event_voiced_ratio <= 1.0:
            raise ValueError("min_event_voiced_ratio must be between 0 and 1.")
        if not 0.0 <= min_event_confidence <= 1.0:
            raise ValueError("min_event_confidence must be between 0 and 1.")
        if not 0.0 <= slide_min_directional_ratio <= 1.0:
            raise ValueError("slide_min_directional_ratio must be between 0 and 1.")
        if ornament_max_range_semitones < ornament_min_range_semitones:
            raise ValueError(
                "ornament_max_range_semitones must be >= ornament_min_range_semitones."
            )
        if vibrato_max_depth_semitones < vibrato_min_depth_semitones:
            raise ValueError(
                "vibrato_max_depth_semitones must be >= vibrato_min_depth_semitones."
            )
        if min_stable_frames < 1:
            raise ValueError("min_stable_frames must be >= 1.")

        self.min_event_duration = float(min_event_duration)
        self.max_gap = float(max_gap)
        self.note_change_semitones = float(note_change_semitones)
        self.min_voiced_probability = float(min_voiced_probability)
        self.min_event_voiced_ratio = float(min_event_voiced_ratio)
        self.min_event_confidence = float(min_event_confidence)

        self.melody_tolerance_semitones = float(melody_tolerance_semitones)
        self.contour_tolerance_semitones = float(contour_tolerance_semitones)
        self.max_contour_deviation_semitones = float(
            max_contour_deviation_semitones
        )
        self.min_stable_frames = int(min_stable_frames)

        self.natural_variation_semitones = float(
            natural_variation_semitones
        )
        self.vibrato_min_depth_semitones = float(
            vibrato_min_depth_semitones
        )
        self.vibrato_max_depth_semitones = float(
            vibrato_max_depth_semitones
        )
        self.vibrato_min_cycles = float(vibrato_min_cycles)

        self.slide_min_range_semitones = float(slide_min_range_semitones)
        self.slide_min_slope = float(slide_min_slope)
        self.slide_min_directional_ratio = float(
            slide_min_directional_ratio
        )

        self.ornament_max_duration = float(ornament_max_duration)
        self.ornament_min_range_semitones = float(
            ornament_min_range_semitones
        )
        self.ornament_max_range_semitones = float(
            ornament_max_range_semitones
        )
        self.ornament_return_tolerance = float(
            ornament_return_tolerance
        )

    # ============================================================
    # Loading
    # ============================================================

    def load_pitch(self, pitch_path: str | Path) -> Dict[str, Any]:
        path = Path(pitch_path)
        if not path.exists():
            raise FileNotFoundError(f"Pitch file not found: {path}")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Pitch data must be a dictionary.")

        pitch = data.get("pitch")
        if not isinstance(pitch, dict):
            raise ValueError("Pitch data must contain a pitch object.")

        frames = pitch.get("frames")
        if not isinstance(frames, list):
            raise ValueError("Pitch data must contain a frames list.")
        if not frames:
            raise ValueError("Pitch frame list is empty.")

        return data

    # ============================================================
    # Numeric helpers
    # ============================================================

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            result = float(value)
            return result if math.isfinite(result) else default
        except (TypeError, ValueError):
            return default

    @staticmethod
    def hz_to_midi(f0_hz: Optional[float]) -> Optional[float]:
        if f0_hz is None:
            return None
        try:
            f0 = float(f0_hz)
        except (TypeError, ValueError):
            return None

        if not math.isfinite(f0) or f0 <= 0:
            return None

        return 69.0 + 12.0 * math.log2(f0 / 440.0)

    @staticmethod
    def midi_to_hz(midi: float) -> float:
        return 440.0 * (2.0 ** ((float(midi) - 69.0) / 12.0))

    @staticmethod
    def midi_to_note_name(midi: Optional[float]) -> Optional[str]:
        if midi is None:
            return None

        names = [
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B",
        ]

        midi_int = int(round(float(midi)))
        note_index = midi_int % 12
        octave = (midi_int // 12) - 1

        return f"{names[note_index]}{octave}"

    @staticmethod
    def _mean(values: List[float]) -> float:
        return (
            sum(values) / len(values)
            if values
            else 0.0
        )

    # ============================================================
    # Frame handling
    # ============================================================

    def _frame_probability(
        self,
        frame: Dict[str, Any],
    ) -> float:
        probability = self._safe_float(
            frame.get("voiced_probability"),
            0.0,
        )
        return max(
            0.0,
            min(1.0, probability),
        )

    def _is_pitch_valid(
        self,
        frame: Dict[str, Any],
    ) -> bool:
        return self._safe_float(
            frame.get("f0_hz"),
            0.0,
        ) > 0.0

    def _is_voiced_flag(
        self,
        frame: Dict[str, Any],
    ) -> bool:
        return bool(frame.get("voiced", False))

    def _is_usable_frame(
        self,
        frame: Dict[str, Any],
    ) -> bool:
        # V1.2.1 intentionally uses F0 + voiced flag.
        # voiced_probability is a quality feature, not a hard gate.
        return (
            isinstance(frame, dict)
            and self._is_pitch_valid(frame)
            and self._is_voiced_flag(frame)
        )

    def _usable_frames(
        self,
        frames: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        usable: List[Dict[str, Any]] = []

        for frame in frames:
            if not self._is_usable_frame(frame):
                continue

            time = self._safe_float(
                frame.get("time"),
                -1.0,
            )
            f0 = self._safe_float(
                frame.get("f0_hz"),
                0.0,
            )

            if time < 0.0 or f0 <= 0.0:
                continue

            midi = self.hz_to_midi(f0)
            if midi is None:
                continue

            usable.append(
                {
                    "frame_index": int(
                        self._safe_float(
                            frame.get(
                                "frame_index",
                                len(usable),
                            ),
                            len(usable),
                        )
                    ),
                    "time": time,
                    "f0_hz": f0,
                    "midi": midi,
                    "voiced": True,
                    "voiced_probability": self._frame_probability(
                        frame
                    ),
                }
            )

        usable.sort(
            key=lambda item: item["time"]
        )

        return usable

    # ============================================================
    # Contour-aware segmentation
    # ============================================================

    @staticmethod
    def _median_midi(
        segment: List[Dict[str, Any]],
    ) -> float:
        return float(
            median(
                [item["midi"] for item in segment]
            )
        )

    def _local_stability(
        self,
        values: List[float],
    ) -> float:
        if not values:
            return 0.0

        center = float(median(values))
        deviations = [
            abs(value - center)
            for value in values
        ]

        mean_deviation = self._mean(
            deviations
        )

        return max(
            0.0,
            1.0 - min(
                1.0,
                mean_deviation / 2.0,
            ),
        )

    def _should_continue_contour_event(
        self,
        current: List[Dict[str, Any]],
        frame: Dict[str, Any],
    ) -> bool:
        previous = current[-1]

        time_gap = (
            frame["time"]
            - previous["time"]
        )

        if time_gap < 0.0:
            return False

        if time_gap > self.max_gap:
            return False

        center = self._median_midi(current)

        deviation = abs(
            frame["midi"] - center
        )

        if deviation <= self.melody_tolerance_semitones:
            return True

        if deviation <= self.contour_tolerance_semitones:
            if len(current) < self.min_stable_frames:
                return True

            recent = current[
                -min(5, len(current)):
            ]

            recent_center = self._median_midi(
                recent
            )

            recent_deviation = abs(
                frame["midi"] - recent_center
            )

            return (
                recent_deviation
                <= self.max_contour_deviation_semitones
            )

        return False

    def _build_segments(
        self,
        frames: List[Dict[str, Any]],
    ) -> List[List[Dict[str, Any]]]:
        if not frames:
            return []

        segments: List[
            List[Dict[str, Any]]
        ] = []

        current = [frames[0]]

        for frame in frames[1:]:
            if self._should_continue_contour_event(
                current,
                frame,
            ):
                current.append(frame)
            else:
                segments.append(current)
                current = [frame]

        if current:
            segments.append(current)

        return segments

    # ============================================================
    # Signal helpers
    # ============================================================

    @staticmethod
    def _pitch_direction(
        values: List[float],
    ) -> str:
        if len(values) < 2:
            return "STABLE"

        delta = values[-1] - values[0]

        if delta > 0.35:
            return "ASCENDING"

        if delta < -0.35:
            return "DESCENDING"

        return "STABLE"

    @staticmethod
    def _linear_slope(
        times: List[float],
        values: List[float],
    ) -> float:
        if len(times) < 2:
            return 0.0

        mean_time = sum(times) / len(times)
        mean_value = sum(values) / len(values)

        denominator = sum(
            (time - mean_time) ** 2
            for time in times
        )

        if denominator <= 1e-12:
            return 0.0

        numerator = sum(
            (time - mean_time)
            * (value - mean_value)
            for time, value in zip(
                times,
                values,
            )
        )

        return numerator / denominator

    @staticmethod
    def _directional_ratio(
        values: List[float],
    ) -> float:
        if len(values) < 3:
            return 0.0

        deltas = [
            values[index + 1] - values[index]
            for index in range(
                len(values) - 1
            )
        ]

        total = sum(
            abs(delta)
            for delta in deltas
        )

        if total <= 1e-12:
            return 0.0

        net = abs(
            values[-1] - values[0]
        )

        return net / total

    # ============================================================
    # Vibrato
    # ============================================================

    def _detect_vibrato(
        self,
        midi_values: List[float],
        times: List[float],
    ) -> Dict[str, Any]:
        if len(midi_values) < 8:
            return {
                "detected": False,
                "cycles_estimate": 0.0,
                "depth_semitones": 0.0,
            }

        center = float(
            median(midi_values)
        )

        centered = [
            value - center
            for value in midi_values
        ]

        depth = (
            max(centered)
            - min(centered)
        ) / 2.0

        if (
            depth
            < self.vibrato_min_depth_semitones
        ):
            return {
                "detected": False,
                "cycles_estimate": 0.0,
                "depth_semitones": round(
                    depth,
                    4,
                ),
            }

        crossings = 0
        previous_sign = 0

        for value in centered:
            if value > 0:
                sign = 1
            elif value < 0:
                sign = -1
            else:
                sign = previous_sign

            if (
                previous_sign
                and sign != previous_sign
            ):
                crossings += 1

            previous_sign = sign

        cycles = crossings / 2.0

        duration = (
            max(
                0.0,
                times[-1] - times[0],
            )
            if len(times) >= 2
            else 0.0
        )

        detected = (
            cycles
            >= self.vibrato_min_cycles
            and self.vibrato_min_depth_semitones
            <= depth
            <= self.vibrato_max_depth_semitones
            and duration >= 0.20
        )

        return {
            "detected": bool(detected),
            "cycles_estimate": round(
                cycles,
                3,
            ),
            "depth_semitones": round(
                depth,
                4,
            ),
        }

    # ============================================================
    # Performance classification V1.2.1
    # ============================================================

    def _classify_performance(
        self,
        midi_values: List[float],
        times: List[float],
        melody_midi: float,
        duration: float,
    ) -> Dict[str, Any]:
        if not midi_values:
            return {
                "primary_type": "UNKNOWN",
                "natural_variation": False,
                "vibrato": {
                    "detected": False,
                    "cycles_estimate": 0.0,
                    "depth_semitones": 0.0,
                },
                "slide": {
                    "detected": False,
                    "direction": "NONE",
                    "range_semitones": 0.0,
                    "directional_ratio": 0.0,
                },
                "pitch_bend": {
                    "detected": False,
                    "range_semitones": 0.0,
                },
                "ornament": {
                    "detected": False,
                    "type": "NONE",
                },
            }

        offsets = [
            value - melody_midi
            for value in midi_values
        ]

        minimum = min(midi_values)
        maximum = max(midi_values)

        range_semitones = (
            maximum - minimum
        )

        slope = self._linear_slope(
            times,
            midi_values,
        )

        directional_ratio = (
            self._directional_ratio(
                midi_values
            )
        )

        direction = self._pitch_direction(
            midi_values
        )

        vibrato = self._detect_vibrato(
            midi_values,
            times,
        )

        # Natural variation: small movement around the stable note.
        max_abs_offset = max(
            abs(offset)
            for offset in offsets
        )

        natural_variation = (
            max_abs_offset
            <= self.natural_variation_semitones
        )

        # Slide / glissando:
        # broad directional movement, not oscillation.
        slide = (
            range_semitones
            >= self.slide_min_range_semitones
            and abs(slope)
            >= self.slide_min_slope
            and directional_ratio
            >= self.slide_min_directional_ratio
            and not vibrato["detected"]
        )

        # Short return-to-center gesture.
        ornament = False
        ornament_type = "NONE"

        if (
            duration
            <= self.ornament_max_duration
            and self.ornament_min_range_semitones
            <= range_semitones
            <= self.ornament_max_range_semitones
            and len(midi_values) >= 3
        ):
            center_distance_start = abs(
                midi_values[0] - melody_midi
            )
            center_distance_end = abs(
                midi_values[-1] - melody_midi
            )

            middle_distance = max(
                abs(
                    value - melody_midi
                )
                for value in midi_values[
                    1:-1
                ]
            ) if len(midi_values) > 2 else 0.0

            returns_to_center = (
                center_distance_start
                <= self.ornament_return_tolerance
                and center_distance_end
                <= self.ornament_return_tolerance
                and middle_distance
                >= self.ornament_min_range_semitones
            )

            if returns_to_center:
                ornament = True

                if (
                    midi_values[
                        len(midi_values) // 2
                    ]
                    > melody_midi
                ):
                    ornament_type = "UPPER_NEIGHBOR"
                else:
                    ornament_type = "LOWER_NEIGHBOR"

        # True bend is now conservative:
        # it must be non-natural, non-vibrato, non-slide,
        # and have meaningful movement around the stable note.
        true_bend = (
            range_semitones
            >= self.natural_variation_semitones
            and not natural_variation
            and not vibrato["detected"]
            and not slide
            and not ornament
        )

        if vibrato["detected"]:
            primary_type = "VIBRATO"
        elif slide:
            primary_type = "SLIDE"
        elif ornament:
            primary_type = "ORNAMENT"
        elif true_bend:
            primary_type = "PITCH_BEND"
        else:
            primary_type = "NATURAL_VARIATION"

        return {
            "primary_type": primary_type,
            "natural_variation": bool(
                natural_variation
            ),
            "range_semitones": round(
                range_semitones,
                4,
            ),
            "slope_semitones_per_second": round(
                slope,
                6,
            ),
            "direction": direction,
            "directional_ratio": round(
                directional_ratio,
                6,
            ),
            "vibrato": vibrato,
            "slide": {
                "detected": bool(slide),
                "direction": (
                    direction
                    if slide
                    else "NONE"
                ),
                "range_semitones": round(
                    range_semitones,
                    4,
                ),
                "directional_ratio": round(
                    directional_ratio,
                    6,
                ),
            },
            "pitch_bend": {
                "detected": bool(true_bend),
                "range_semitones": round(
                    range_semitones,
                    4,
                ),
            },
            "ornament": {
                "detected": bool(ornament),
                "type": ornament_type,
            },
        }

    # ============================================================
    # Event creation
    # ============================================================

    def _segment_to_event(
        self,
        segment: List[Dict[str, Any]],
        event_index: int,
    ) -> Optional[Dict[str, Any]]:
        if not segment:
            return None

        start_time = float(
            segment[0]["time"]
        )

        if len(segment) >= 2:
            spacing = (
                segment[-1]["time"]
                - segment[-2]["time"]
            )

            if spacing <= 0:
                spacing = 0.01
        else:
            spacing = 0.01

        end_time = (
            segment[-1]["time"]
            + spacing
        )

        duration = (
            end_time
            - start_time
        )

        if (
            duration + 1e-6
            < self.min_event_duration
        ):
            return None

        midis = [
            item["midi"]
            for item in segment
        ]

        f0s = [
            item["f0_hz"]
            for item in segment
        ]

        probabilities = [
            item["voiced_probability"]
            for item in segment
        ]

        stable_midi = float(
            median(midis)
        )

        midi_note = int(
            round(stable_midi)
        )

        note_name = self.midi_to_note_name(
            midi_note
        )

        probability = self._mean(
            probabilities
        )

        stability = self._local_stability(
            midis
        )

        voiced_ratio = 1.0

        event_confidence = (
            0.45 * probability
            + 0.35 * stability
            + 0.20 * voiced_ratio
        )

        if (
            voiced_ratio
            < self.min_event_voiced_ratio
        ):
            return None

        if (
            event_confidence
            < self.min_event_confidence
        ):
            return None

        times = [
            item["time"]
            for item in segment
        ]

        performance = (
            self._classify_performance(
                midis,
                times,
                stable_midi,
                duration,
            )
        )

        contour = [
            {
                "time": round(
                    item["time"],
                    6,
                ),
                "f0_hz": round(
                    item["f0_hz"],
                    4,
                ),
                "midi": round(
                    item["midi"],
                    4,
                ),
                "offset_from_melody_semitones": round(
                    item["midi"]
                    - stable_midi,
                    4,
                ),
                "voiced_probability": round(
                    item[
                        "voiced_probability"
                    ],
                    6,
                ),
            }
            for item in segment
        ]

        pitch_min = min(midis)
        pitch_max = max(midis)

        return {
            "event_index": int(
                event_index
            ),
            "start_time": round(
                start_time,
                6,
            ),
            "end_time": round(
                end_time,
                6,
            ),
            "duration": round(
                duration,
                6,
            ),

            # Stable melodic identity.
            "midi_note": midi_note,
            "note_name": note_name,
            "midi_mean": round(
                self._mean(midis),
                4,
            ),
            "f0_mean_hz": round(
                self._mean(f0s),
                4,
            ),

            "confidence": round(
                event_confidence,
                6,
            ),
            "frame_confidence": round(
                probability,
                6,
            ),
            "stability": round(
                stability,
                6,
            ),
            "voiced_ratio": round(
                voiced_ratio,
                6,
            ),
            "frame_count": len(segment),

            "performance": performance,

            # Backward-compatible summary fields.
            "pitch_direction": performance[
                "direction"
            ],
            "pitch_bend_detected": performance[
                "pitch_bend"
            ]["detected"],
            "pitch_bend_range_semitones": performance[
                "pitch_bend"
            ]["range_semitones"],
            "vibrato_detected": performance[
                "vibrato"
            ]["detected"],

            "transition": {
                "start_midi": round(
                    midis[0],
                    4,
                ),
                "end_midi": round(
                    midis[-1],
                    4,
                ),
                "delta_semitones": round(
                    midis[-1]
                    - midis[0],
                    4,
                ),
                "direction": self._pitch_direction(
                    midis
                ),
            },

            # Critical performance payload.
            "pitch_contour": contour,
        }

    # Legacy-compatible alias.
    def _build_event(
        self,
        segment: List[Dict[str, Any]],
        event_index: int,
    ) -> Optional[Dict[str, Any]]:
        return self._segment_to_event(
            segment,
            event_index,
        )

    # ============================================================
    # Melody extraction
    # ============================================================

    def extract_melody(
        self,
        frames: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        usable = self._usable_frames(
            frames
        )

        segments = self._build_segments(
            usable
        )

        events: List[
            Dict[str, Any]
        ] = []

        for segment in segments:
            event = self._segment_to_event(
                segment,
                len(events) + 1,
            )

            if event is not None:
                events.append(event)

        events.sort(
            key=lambda item: (
                item["start_time"],
                item["event_index"],
            )
        )

        for index, event in enumerate(
            events,
            start=1,
        ):
            event["event_index"] = index

        return {
            "source_frame_count": len(frames),
            "usable_frame_count": len(usable),
            "event_count": len(events),
            "events": events,
        }

    # ============================================================
    # Full analysis
    # ============================================================

    def analyze(
        self,
        pitch_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(
            pitch_data,
            dict,
        ):
            raise ValueError(
                "pitch_data must be a dictionary."
            )

        pitch = pitch_data.get(
            "pitch"
        )

        if not isinstance(
            pitch,
            dict,
        ):
            raise ValueError(
                "pitch_data must contain a pitch object."
            )

        frames = pitch.get(
            "frames"
        )

        if not isinstance(
            frames,
            list,
        ):
            raise ValueError(
                "pitch_data must contain a frames list."
            )

        melody = self.extract_melody(
            frames
        )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "source": pitch_data.get(
                "source"
            ),

            "analysis": {
                "min_event_duration": (
                    self.min_event_duration
                ),
                "max_gap": self.max_gap,
                "note_change_semitones": (
                    self.note_change_semitones
                ),
                "min_voiced_probability": (
                    self.min_voiced_probability
                ),
                "min_event_voiced_ratio": (
                    self.min_event_voiced_ratio
                ),
                "min_event_confidence": (
                    self.min_event_confidence
                ),
                "melody_tolerance_semitones": (
                    self.melody_tolerance_semitones
                ),
                "contour_tolerance_semitones": (
                    self.contour_tolerance_semitones
                ),
                "max_contour_deviation_semitones": (
                    self.max_contour_deviation_semitones
                ),
                "min_stable_frames": (
                    self.min_stable_frames
                ),

                "natural_variation_semitones": (
                    self.natural_variation_semitones
                ),
                "vibrato_min_depth_semitones": (
                    self.vibrato_min_depth_semitones
                ),
                "vibrato_max_depth_semitones": (
                    self.vibrato_max_depth_semitones
                ),
                "vibrato_min_cycles": (
                    self.vibrato_min_cycles
                ),
                "slide_min_range_semitones": (
                    self.slide_min_range_semitones
                ),
                "slide_min_slope": (
                    self.slide_min_slope
                ),
                "slide_min_directional_ratio": (
                    self.slide_min_directional_ratio
                ),
                "ornament_max_duration": (
                    self.ornament_max_duration
                ),
                "ornament_min_range_semitones": (
                    self.ornament_min_range_semitones
                ),
                "ornament_max_range_semitones": (
                    self.ornament_max_range_semitones
                ),
                "ornament_return_tolerance": (
                    self.ornament_return_tolerance
                ),

                "performance_aware": True,
                "contour_aware": True,
                "performance_classification": True,
                "probability_is_soft_gate": True,
                "performance_does_not_force_event_boundary": True,
            },

            "input": {
                "pitch_version": pitch_data.get(
                    "version"
                ),
                "frame_count": len(frames),
            },

            "melody": melody,
        }

    # ============================================================
    # File analysis
    # ============================================================

    def analyze_file(
        self,
        pitch_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:
        pitch_data = self.load_pitch(
            pitch_path
        )

        result = self.analyze(
            pitch_data
        )

        output = Path(
            output_path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                result,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return result