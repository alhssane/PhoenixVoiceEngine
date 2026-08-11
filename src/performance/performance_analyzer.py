from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional


class PerformanceAnalyzer:
    """
    PhoenixVoiceEngine
    Performance Analysis V1.0

    Reads:
        - pitch analysis JSON
        - contour-aware melody JSON

    Produces a descriptive performance layer without modifying audio,
    lyrics, melody timing, or source pitch data.

    Design principles:
        1. Raw contour is preserved.
        2. Stable melody identity is preserved.
        3. Performance labels are descriptive, not corrective.
        4. Timing is preserved exactly.
        5. Pitch movement is analyzed inside existing melody events.
    """

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"

    DEFAULT_MIN_CONFIDENCE = 0.0
    DEFAULT_NEAR_NOTE_TOLERANCE = 0.35
    DEFAULT_STRONG_MOVEMENT = 0.75
    DEFAULT_SHORT_GESTURE_DURATION = 0.45
    DEFAULT_MAX_ORNAMENT_RANGE = 3.5
    DEFAULT_MIN_ORNAMENT_RANGE = 0.50
    DEFAULT_RETURN_TOLERANCE = 0.45
    DEFAULT_VIBRATO_MIN_DEPTH = 0.15
    DEFAULT_VIBRATO_MAX_DEPTH = 1.50
    DEFAULT_VIBRATO_MIN_CYCLES = 1.5
    DEFAULT_SLIDE_MIN_RANGE = 0.75
    DEFAULT_SLIDE_DIRECTIONAL_RATIO = 0.65
    DEFAULT_ATTACK_WINDOW = 0.20
    DEFAULT_RELEASE_WINDOW = 0.20

    def __init__(
        self,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        near_note_tolerance: float = DEFAULT_NEAR_NOTE_TOLERANCE,
        strong_movement_semitones: float = DEFAULT_STRONG_MOVEMENT,
        short_gesture_duration: float = DEFAULT_SHORT_GESTURE_DURATION,
        max_ornament_range: float = DEFAULT_MAX_ORNAMENT_RANGE,
        min_ornament_range: float = DEFAULT_MIN_ORNAMENT_RANGE,
        return_tolerance: float = DEFAULT_RETURN_TOLERANCE,
        vibrato_min_depth: float = DEFAULT_VIBRATO_MIN_DEPTH,
        vibrato_max_depth: float = DEFAULT_VIBRATO_MAX_DEPTH,
        vibrato_min_cycles: float = DEFAULT_VIBRATO_MIN_CYCLES,
        slide_min_range: float = DEFAULT_SLIDE_MIN_RANGE,
        slide_directional_ratio: float = DEFAULT_SLIDE_DIRECTIONAL_RATIO,
        attack_window: float = DEFAULT_ATTACK_WINDOW,
        release_window: float = DEFAULT_RELEASE_WINDOW,
    ) -> None:
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1.")
        positive = {
            "near_note_tolerance": near_note_tolerance,
            "strong_movement_semitones": strong_movement_semitones,
            "short_gesture_duration": short_gesture_duration,
            "max_ornament_range": max_ornament_range,
            "min_ornament_range": min_ornament_range,
            "return_tolerance": return_tolerance,
            "vibrato_min_depth": vibrato_min_depth,
            "vibrato_max_depth": vibrato_max_depth,
            "vibrato_min_cycles": vibrato_min_cycles,
            "slide_min_range": slide_min_range,
            "slide_directional_ratio": slide_directional_ratio,
            "attack_window": attack_window,
            "release_window": release_window,
        }
        for name, value in positive.items():
            if float(value) <= 0:
                raise ValueError(f"{name} must be positive.")
        if max_ornament_range < min_ornament_range:
            raise ValueError("max_ornament_range must be >= min_ornament_range.")
        if vibrato_max_depth < vibrato_min_depth:
            raise ValueError("vibrato_max_depth must be >= vibrato_min_depth.")
        if slide_directional_ratio > 1:
            raise ValueError("slide_directional_ratio must be <= 1.")

        self.min_confidence = float(min_confidence)
        self.near_note_tolerance = float(near_note_tolerance)
        self.strong_movement_semitones = float(strong_movement_semitones)
        self.short_gesture_duration = float(short_gesture_duration)
        self.max_ornament_range = float(max_ornament_range)
        self.min_ornament_range = float(min_ornament_range)
        self.return_tolerance = float(return_tolerance)
        self.vibrato_min_depth = float(vibrato_min_depth)
        self.vibrato_max_depth = float(vibrato_max_depth)
        self.vibrato_min_cycles = float(vibrato_min_cycles)
        self.slide_min_range = float(slide_min_range)
        self.slide_directional_ratio = float(slide_directional_ratio)
        self.attack_window = float(attack_window)
        self.release_window = float(release_window)

    # ------------------------------------------------------------
    # Loading / validation
    # ------------------------------------------------------------

    @staticmethod
    def _load_json(path: str | Path) -> Dict[str, Any]:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("Input JSON must contain an object.")
        return data

    def _validate_melody(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        melody = data.get("melody")
        if not isinstance(melody, dict):
            raise ValueError("Melody data must contain a melody object.")
        events = melody.get("events")
        if not isinstance(events, list):
            raise ValueError("Melody data must contain an events list.")

        previous = -float("inf")
        validated: List[Dict[str, Any]] = []

        for event in events:
            if not isinstance(event, dict):
                raise ValueError("Melody events must be objects.")

            start = self._num(event.get("start_time"), None)
            end = self._num(event.get("end_time"), None)
            duration = self._num(event.get("duration"), None)

            if start is None or end is None or duration is None:
                raise ValueError("Every melody event needs timing.")
            if end < start or duration <= 0:
                raise ValueError("Invalid melody event timing.")
            if start < previous:
                raise ValueError("Melody events must be chronologically ordered.")

            previous = start
            validated.append(event)

        return validated

    def _validate_pitch(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        pitch = data.get("pitch")
        if not isinstance(pitch, dict):
            raise ValueError("Pitch data must contain a pitch object.")
        frames = pitch.get("frames")
        if not isinstance(frames, list):
            raise ValueError("Pitch data must contain a frames list.")
        return [f for f in frames if isinstance(f, dict)]

    # ------------------------------------------------------------
    # Numeric helpers
    # ------------------------------------------------------------

    @staticmethod
    def _num(value: Any, default: Optional[float] = 0.0) -> Optional[float]:
        try:
            result = float(value)
            if not math.isfinite(result):
                return default
            return result
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _mean(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def _direction(values: List[float]) -> str:
        if len(values) < 2:
            return "STABLE"
        delta = values[-1] - values[0]
        if delta > 0.35:
            return "ASCENDING"
        if delta < -0.35:
            return "DESCENDING"
        return "STABLE"

    @staticmethod
    def _directional_ratio(values: List[float]) -> float:
        if len(values) < 3:
            return 0.0
        deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        total = sum(abs(x) for x in deltas)
        if total <= 1e-12:
            return 0.0
        return abs(values[-1] - values[0]) / total

    @staticmethod
    def _slope(times: List[float], values: List[float]) -> float:
        if len(times) < 2:
            return 0.0
        mt = sum(times) / len(times)
        mv = sum(values) / len(values)
        denominator = sum((t - mt) ** 2 for t in times)
        if denominator <= 1e-12:
            return 0.0
        numerator = sum((t - mt) * (v - mv) for t, v in zip(times, values))
        return numerator / denominator

    # ------------------------------------------------------------
    # Contour extraction
    # ------------------------------------------------------------

    def _event_contour(
        self,
        event: Dict[str, Any],
        pitch_frames: List[Dict[str, Any]],
    ) -> List[Dict[str, float]]:
        start = float(event["start_time"])
        end = float(event["end_time"])
        melody_midi = self._num(
            event.get("midi_note"),
            self._num(event.get("midi_mean"), 0.0),
        ) or 0.0

        contour = event.get("pitch_contour")
        if isinstance(contour, list) and contour:
            result = []
            for point in contour:
                if not isinstance(point, dict):
                    continue
                time = self._num(point.get("time"), None)
                midi = self._num(point.get("midi"), None)
                f0 = self._num(point.get("f0_hz"), None)
                if time is None or midi is None:
                    continue
                if start - 1e-6 <= time <= end + 1e-6:
                    result.append({
                        "time": time,
                        "midi": midi,
                        "f0_hz": f0 if f0 is not None else 0.0,
                        "offset": midi - melody_midi,
                    })
            if result:
                return result

        # Fallback: recover contour from pitch frames.
        result = []
        for frame in pitch_frames:
            time = self._num(frame.get("time"), None)
            f0 = self._num(frame.get("f0_hz"), None)
            midi = self._num(frame.get("midi"), None)

            if time is None or not (start - 1e-6 <= time <= end + 1e-6):
                continue
            if midi is None and f0 is not None and f0 > 0:
                midi = 69.0 + 12.0 * math.log2(f0 / 440.0)
            if midi is None:
                continue

            result.append({
                "time": time,
                "midi": midi,
                "f0_hz": f0 or 0.0,
                "offset": midi - melody_midi,
            })

        return result

    # ------------------------------------------------------------
    # Technique detectors
    # ------------------------------------------------------------

    def _vibrato(
        self,
        values: List[float],
        times: List[float],
    ) -> Dict[str, Any]:
        if len(values) < 8:
            return {"detected": False, "cycles": 0.0, "depth_semitones": 0.0}

        center = float(median(values))
        centered = [v - center for v in values]
        depth = (max(centered) - min(centered)) / 2.0

        crossings = 0
        last = 0
        for value in centered:
            sign = 1 if value > 0 else -1 if value < 0 else last
            if last and sign != last:
                crossings += 1
            last = sign

        cycles = crossings / 2.0
        duration = max(0.0, times[-1] - times[0]) if len(times) > 1 else 0.0

        detected = (
            self.vibrato_min_depth <= depth <= self.vibrato_max_depth
            and cycles >= self.vibrato_min_cycles
            and duration >= 0.20
        )

        return {
            "detected": bool(detected),
            "cycles": round(cycles, 3),
            "depth_semitones": round(depth, 4),
        }

    def _slide(
        self,
        values: List[float],
        times: List[float],
    ) -> Dict[str, Any]:
        if len(values) < 3:
            return {
                "detected": False,
                "direction": "NONE",
                "range_semitones": 0.0,
                "directional_ratio": 0.0,
            }

        value_range = max(values) - min(values)
        ratio = self._directional_ratio(values)
        slope = self._slope(times, values)
        direction = self._direction(values)

        detected = (
            value_range >= self.slide_min_range
            and ratio >= self.slide_directional_ratio
            and abs(slope) >= 0.40
        )

        return {
            "detected": bool(detected),
            "direction": direction if detected else "NONE",
            "range_semitones": round(value_range, 4),
            "directional_ratio": round(ratio, 4),
            "slope_semitones_per_second": round(slope, 5),
        }

    def _ornament(
        self,
        values: List[float],
        melody_midi: float,
        duration: float,
    ) -> Dict[str, Any]:
        if len(values) < 3:
            return {"detected": False, "type": "NONE", "range_semitones": 0.0}

        value_range = max(values) - min(values)

        if not (
            self.min_ornament_range
            <= value_range
            <= self.max_ornament_range
            and duration <= self.short_gesture_duration
        ):
            return {
                "detected": False,
                "type": "NONE",
                "range_semitones": round(value_range, 4),
            }

        start_ok = abs(values[0] - melody_midi) <= self.return_tolerance
        end_ok = abs(values[-1] - melody_midi) <= self.return_tolerance

        middle = values[1:-1]
        middle_peak = max(
            (abs(v - melody_midi) for v in middle),
            default=0.0,
        )

        if not (start_ok and end_ok and middle_peak >= self.min_ornament_range):
            return {
                "detected": False,
                "type": "NONE",
                "range_semitones": round(value_range, 4),
            }

        middle_mean = self._mean(middle)
        kind = "UPPER_NEIGHBOR" if middle_mean > melody_midi else "LOWER_NEIGHBOR"

        return {
            "detected": True,
            "type": kind,
            "range_semitones": round(value_range, 4),
        }

    # ------------------------------------------------------------
    # Attack / release / summary
    # ------------------------------------------------------------

    def _attack_release(
        self,
        contour: List[Dict[str, float]],
        melody_midi: float,
        start: float,
        end: float,
    ) -> Dict[str, Any]:
        if not contour:
            return {
                "attack": {"direction": "UNKNOWN", "delta_semitones": 0.0},
                "release": {"direction": "UNKNOWN", "delta_semitones": 0.0},
            }

        attack_points = [
            p for p in contour
            if p["time"] <= min(end, start + self.attack_window)
        ]
        release_points = [
            p for p in contour
            if p["time"] >= max(start, end - self.release_window)
        ]

        if len(attack_points) < 2:
            attack_delta = contour[0]["midi"] - melody_midi
        else:
            attack_delta = attack_points[-1]["midi"] - attack_points[0]["midi"]

        if len(release_points) < 2:
            release_delta = contour[-1]["midi"] - melody_midi
        else:
            release_delta = release_points[-1]["midi"] - release_points[0]["midi"]

        return {
            "attack": {
                "direction": self._direction(
                    [p["midi"] for p in attack_points]
                ),
                "delta_semitones": round(attack_delta, 4),
            },
            "release": {
                "direction": self._direction(
                    [p["midi"] for p in release_points]
                ),
                "delta_semitones": round(release_delta, 4),
            },
        }

    def analyze_event(
        self,
        event: Dict[str, Any],
        contour: List[Dict[str, float]],
    ) -> Dict[str, Any]:
        start = float(event["start_time"])
        end = float(event["end_time"])
        duration = float(event["duration"])
        melody_midi = self._num(
            event.get("midi_note"),
            self._num(event.get("midi_mean"), 0.0),
        ) or 0.0

        values = [p["midi"] for p in contour]
        times = [p["time"] for p in contour]
        offsets = [p["offset"] for p in contour]

        if values:
            pitch_min = min(values)
            pitch_max = max(values)
            pitch_range = pitch_max - pitch_min
            mean_offset = self._mean(offsets)
            max_deviation = max(abs(x) for x in offsets)
            direction = self._direction(values)
            slope = self._slope(times, values)
            directional_ratio = self._directional_ratio(values)
        else:
            pitch_min = pitch_max = melody_midi
            pitch_range = 0.0
            mean_offset = 0.0
            max_deviation = 0.0
            direction = "UNKNOWN"
            slope = 0.0
            directional_ratio = 0.0

        vibrato = self._vibrato(values, times)
        slide = self._slide(values, times)
        ornament = self._ornament(
            values,
            melody_midi,
            duration,
        )

        # Respect the classifier already produced by V1.2.1 when available,
        # but retain independent measurements in this layer.
        source_performance = event.get("performance")
        source_type = None
        if isinstance(source_performance, dict):
            source_type = source_performance.get("primary_type")

        if vibrato["detected"]:
            dominant = "VIBRATO"
        elif slide["detected"]:
            dominant = "SLIDE"
        elif ornament["detected"]:
            dominant = "ORNAMENT"
        elif pitch_range >= self.strong_movement_semitones:
            dominant = "PITCH_BEND"
        else:
            dominant = "NATURAL_VARIATION"

        return {
            "event_index": event.get("event_index"),
            "start_time": start,
            "end_time": end,
            "duration": duration,

            "melody": {
                "midi_note": event.get("midi_note"),
                "note_name": event.get("note_name"),
                "midi_mean": event.get("midi_mean"),
                "f0_mean_hz": event.get("f0_mean_hz"),
            },

            "pitch": {
                "min_midi": round(pitch_min, 4),
                "max_midi": round(pitch_max, 4),
                "range_semitones": round(pitch_range, 4),
                "mean_offset_semitones": round(mean_offset, 4),
                "max_deviation_semitones": round(max_deviation, 4),
                "direction": direction,
                "slope_semitones_per_second": round(slope, 5),
                "directional_ratio": round(directional_ratio, 5),
            },

            "techniques": {
                "dominant_type": dominant,
                "source_classifier": source_type,
                "vibrato": vibrato,
                "slide": slide,
                "ornament": ornament,
                "pitch_bend": {
                    "detected": (
                        pitch_range >= self.strong_movement_semitones
                        and not vibrato["detected"]
                        and not slide["detected"]
                        and not ornament["detected"]
                    ),
                    "range_semitones": round(pitch_range, 4),
                },
            },

            "attack_release": self._attack_release(
                contour,
                melody_midi,
                start,
                end,
            ),

            "contour": contour,
            "source": {
                "confidence": event.get("confidence"),
                "stability": event.get("stability"),
                "frame_count": event.get("frame_count"),
            },
        }

    def analyze(
        self,
        pitch_data: Dict[str, Any],
        melody_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        events = self._validate_melody(melody_data)
        frames = self._validate_pitch(pitch_data)

        analyses = []

        # Performance Analysis owns its own sequential event numbering.
        # The original melody event is never modified.
        for sequence_index, event in enumerate(events, 1):
            event_for_analysis = dict(event)
            event_for_analysis["event_index"] = sequence_index

            contour = self._event_contour(
                event_for_analysis,
                frames,
            )

            analyses.append(
                self.analyze_event(
                    event_for_analysis,
                    contour,
                )
            )

        counts: Dict[str, int] = {}
        for item in analyses:
            kind = item["techniques"]["dominant_type"]
            counts[kind] = counts.get(kind, 0) + 1

        duration = 0.0
        if events:
            duration = max(
                float(event["end_time"])
                for event in events
            )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,

            "analysis": {
                "min_confidence": self.min_confidence,
                "near_note_tolerance": self.near_note_tolerance,
                "strong_movement_semitones": self.strong_movement_semitones,
                "short_gesture_duration": self.short_gesture_duration,
                "max_ornament_range": self.max_ornament_range,
                "min_ornament_range": self.min_ornament_range,
                "return_tolerance": self.return_tolerance,
                "vibrato_min_depth": self.vibrato_min_depth,
                "vibrato_max_depth": self.vibrato_max_depth,
                "vibrato_min_cycles": self.vibrato_min_cycles,
                "slide_min_range": self.slide_min_range,
                "slide_directional_ratio": self.slide_directional_ratio,
                "attack_window": self.attack_window,
                "release_window": self.release_window,
                "no_auto_correction": True,
                "raw_contour_preserved": True,
                "timing_preserved": True,
            },

            "input": {
                "pitch_version": pitch_data.get("version"),
                "melody_version": melody_data.get("version"),
                "melody_feature_version": melody_data.get("feature_version"),
                "pitch_frame_count": len(frames),
                "melody_event_count": len(events),
            },

            "performance": {
                "duration": round(duration, 6),
                "event_count": len(analyses),
                "classification_counts": counts,
                "events": analyses,
            },
        }

    def analyze_file(
        self,
        pitch_path: str | Path,
        melody_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:
        pitch_data = self._load_json(pitch_path)
        melody_data = self._load_json(melody_path)
        result = self.analyze(pitch_data, melody_data)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(result, fh, ensure_ascii=False, indent=2)

        return result