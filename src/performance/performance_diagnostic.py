"""
PhoenixVoiceEngine
Performance Diagnostic V1.0.1 — Boundary-Aware

Diagnostic-only layer for Performance Analysis V1.0.
It detects and classifies performance-analysis issues without correction.

V1.0.1 changes:
- Uses edge_tolerance for event-boundary overlap detection.
- Small boundary overlaps are reported as BOUNDARY_OVERLAP warnings.
- Larger overlaps remain REAL_EVENT_OVERLAP failures.
- Preserves original event timing and raw contour.
- Reads confidence/stability from source when required.
- Does not modify, merge, delete, or auto-correct source events.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


class PerformanceDiagnostic:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"

    # Patch-level diagnostic evolution.
    PATCH_VERSION = "1.0.1"

    DEFAULT_MIN_CONFIDENCE = 0.25
    DEFAULT_MIN_STABILITY = 0.25
    DEFAULT_MIN_CONTOUR_POINTS = 2
    DEFAULT_MAX_CONTOUR_GAP = 0.12
    DEFAULT_EDGE_TOLERANCE = 0.04
    DEFAULT_PITCH_RANGE_LIMIT = 12.0

    def __init__(
        self,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        min_stability: float = DEFAULT_MIN_STABILITY,
        min_contour_points: int = DEFAULT_MIN_CONTOUR_POINTS,
        max_contour_gap: float = DEFAULT_MAX_CONTOUR_GAP,
        edge_tolerance: float = DEFAULT_EDGE_TOLERANCE,
        pitch_range_limit: float = DEFAULT_PITCH_RANGE_LIMIT,
    ) -> None:
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1.")
        if not 0.0 <= min_stability <= 1.0:
            raise ValueError("min_stability must be between 0 and 1.")
        if min_contour_points < 1:
            raise ValueError("min_contour_points must be positive.")
        if max_contour_gap < 0:
            raise ValueError("max_contour_gap cannot be negative.")
        if edge_tolerance < 0:
            raise ValueError("edge_tolerance cannot be negative.")
        if pitch_range_limit <= 0:
            raise ValueError("pitch_range_limit must be positive.")

        self.min_confidence = float(min_confidence)
        self.min_stability = float(min_stability)
        self.min_contour_points = int(min_contour_points)
        self.max_contour_gap = float(max_contour_gap)
        self.edge_tolerance = float(edge_tolerance)
        self.pitch_range_limit = float(pitch_range_limit)

    # ============================================================
    # Generic helpers
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
    def _events(
        performance_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        performance = performance_data.get("performance", {})
        events = performance.get("events", [])

        if not isinstance(events, list):
            raise ValueError("Performance events must be a list.")

        return [
            x for x in events
            if isinstance(x, dict)
        ]

    @staticmethod
    def _pitch_frames(
        pitch_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        pitch = pitch_data.get("pitch", {})
        frames = pitch.get("frames", [])

        if not isinstance(frames, list):
            raise ValueError("Pitch frames must be a list.")

        return [
            x for x in frames
            if isinstance(x, dict)
        ]

    @staticmethod
    def _issue(
        severity: str,
        issue_type: str,
        message: str,
        position: Optional[int] = None,
        **details: Any,
    ) -> Dict[str, Any]:
        item: Dict[str, Any] = {
            "severity": severity,
            "type": issue_type,
            "message": message,
        }

        if position is not None:
            item["position"] = position

        item.update(details)
        return item

    # ============================================================
    # Contour inspection
    # ============================================================

    def _validate_contour(
        self,
        event: Dict[str, Any],
        position: int,
    ) -> Dict[str, Any]:
        contour = event.get("contour", [])

        if not isinstance(contour, list):
            contour = []

        valid = []
        invalid = []

        for point in contour:
            if not isinstance(point, dict):
                invalid.append(point)
                continue

            time = self._num(point.get("time"))
            midi = self._num(point.get("midi"))

            if time is None or midi is None:
                invalid.append(point)
                continue

            valid.append({
                "time": time,
                "midi": midi,
            })

        valid.sort(
            key=lambda x: x["time"]
        )

        gaps: List[float] = []

        for a, b in zip(valid, valid[1:]):
            gap = b["time"] - a["time"]

            if gap > self.max_contour_gap:
                gaps.append(gap)

        return {
            "source_count": len(contour),
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "valid_points": valid,
            "large_gaps": gaps,
        }

    # ============================================================
    # Single-event diagnostics
    # ============================================================

    def _diagnose_event(
        self,
        event: Dict[str, Any],
        position: int,
    ) -> Dict[str, Any]:
        start = self._num(
            event.get("start_time")
        )

        end = self._num(
            event.get("end_time")
        )

        duration = self._num(
            event.get("duration"),
            0.0,
        )

        # Performance Analysis V1.0 stores the authoritative
        # confidence/stability inside "source".
        # Top-level values remain supported for compatibility.
        source = event.get("source")

        if not isinstance(source, dict):
            source = {}

        confidence = self._num(
            event.get(
                "confidence",
                source.get("confidence"),
            )
        )

        stability = self._num(
            event.get(
                "stability",
                source.get("stability"),
            )
        )

        issues: List[Dict[str, Any]] = []
        classifications: List[str] = []

        # --------------------------------------------------------
        # Timing
        # --------------------------------------------------------

        if (
            start is None
            or end is None
            or end < start
        ):
            classifications.append(
                "INVALID_TIMING"
            )

            issues.append(
                self._issue(
                    "FAIL",
                    "INVALID_EVENT_TIMING",
                    "Performance event has invalid timing.",
                    position,
                    start_time=start,
                    end_time=end,
                )
            )

        elif (
            duration is not None
            and abs((end - start) - duration) > 0.02
        ):
            classifications.append(
                "TIMING_MISMATCH"
            )

            issues.append(
                self._issue(
                    "WARNING",
                    "TIMING_MISMATCH",
                    "Event duration does not closely match its start/end timing.",
                    position,
                    start_time=start,
                    end_time=end,
                    duration=duration,
                )
            )

        # --------------------------------------------------------
        # Confidence
        # --------------------------------------------------------

        if (
            confidence is None
            or not 0.0 <= confidence <= 1.0
        ):
            classifications.append(
                "INVALID_CONFIDENCE"
            )

            issues.append(
                self._issue(
                    "FAIL",
                    "INVALID_CONFIDENCE",
                    "Performance confidence is missing or outside [0, 1].",
                    position,
                    confidence=confidence,
                )
            )

        elif confidence < self.min_confidence:
            classifications.append(
                "LOW_CONFIDENCE"
            )

            issues.append(
                self._issue(
                    "WARNING",
                    "LOW_CONFIDENCE",
                    "Performance analysis confidence is below the diagnostic threshold.",
                    position,
                    confidence=confidence,
                    threshold=self.min_confidence,
                )
            )

        # --------------------------------------------------------
        # Stability
        # --------------------------------------------------------

        if (
            stability is not None
            and stability < self.min_stability
        ):
            classifications.append(
                "LOW_STABILITY"
            )

            issues.append(
                self._issue(
                    "WARNING",
                    "LOW_STABILITY",
                    "Performance contour stability is below the diagnostic threshold.",
                    position,
                    stability=stability,
                    threshold=self.min_stability,
                )
            )

        # --------------------------------------------------------
        # Contour
        # --------------------------------------------------------

        contour_info = self._validate_contour(
            event,
            position,
        )

        if (
            contour_info["source_count"]
            < self.min_contour_points
        ):
            classifications.append(
                "INSUFFICIENT_CONTOUR"
            )

            issues.append(
                self._issue(
                    "WARNING",
                    "INSUFFICIENT_CONTOUR",
                    "Performance event contains too few contour points.",
                    position,
                    contour_points=contour_info["source_count"],
                    minimum=self.min_contour_points,
                )
            )

        if contour_info["invalid_count"]:
            classifications.append(
                "INVALID_CONTOUR_POINT"
            )

            issues.append(
                self._issue(
                    "WARNING",
                    "INVALID_CONTOUR_POINT",
                    "One or more raw contour points could not be validated.",
                    position,
                    invalid_points=contour_info["invalid_count"],
                )
            )

        if contour_info["large_gaps"]:
            classifications.append(
                "CONTOUR_GAP"
            )

            issues.append(
                self._issue(
                    "WARNING",
                    "CONTOUR_GAP",
                    "Large time gap detected inside the raw performance contour.",
                    position,
                    largest_gap=round(
                        max(contour_info["large_gaps"]),
                        6,
                    ),
                    gap_count=len(
                        contour_info["large_gaps"]
                    ),
                )
            )

        # --------------------------------------------------------
        # Pitch range
        # --------------------------------------------------------

        pitch = event.get("pitch", {})

        if not isinstance(pitch, dict):
            pitch = {}

        pitch_range = self._num(
            pitch.get("range_semitones")
        )

        if (
            pitch_range is not None
            and pitch_range > self.pitch_range_limit
        ):
            classifications.append(
                "EXTREME_PITCH_RANGE"
            )

            issues.append(
                self._issue(
                    "WARNING",
                    "EXTREME_PITCH_RANGE",
                    "Performance pitch range is unusually large and should be reviewed.",
                    position,
                    range_semitones=pitch_range,
                    threshold=self.pitch_range_limit,
                )
            )

        # --------------------------------------------------------
        # Classification comparison
        # --------------------------------------------------------

        techniques = event.get(
            "techniques",
            {},
        )

        if not isinstance(
            techniques,
            dict,
        ):
            techniques = {}

        dominant = techniques.get(
            "dominant_type"
        )

        source_classifier = techniques.get(
            "source_classifier"
        )

        if (
            source_classifier
            and dominant
            and source_classifier != dominant
        ):
            classifications.append(
                "CLASSIFICATION_CONFLICT"
            )

            issues.append(
                self._issue(
                    "WARNING",
                    "CLASSIFICATION_CONFLICT",
                    "Independent performance classification differs from the source classifier.",
                    position,
                    source_classifier=source_classifier,
                    independent_classifier=dominant,
                )
            )

        if not classifications:
            classifications.append(
                "HEALTHY"
            )

        return {
            "event_index": event.get(
                "event_index",
                position,
            ),
            "position": position,
            "classification": classifications[0],
            "classifications": classifications,
            "timing": {
                "start_time": start,
                "end_time": end,
                "duration": duration,
            },
            "confidence": confidence,
            "stability": stability,
            "contour": {
                "source_count": contour_info[
                    "source_count"
                ],
                "valid_count": contour_info[
                    "valid_count"
                ],
                "invalid_count": contour_info[
                    "invalid_count"
                ],
                "large_gap_count": len(
                    contour_info["large_gaps"]
                ),
                "largest_gap": (
                    round(
                        max(
                            contour_info["large_gaps"]
                        ),
                        6,
                    )
                    if contour_info["large_gaps"]
                    else 0.0
                ),
            },
            "techniques": {
                "dominant_type": dominant,
                "source_classifier": source_classifier,
            },
            "issues": issues,
        }

    # ============================================================
    # Global diagnostics
    # ============================================================

    def analyze(
        self,
        pitch_data: Dict[str, Any],
        performance_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        frames = self._pitch_frames(
            pitch_data
        )

        events = self._events(
            performance_data
        )

        issues: List[
            Dict[str, Any]
        ] = []

        diagnostics: List[
            Dict[str, Any]
        ] = []

        # --------------------------------------------------------
        # Event order
        # --------------------------------------------------------

        expected_indices = list(
            range(
                1,
                len(events) + 1,
            )
        )

        actual_indices = [
            self._num(
                event.get("event_index")
            )
            for event in events
        ]

        if actual_indices != expected_indices:
            issues.append(
                self._issue(
                    "FAIL",
                    "EVENT_ORDER",
                    "Performance events are not sequentially ordered.",
                    actual_indices=actual_indices,
                    expected_indices=expected_indices,
                )
            )

        # --------------------------------------------------------
        # Boundary-aware event overlap
        # --------------------------------------------------------

        previous_end: Optional[
            float
        ] = None

        previous_position: Optional[
            int
        ] = None

        for position, event in enumerate(
            events,
            1,
        ):
            item = self._diagnose_event(
                event,
                position,
            )

            diagnostics.append(
                item
            )

            issues.extend(
                item["issues"]
            )

            start = self._num(
                event.get("start_time")
            )

            end = self._num(
                event.get("end_time")
            )

            if (
                start is not None
                and previous_end is not None
                and start < previous_end - 1e-6
            ):
                overlap = (
                    previous_end
                    - start
                )

                overlap = max(
                    0.0,
                    overlap,
                )

                # ------------------------------------------------
                # V1.0.1:
                # Small overlap near an event boundary is not
                # treated as a structural event failure.
                # ------------------------------------------------

                if (
                    overlap
                    <= self.edge_tolerance + 1e-6
                ):
                    item["classifications"].append(
                        "BOUNDARY_OVERLAP"
                    )

                    # Do not replace a more meaningful primary
                    # event classification. The boundary condition
                    # remains visible in classifications.
                    issues.append(
                        self._issue(
                            "WARNING",
                            "EVENT_OVERLAP",
                            "Small event-boundary overlap detected within the configured edge tolerance.",
                            position,
                            previous_position=previous_position,
                            previous_end=round(
                                previous_end,
                                6,
                            ),
                            start_time=round(
                                start,
                                6,
                            ),
                            overlap=round(
                                overlap,
                                6,
                            ),
                            overlap_kind="BOUNDARY",
                            tolerance=self.edge_tolerance,
                        )
                    )

                    item["issues"].append(
                        self._issue(
                            "WARNING",
                            "EVENT_OVERLAP",
                            "Small event-boundary overlap detected within the configured edge tolerance.",
                            position,
                            previous_position=previous_position,
                            previous_end=round(
                                previous_end,
                                6,
                            ),
                            start_time=round(
                                start,
                                6,
                            ),
                            overlap=round(
                                overlap,
                                6,
                            ),
                            overlap_kind="BOUNDARY",
                            tolerance=self.edge_tolerance,
                        )
                    )

                else:
                    item["classifications"].append(
                        "REAL_EVENT_OVERLAP"
                    )

                    issues.append(
                        self._issue(
                            "FAIL",
                            "EVENT_OVERLAP",
                            "Performance events overlap beyond the configured boundary tolerance.",
                            position,
                            previous_position=previous_position,
                            previous_end=round(
                                previous_end,
                                6,
                            ),
                            start_time=round(
                                start,
                                6,
                            ),
                            overlap=round(
                                overlap,
                                6,
                            ),
                            overlap_kind="REAL",
                            tolerance=self.edge_tolerance,
                        )
                    )

                    item["issues"].append(
                        self._issue(
                            "FAIL",
                            "EVENT_OVERLAP",
                            "Performance events overlap beyond the configured boundary tolerance.",
                            position,
                            previous_position=previous_position,
                            previous_end=round(
                                previous_end,
                                6,
                            ),
                            start_time=round(
                                start,
                                6,
                            ),
                            overlap=round(
                                overlap,
                                6,
                            ),
                            overlap_kind="REAL",
                            tolerance=self.edge_tolerance,
                        )
                    )

            if end is not None:
                previous_end = end
                previous_position = position

        # --------------------------------------------------------
        # Classification counts
        # --------------------------------------------------------

        counts: Dict[str, int] = {}

        for item in diagnostics:
            # Count the primary event classification exactly as
            # V1.0 did. Boundary/overlap diagnostics are available
            # in the classifications list and issue list.
            key = item["classification"]

            counts[key] = (
                counts.get(key, 0)
                + 1
            )

        # Additional global diagnostic counts.
        boundary_overlap_count = sum(
            1
            for issue in issues
            if (
                issue["type"] == "EVENT_OVERLAP"
                and issue.get("overlap_kind") == "BOUNDARY"
            )
        )

        real_overlap_count = sum(
            1
            for issue in issues
            if (
                issue["type"] == "EVENT_OVERLAP"
                and issue.get("overlap_kind") == "REAL"
            )
        )

        fail_count = sum(
            1
            for issue in issues
            if issue["severity"] == "FAIL"
        )

        warning_count = sum(
            1
            for issue in issues
            if issue["severity"] == "WARNING"
        )

        status = (
            "FAIL"
            if fail_count
            else (
                "WARNING"
                if warning_count
                else "PASS"
            )
        )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "status": status,
            "issue_count": len(issues),
            "fail_count": fail_count,
            "warning_count": warning_count,
            "classification_counts": counts,
            "issues": issues,
            "events": diagnostics,
            "analysis": {
                "min_confidence": self.min_confidence,
                "min_stability": self.min_stability,
                "min_contour_points": self.min_contour_points,
                "max_contour_gap": self.max_contour_gap,
                "edge_tolerance": self.edge_tolerance,
                "pitch_range_limit": self.pitch_range_limit,
                "boundary_aware": True,
                "boundary_overlap_count": boundary_overlap_count,
                "real_event_overlap_count": real_overlap_count,
                "no_auto_correction": True,
                "raw_contour_preserved": True,
                "timing_preserved": True,
            },
            "input": {
                "pitch_version": pitch_data.get(
                    "version"
                ),
                "performance_version": performance_data.get(
                    "version"
                ),
                "performance_feature_version": performance_data.get(
                    "feature_version"
                ),
                "pitch_frame_count": len(
                    frames
                ),
                "performance_event_count": len(
                    events
                ),
            },
        }

    def analyze_file(
        self,
        pitch_path: str | Path,
        performance_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:
        pitch_path = Path(
            pitch_path
        )

        performance_path = Path(
            performance_path
        )

        output_path = Path(
            output_path
        )

        with pitch_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            pitch_data = json.load(
                handle
            )

        with performance_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            performance_data = json.load(
                handle
            )

        result = self.analyze(
            pitch_data,
            performance_data,
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with output_path.open(
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