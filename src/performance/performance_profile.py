"""
PhoenixVoiceEngine
Performance Profile V1.0

Aggregates the already-produced Pitch, Melody, Performance and
Performance Diagnostic representations into one immutable performance
profile.

This layer does NOT:
- modify pitch data
- modify melody timing
- modify performance contour
- correct overlaps
- smooth pitch
- infer maqam
- infer Arabic ornament names
- generate audio

It is a representation/aggregation layer only.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


class PerformanceProfile:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"

    def __init__(self) -> None:
        pass

    # ============================================================
    # Helpers
    # ============================================================

    @staticmethod
    def _num(
        value: Any,
        default: Optional[float] = None,
    ) -> Optional[float]:
        try:
            if value is None:
                return default
            number = float(value)
            if not math.isfinite(number):
                return default
            return number
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _dict(value: Any) -> Dict[str, Any]:
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _list(value: Any) -> List[Any]:
        return value if isinstance(value, list) else []

    @staticmethod
    def _round(value: Any, digits: int = 6) -> Any:
        number = PerformanceProfile._num(value)
        if number is None:
            return value
        return round(number, digits)

    @staticmethod
    def _copy(value: Any) -> Any:
        """
        JSON-safe deep copy. This intentionally keeps source values
        intact while preventing accidental mutation of source objects.
        """
        return json.loads(json.dumps(value, ensure_ascii=False))

    # ============================================================
    # Source indexing
    # ============================================================

    def _index_by_event(
        self,
        events: List[Dict[str, Any]],
    ) -> Dict[int, Dict[str, Any]]:
        indexed: Dict[int, Dict[str, Any]] = {}

        for position, event in enumerate(events, 1):
            if not isinstance(event, dict):
                continue

            raw_index = event.get(
                "event_index",
                position,
            )

            number = self._num(raw_index)

            if number is None:
                index = position
            else:
                index = int(number)

            indexed[index] = event

        return indexed

    # ============================================================
    # Technique profile
    # ============================================================

    def _technique_profile(
        self,
        performance_event: Dict[str, Any],
    ) -> Dict[str, Any]:
        techniques = self._dict(
            performance_event.get("techniques")
        )

        performance_block = self._dict(
            performance_event.get("performance")
        )

        source_classifier = (
            techniques.get("source_classifier")
        )

        independent_classifier = (
            techniques.get("dominant_type")
        )

        # The source classifier remains the primary classifier when
        # available. We never overwrite the source event.
        primary = (
            source_classifier
            or independent_classifier
            or "UNKNOWN"
        )

        secondary: List[str] = []

        if (
            independent_classifier
            and independent_classifier != primary
        ):
            secondary.append(
                str(independent_classifier)
            )

        # Preserve explicit technique detections from the
        # Performance Analyzer as secondary information.
        for key, label in (
            ("vibrato", "VIBRATO"),
            ("slide", "SLIDE"),
            ("ornament", "ORNAMENT"),
        ):
            block = performance_block.get(key)

            if isinstance(block, dict):
                detected = bool(
                    block.get("detected", False)
                )

                if detected and label != primary:
                    if label not in secondary:
                        secondary.append(label)

        pitch_bend = performance_event.get(
            "pitch_bend"
        )

        if isinstance(pitch_bend, dict):
            if bool(
                pitch_bend.get("detected", False)
            ):
                if (
                    "PITCH_BEND" != primary
                    and "PITCH_BEND" not in secondary
                ):
                    secondary.append("PITCH_BEND")

        # Do not invent a technique from an absent source field.
        return {
            "primary": primary,
            "secondary": secondary,
            "source_classifier": source_classifier,
            "independent_classifier": independent_classifier,
        }

    # ============================================================
    # Event profile
    # ============================================================

    def _event_profile(
        self,
        melody_event: Dict[str, Any],
        performance_event: Optional[Dict[str, Any]],
        diagnostic_event: Optional[Dict[str, Any]],
        position: int,
    ) -> Dict[str, Any]:

        melody_event = self._dict(melody_event)
        performance_event = self._dict(
            performance_event
        )
        diagnostic_event = self._dict(
            diagnostic_event
        )

        melody = {
            "event_index": melody_event.get(
                "event_index",
                position,
            ),
            "start_time": melody_event.get(
                "start_time"
            ),
            "end_time": melody_event.get(
                "end_time"
            ),
            "duration": melody_event.get(
                "duration"
            ),
            "midi_note": melody_event.get(
                "midi_note"
            ),
            "note_name": melody_event.get(
                "note_name"
            ),
            "midi_mean": melody_event.get(
                "midi_mean"
            ),
            "f0_mean_hz": melody_event.get(
                "f0_mean_hz"
            ),
            "confidence": melody_event.get(
                "confidence"
            ),
            "stability": melody_event.get(
                "stability"
            ),
        }

        pitch = self._dict(
            performance_event.get("pitch")
        )

        performance_melody = self._dict(
            performance_event.get("melody")
        )

        # Performance Analysis is the preferred source for detailed
        # performance measurements, while Melody remains the source
        # of the canonical melodic event.
        pitch_profile = {
            "min_midi": pitch.get("min_midi"),
            "max_midi": pitch.get("max_midi"),
            "range_semitones": pitch.get(
                "range_semitones"
            ),
            "mean_offset_semitones": pitch.get(
                "mean_offset_semitones"
            ),
            "max_deviation_semitones": pitch.get(
                "max_deviation_semitones"
            ),
            "direction": pitch.get("direction"),
            "slope_semitones_per_second": pitch.get(
                "slope_semitones_per_second"
            ),
            "directional_ratio": pitch.get(
                "directional_ratio"
            ),
        }

        timing = {
            "start_time": performance_event.get(
                "start_time",
                melody_event.get("start_time"),
            ),
            "end_time": performance_event.get(
                "end_time",
                melody_event.get("end_time"),
            ),
            "duration": performance_event.get(
                "duration",
                melody_event.get("duration"),
            ),
        }

        contour = self._copy(
            performance_event.get(
                "contour",
                melody_event.get(
                    "pitch_contour",
                    [],
                ),
            )
        )

        techniques = self._technique_profile(
            performance_event
        )

        diagnostic_classification = (
            diagnostic_event.get(
                "classification"
            )
        )

        diagnostic_classifications = self._copy(
            diagnostic_event.get(
                "classifications",
                [],
            )
        )

        diagnostic_issues = self._copy(
            diagnostic_event.get(
                "issues",
                [],
            )
        )

        return {
            "event_index": melody_event.get(
                "event_index",
                performance_event.get(
                    "event_index",
                    position,
                ),
            ),

            "melody": melody,

            "timing": timing,

            "pitch": pitch_profile,

            "performance": {
                "confidence": performance_event.get(
                    "confidence",
                    melody_event.get("confidence"),
                ),
                "stability": performance_event.get(
                    "stability",
                    melody_event.get("stability"),
                ),
                "techniques": techniques,
            },

            "contour": {
                "point_count": len(contour),
                "points": contour,
                "raw_preserved": True,
            },

            "diagnostic": {
                "classification": diagnostic_classification,
                "classifications": diagnostic_classifications,
                "issue_count": len(
                    diagnostic_issues
                ),
                "issues": diagnostic_issues,
            },

            # These are references/measurements already present in
            # Performance Analysis. No new musical inference occurs.
            "source_measurements": {
                "melody_midi": performance_melody.get(
                    "midi_note",
                    melody_event.get("midi_note"),
                ),
                "melody_note_name": performance_melody.get(
                    "note_name",
                    melody_event.get("note_name"),
                ),
                "midi_mean": performance_melody.get(
                    "midi_mean",
                    melody_event.get("midi_mean"),
                ),
                "f0_mean_hz": performance_melody.get(
                    "f0_mean_hz",
                    melody_event.get("f0_mean_hz"),
                ),
            },
        }

    # ============================================================
    # Global statistics
    # ============================================================

    def _global_statistics(
        self,
        events: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        count = len(events)

        durations: List[float] = []
        confidences: List[float] = []
        stabilities: List[float] = []
        pitch_ranges: List[float] = []
        deviations: List[float] = []

        technique_counts: Dict[str, int] = {}

        for event in events:
            timing = self._dict(
                event.get("timing")
            )

            performance = self._dict(
                event.get("performance")
            )

            pitch = self._dict(
                event.get("pitch")
            )

            duration = self._num(
                timing.get("duration")
            )
            confidence = self._num(
                performance.get("confidence")
            )
            stability = self._num(
                performance.get("stability")
            )
            pitch_range = self._num(
                pitch.get("range_semitones")
            )
            deviation = self._num(
                pitch.get("max_deviation_semitones")
            )

            if duration is not None:
                durations.append(duration)

            if confidence is not None:
                confidences.append(confidence)

            if stability is not None:
                stabilities.append(stability)

            if pitch_range is not None:
                pitch_ranges.append(pitch_range)

            if deviation is not None:
                deviations.append(deviation)

            techniques = self._dict(
                performance.get("techniques")
            )

            primary = techniques.get(
                "primary"
            )

            if primary:
                technique_counts[primary] = (
                    technique_counts.get(
                        primary,
                        0,
                    )
                    + 1
                )

            for secondary in self._list(
                techniques.get("secondary")
            ):
                key = str(secondary)

                technique_counts[key] = (
                    technique_counts.get(
                        key,
                        0,
                    )
                    + 1
                )

        def mean(values: List[float]) -> Optional[float]:
            if not values:
                return None
            return round(
                sum(values) / len(values),
                6,
            )

        return {
            "event_count": count,

            "duration": {
                "mean": mean(durations),
                "total": round(
                    sum(durations),
                    6,
                ),
                "min": (
                    round(min(durations), 6)
                    if durations
                    else None
                ),
                "max": (
                    round(max(durations), 6)
                    if durations
                    else None
                ),
            },

            "confidence": {
                "mean": mean(confidences),
                "count": len(confidences),
            },

            "stability": {
                "mean": mean(stabilities),
                "count": len(stabilities),
            },

            "pitch": {
                "mean_range_semitones": mean(
                    pitch_ranges
                ),
                "mean_max_deviation_semitones": mean(
                    deviations
                ),
            },

            "techniques": {
                "counts": technique_counts,
            },
        }

    # ============================================================
    # Main analysis
    # ============================================================

    def analyze(
        self,
        pitch_data: Dict[str, Any],
        melody_data: Dict[str, Any],
        performance_data: Dict[str, Any],
        diagnostic_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        melody_block = self._dict(
            melody_data.get("melody")
        )

        performance_block = self._dict(
            performance_data.get("performance")
        )

        diagnostic_events = self._list(
            diagnostic_data.get("events")
        )

        melody_events = [
            x for x in self._list(
                melody_block.get("events")
            )
            if isinstance(x, dict)
        ]

        performance_events = [
            x for x in self._list(
                performance_block.get("events")
            )
            if isinstance(x, dict)
        ]

        melody_index = self._index_by_event(
            melody_events
        )

        performance_index = self._index_by_event(
            performance_events
        )

        diagnostic_index = self._index_by_event(
            diagnostic_events
        )

        # Melody is the canonical event ordering.
        indices: List[int] = []

        for position, event in enumerate(
            melody_events,
            1,
        ):
            raw_index = event.get(
                "event_index",
                position,
            )

            number = self._num(
                raw_index
            )

            indices.append(
                int(number)
                if number is not None
                else position
            )

        profile_events: List[
            Dict[str, Any]
        ] = []

        for position, index in enumerate(
            indices,
            1,
        ):
            melody_event = melody_index.get(
                index,
                {},
            )

            performance_event = (
                performance_index.get(index)
            )

            diagnostic_event = (
                diagnostic_index.get(index)
            )

            profile_events.append(
                self._event_profile(
                    melody_event,
                    performance_event,
                    diagnostic_event,
                    position,
                )
            )

        statistics = self._global_statistics(
            profile_events
        )

        # Diagnostic summary is copied as a summary, not re-evaluated.
        diagnostic_summary = {
            "status": diagnostic_data.get(
                "status"
            ),
            "issue_count": diagnostic_data.get(
                "issue_count",
                0,
            ),
            "fail_count": diagnostic_data.get(
                "fail_count",
                0,
            ),
            "warning_count": diagnostic_data.get(
                "warning_count",
                0,
            ),
            "boundary_overlap_count": self._dict(
                diagnostic_data.get("analysis")
            ).get(
                "boundary_overlap_count",
                0,
            ),
            "real_event_overlap_count": self._dict(
                diagnostic_data.get("analysis")
            ).get(
                "real_event_overlap_count",
                0,
            ),
        }

        # Source versions are retained for traceability.
        source = {
            "pitch_version": pitch_data.get(
                "version"
            ),
            "melody_version": melody_data.get(
                "version"
            ),
            "melody_feature_version": melody_data.get(
                "feature_version"
            ),
            "performance_version": performance_data.get(
                "version"
            ),
            "performance_feature_version": performance_data.get(
                "feature_version"
            ),
            "diagnostic_version": diagnostic_data.get(
                "version"
            ),
            "diagnostic_feature_version": diagnostic_data.get(
                "feature_version"
            ),
            "diagnostic_patch_version": diagnostic_data.get(
                "patch_version"
            ),
        }

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,

            "profile": {
                "event_count": len(
                    profile_events
                ),
                "events": profile_events,
                "statistics": statistics,
                "diagnostic": diagnostic_summary,

                "capabilities": {
                    "raw_contour_preserved": True,
                    "timing_preserved": True,
                    "no_auto_correction": True,

                    # These are intentionally false in V1.0.
                    # They belong to future analysis layers.
                    "maqam_analyzed": False,
                    "arab_analyzed": False,
                    "phrase_analyzed": False,
                    "generation_ready": False,
                },
            },

            "source": source,

            "input": {
                "pitch_frame_count": len(
                    self._list(
                        self._dict(
                            pitch_data.get("pitch")
                        ).get("frames")
                    )
                ),
                "melody_event_count": len(
                    melody_events
                ),
                "performance_event_count": len(
                    performance_events
                ),
                "diagnostic_event_count": len(
                    diagnostic_events
                ),
            },
        }

    # ============================================================
    # File API
    # ============================================================

    def analyze_file(
        self,
        pitch_path: str | Path,
        melody_path: str | Path,
        performance_path: str | Path,
        diagnostic_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:

        paths = [
            Path(pitch_path),
            Path(melody_path),
            Path(performance_path),
            Path(diagnostic_path),
        ]

        data: List[Dict[str, Any]] = []

        for path in paths:
            with path.open(
                "r",
                encoding="utf-8",
            ) as handle:
                data.append(
                    json.load(handle)
                )

        result = self.analyze(
            data[0],
            data[1],
            data[2],
            data[3],
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
        ) as handle:
            json.dump(
                result,
                handle,
                ensure_ascii=False,
                indent=2,
            )

        return result