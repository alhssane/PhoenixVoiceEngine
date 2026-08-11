"""
PhoenixVoiceEngine
Musical Phrase Analyzer V1.0.1 — Boundary Aware

Patch over V1.0:
- Preserves source event timing exactly.
- Prevents artificial phrase splits while the next event overlaps
  the previous event in time.
- Allows a phrase to exceed max_phrase_duration when necessary to
  avoid cutting through an overlapping source event.
- Does not correct, clamp, shift, or rewrite source timing.
- Does not infer maqam, arab, or semantic ornamentation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


class MusicalPhraseAnalyzer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.1"

    DEFAULT_MAX_EVENT_GAP = 0.45
    DEFAULT_MAX_PHRASE_DURATION = 8.0
    DEFAULT_MAX_PITCH_JUMP = 7.0
    DEFAULT_MAX_SILENCE_GAP = 0.75
    DEFAULT_MIN_EVENTS = 2

    def __init__(
        self,
        max_event_gap: float = DEFAULT_MAX_EVENT_GAP,
        max_phrase_duration: float = DEFAULT_MAX_PHRASE_DURATION,
        max_pitch_jump: float = DEFAULT_MAX_PITCH_JUMP,
        max_silence_gap: float = DEFAULT_MAX_SILENCE_GAP,
        min_events: int = DEFAULT_MIN_EVENTS,
    ) -> None:
        if max_event_gap < 0:
            raise ValueError("max_event_gap cannot be negative.")
        if max_phrase_duration <= 0:
            raise ValueError(
                "max_phrase_duration must be positive."
            )
        if max_pitch_jump <= 0:
            raise ValueError(
                "max_pitch_jump must be positive."
            )
        if max_silence_gap < 0:
            raise ValueError(
                "max_silence_gap cannot be negative."
            )
        if min_events <= 0:
            raise ValueError(
                "min_events must be positive."
            )

        self.max_event_gap = float(max_event_gap)
        self.max_phrase_duration = float(
            max_phrase_duration
        )
        self.max_pitch_jump = float(max_pitch_jump)
        self.max_silence_gap = float(max_silence_gap)
        self.min_events = int(min_events)

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
    def _copy(value: Any) -> Any:
        return json.loads(
            json.dumps(
                value,
                ensure_ascii=False,
            )
        )

    def _validate_events(
        self,
        profile_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        profile = self._dict(
            profile_data.get("profile")
        )

        raw_events = self._list(
            profile.get("events")
        )

        events = [
            self._copy(event)
            for event in raw_events
            if isinstance(event, dict)
        ]

        # Traversal order only. Source event_index values and timing
        # remain untouched.
        events.sort(
            key=lambda event: (
                self._num(
                    self._dict(
                        event.get("timing")
                    ).get("start_time"),
                    float("inf"),
                ),
                int(
                    self._num(
                        event.get("event_index"),
                        0,
                    )
                    or 0
                ),
            )
        )

        return events

    def _boundary_evidence(
        self,
        previous: Dict[str, Any],
        current: Dict[str, Any],
        phrase_start: float,
    ) -> Dict[str, Any]:
        previous_timing = self._dict(
            previous.get("timing")
        )
        current_timing = self._dict(
            current.get("timing")
        )

        previous_end = self._num(
            previous_timing.get("end_time")
        )
        current_start = self._num(
            current_timing.get("start_time")
        )
        current_end = self._num(
            current_timing.get("end_time")
        )

        previous_melody = self._dict(
            previous.get("melody")
        )
        current_melody = self._dict(
            current.get("melody")
        )

        previous_midi = self._num(
            previous_melody.get("midi_note")
        )
        current_midi = self._num(
            current_melody.get("midi_note")
        )

        if (
            previous_end is None
            or current_start is None
        ):
            gap = None
            overlap = False
            overlap_duration = None
        else:
            raw_gap = current_start - previous_end
            gap = max(0.0, raw_gap)
            overlap = raw_gap < 0.0
            overlap_duration = (
                previous_end - current_start
                if overlap
                else 0.0
            )

        if (
            previous_midi is None
            or current_midi is None
        ):
            pitch_jump = None
        else:
            pitch_jump = abs(
                current_midi - previous_midi
            )

        phrase_duration = None
        if current_end is not None:
            phrase_duration = (
                current_end - phrase_start
            )

        reasons: List[str] = []

        if overlap:
            reasons.append("SOURCE_EVENT_OVERLAP")

        if (
            gap is not None
            and gap > self.max_event_gap
        ):
            reasons.append("EVENT_GAP")

        if (
            gap is not None
            and gap > self.max_silence_gap
        ):
            reasons.append("LONG_SILENCE")

        if (
            pitch_jump is not None
            and pitch_jump > self.max_pitch_jump
        ):
            reasons.append("LARGE_PITCH_JUMP")

        if (
            phrase_duration is not None
            and phrase_duration
            > self.max_phrase_duration
        ):
            reasons.append("MAX_PHRASE_DURATION")

        return {
            "gap": (
                round(gap, 6)
                if gap is not None
                else None
            ),
            "overlap": overlap,
            "overlap_duration": (
                round(overlap_duration, 6)
                if overlap_duration is not None
                else None
            ),
            "pitch_jump_semitones": (
                round(pitch_jump, 6)
                if pitch_jump is not None
                else None
            ),
            "phrase_duration": (
                round(phrase_duration, 6)
                if phrase_duration is not None
                else None
            ),
            "reasons": reasons,
        }

    def _should_split(
        self,
        evidence: Dict[str, Any],
    ) -> bool:
        # Critical V1.0.1 rule:
        # Never create a phrase boundary through an overlapping source
        # event. The original timing is authoritative.
        if evidence["overlap"]:
            return False

        gap = evidence["gap"]
        phrase_duration = evidence[
            "phrase_duration"
        ]

        if (
            gap is not None
            and gap > self.max_silence_gap
        ):
            return True

        if (
            gap is not None
            and gap > self.max_event_gap
        ):
            return True

        if (
            phrase_duration is not None
            and phrase_duration
            > self.max_phrase_duration
        ):
            return True

        return False

    def _build_phrases(
        self,
        events: List[Dict[str, Any]],
    ) -> List[List[Dict[str, Any]]]:
        if not events:
            return []

        phrases: List[List[Dict[str, Any]]] = []
        current: List[Dict[str, Any]] = [events[0]]

        phrase_start = self._num(
            self._dict(
                events[0].get("timing")
            ).get("start_time"),
            0.0,
        ) or 0.0

        for event in events[1:]:
            previous = current[-1]

            evidence = self._boundary_evidence(
                previous,
                event,
                phrase_start,
            )

            if self._should_split(evidence):
                phrases.append(current)
                current = [event]

                phrase_start = self._num(
                    self._dict(
                        event.get("timing")
                    ).get("start_time"),
                    phrase_start,
                ) or phrase_start
            else:
                current.append(event)

        if current:
            phrases.append(current)

        return phrases

    def _phrase_to_output(
        self,
        events: List[Dict[str, Any]],
        phrase_index: int,
    ) -> Dict[str, Any]:
        first_timing = self._dict(
            events[0].get("timing")
        )
        last_timing = self._dict(
            events[-1].get("timing")
        )

        start = self._num(
            first_timing.get("start_time"),
            0.0,
        ) or 0.0

        end = self._num(
            last_timing.get("end_time"),
            start,
        ) or start

        midi_values: List[float] = []
        directions: List[str] = []
        primary_techniques: List[str] = []

        for event in events:
            melody = self._dict(
                event.get("melody")
            )
            midi = self._num(
                melody.get("midi_note")
            )
            if midi is not None:
                midi_values.append(midi)

            pitch = self._dict(
                event.get("pitch")
            )
            direction = pitch.get("direction")
            if direction:
                directions.append(str(direction))

            performance = self._dict(
                event.get("performance")
            )
            techniques = self._dict(
                performance.get("techniques")
            )
            primary = techniques.get("primary")
            if primary:
                primary_techniques.append(
                    str(primary)
                )

        if midi_values:
            pitch_min = min(midi_values)
            pitch_max = max(midi_values)
            pitch_range = pitch_max - pitch_min
        else:
            pitch_min = None
            pitch_max = None
            pitch_range = None

        if not directions:
            direction = "UNKNOWN"
        elif all(
            item == directions[0]
            for item in directions
        ):
            direction = directions[0]
        elif (
            "ASCENDING" in directions
            and "DESCENDING" not in directions
        ):
            direction = "ASCENDING"
        elif (
            "DESCENDING" in directions
            and "ASCENDING" not in directions
        ):
            direction = "DESCENDING"
        else:
            direction = "MIXED"

        technique_counts: Dict[str, int] = {}
        for technique in primary_techniques:
            technique_counts[technique] = (
                technique_counts.get(
                    technique,
                    0,
                )
                + 1
            )

        return {
            "phrase_index": phrase_index,
            "start_time": round(start, 6),
            "end_time": round(end, 6),
            "duration": round(
                max(0.0, end - start),
                6,
            ),
            "event_count": len(events),

            "events": [
                self._copy(event)
                for event in events
            ],

            "structure": {
                "midi_min": (
                    round(pitch_min, 6)
                    if pitch_min is not None
                    else None
                ),
                "midi_max": (
                    round(pitch_max, 6)
                    if pitch_max is not None
                    else None
                ),
                "pitch_range_semitones": (
                    round(pitch_range, 6)
                    if pitch_range is not None
                    else None
                ),
                "direction": direction,
                "technique_counts": technique_counts,
            },

            "analysis_status": {
                "phrase_detected": True,
                "maqam_analyzed": False,
                "arab_analyzed": False,
                "ornament_semantics_analyzed": False,
                "timing_preserved": True,
                "source_events_preserved": True,
                "no_auto_correction": True,
            },
        }

    def analyze(
        self,
        profile_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        events = self._validate_events(
            profile_data
        )

        raw_phrases = self._build_phrases(
            events
        )

        phrases = [
            self._phrase_to_output(
                phrase,
                index,
            )
            for index, phrase in enumerate(
                raw_phrases,
                1,
            )
        ]

        timeline_duration = 0.0
        if events:
            last_timing = self._dict(
                events[-1].get("timing")
            )
            timeline_duration = (
                self._num(
                    last_timing.get("end_time"),
                    0.0,
                )
                or 0.0
            )

        overlap_event_count = 0
        for previous, current in zip(
            events,
            events[1:],
        ):
            previous_end = self._num(
                self._dict(
                    previous.get("timing")
                ).get("end_time")
            )
            current_start = self._num(
                self._dict(
                    current.get("timing")
                ).get("start_time")
            )

            if (
                previous_end is not None
                and current_start is not None
                and current_start < previous_end
            ):
                overlap_event_count += 1

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,

            "input": {
                "profile_version": profile_data.get(
                    "version"
                ),
                "profile_feature_version": profile_data.get(
                    "feature_version"
                ),
                "profile_event_count": len(events),
            },

            "analysis": {
                "max_event_gap": self.max_event_gap,
                "max_phrase_duration": self.max_phrase_duration,
                "max_pitch_jump": self.max_pitch_jump,
                "max_silence_gap": self.max_silence_gap,
                "min_events": self.min_events,

                "boundary_overlap_protection": True,
                "source_overlap_event_count": (
                    overlap_event_count
                ),

                "timing_preserved": True,
                "source_events_preserved": True,
                "raw_contour_preserved": True,
                "no_auto_correction": True,

                "maqam_analysis": False,
                "arab_analysis": False,
                "ornament_semantics_analysis": False,
            },

            "phrases": {
                "phrase_count": len(phrases),
                "event_count": len(events),
                "duration": round(
                    timeline_duration,
                    6,
                ),
                "phrases": phrases,
            },
        }

    def analyze_file(
        self,
        profile_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:
        profile_path = Path(profile_path)
        output_path = Path(output_path)

        with profile_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            profile_data = json.load(handle)

        result = self.analyze(
            profile_data
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