"""
PhoenixVoiceEngine
Maqam Evidence Analyzer V1.0.1

Evidence-only layer for maqam analysis.

V1.0.1 fixes a data-model issue discovered on the real Bender output:
the Phrase/Performance events do not reliably expose generic
`confidence` and `stability` fields at the top level.

Therefore stable-note evidence is derived from the actual performance
evidence when available:
    - pitch range
    - max pitch deviation
    - technique classification
    - duration

The analyzer never modifies source timing or pitch and never decides
maqam/jins/sayr.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class MaqamEvidenceAnalyzer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.1"

    def __init__(
        self,
        stable_max_range_semitones: float = 0.35,
        stable_max_deviation_semitones: float = 0.30,
        stable_min_duration: float = 0.10,
        cadence_window_events: int = 2,
    ) -> None:
        if stable_max_range_semitones < 0:
            raise ValueError("stable_max_range_semitones must be >= 0")
        if stable_max_deviation_semitones < 0:
            raise ValueError("stable_max_deviation_semitones must be >= 0")
        if stable_min_duration < 0:
            raise ValueError("stable_min_duration must be >= 0")
        if cadence_window_events <= 0:
            raise ValueError("cadence_window_events must be positive")

        self.stable_max_range_semitones = float(
            stable_max_range_semitones
        )
        self.stable_max_deviation_semitones = float(
            stable_max_deviation_semitones
        )
        self.stable_min_duration = float(stable_min_duration)
        self.cadence_window_events = int(cadence_window_events)

    @staticmethod
    def _num(
        value: Any,
        default: Optional[float] = None,
    ) -> Optional[float]:
        try:
            if value is None:
                return default
            value = float(value)
            return value if math.isfinite(value) else default
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
            json.dumps(value, ensure_ascii=False)
        )

    def _phrases(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        root = self._dict(data.get("phrases"))
        return [
            self._copy(item)
            for item in self._list(root.get("phrases"))
            if isinstance(item, dict)
        ]

    def _events_from_phrases(
        self,
        phrases: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for phrase in phrases:
            for event in self._list(phrase.get("events")):
                if isinstance(event, dict):
                    events.append(event)
        return events

    def _melody(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return self._dict(event.get("melody"))

    def _pitch(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return self._dict(event.get("pitch"))

    def _techniques(self, event: Dict[str, Any]) -> Dict[str, Any]:
        return self._dict(event.get("techniques"))

    def _event_midi(
        self,
        event: Dict[str, Any],
    ) -> Optional[float]:
        melody = self._melody(event)

        for key in ("midi_note", "midi_mean"):
            value = self._num(melody.get(key))
            if value is not None:
                return value

        for key in ("midi_note", "midi_mean"):
            value = self._num(event.get(key))
            if value is not None:
                return value

        pitch = self._pitch(event)
        for key in ("midi", "midi_mean", "mean_midi"):
            value = self._num(pitch.get(key))
            if value is not None:
                return value

        return None

    def _timing(
        self,
        event: Dict[str, Any],
    ) -> Tuple[float, float]:
        start = self._num(event.get("start_time"))
        end = self._num(event.get("end_time"))

        timing = self._dict(event.get("timing"))
        if start is None:
            start = self._num(timing.get("start_time"))
        if end is None:
            end = self._num(timing.get("end_time"))

        start = start if start is not None else 0.0
        end = end if end is not None else start

        return start, end

    def _duration(
        self,
        event: Dict[str, Any],
        start: float,
        end: float,
    ) -> float:
        value = self._num(event.get("duration"))
        if value is not None:
            return max(0.0, value)

        timing = self._dict(event.get("timing"))
        value = self._num(timing.get("duration"))
        if value is not None:
            return max(0.0, value)

        return max(0.0, end - start)

    @staticmethod
    def _pitch_class(midi: float) -> int:
        return int(round(midi)) % 12

    @staticmethod
    def _pc_name(pc: int) -> str:
        names = (
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B",
        )
        return names[int(pc) % 12]

    def _performance_stability(
        self,
        event: Dict[str, Any],
    ) -> Dict[str, Any]:
        pitch = self._pitch(event)
        techniques = self._techniques(event)

        range_semitones = self._num(
            pitch.get("range_semitones")
        )
        max_deviation = self._num(
            pitch.get("max_deviation_semitones")
        )
        dominant = str(
            techniques.get("dominant_type") or ""
        ).upper()

        movement_types = {
            "PITCH_BEND",
            "SLIDE",
            "ORNAMENT",
            "VIBRATO",
        }

        range_ok = (
            range_semitones is not None
            and range_semitones <= self.stable_max_range_semitones
        )
        deviation_ok = (
            max_deviation is not None
            and max_deviation <= self.stable_max_deviation_semitones
        )

        explicit_stable = (
            range_semitones is not None
            and max_deviation is not None
            and range_ok
            and deviation_ok
            and dominant not in movement_types
        )

        evidence_available = (
            range_semitones is not None
            or max_deviation is not None
            or bool(dominant)
        )

        return {
            "evidence_available": evidence_available,
            "range_semitones": (
                round(range_semitones, 6)
                if range_semitones is not None
                else None
            ),
            "max_deviation_semitones": (
                round(max_deviation, 6)
                if max_deviation is not None
                else None
            ),
            "dominant_type": dominant or None,
            "stable": bool(explicit_stable),
            "basis": (
                "PERFORMANCE_PITCH_EVIDENCE"
                if evidence_available
                else "INSUFFICIENT_PERFORMANCE_EVIDENCE"
            ),
        }

    def _event_evidence(
        self,
        events: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        output = []

        for event in events:
            midi = self._event_midi(event)
            start, end = self._timing(event)
            duration = self._duration(event, start, end)

            if midi is None:
                output.append({
                    "event_index": event.get("event_index"),
                    "midi": None,
                    "pitch_class": None,
                    "pitch_class_name": None,
                    "start_time": round(start, 6),
                    "end_time": round(end, 6),
                    "duration": round(duration, 6),
                    "stable": False,
                    "stability": {
                        "evidence_available": False,
                        "stable": False,
                        "basis": "NO_MIDI",
                    },
                })
                continue

            pc = self._pitch_class(midi)
            stability = self._performance_stability(event)

            stable = (
                stability["stable"]
                and duration >= self.stable_min_duration
            )

            output.append({
                "event_index": event.get("event_index"),
                "midi": round(midi, 6),
                "pitch_class": pc,
                "pitch_class_name": self._pc_name(pc),
                "start_time": round(start, 6),
                "end_time": round(end, 6),
                "duration": round(duration, 6),
                "stable": stable,
                "stability": {
                    **stability,
                    "stable": stable,
                },
            })

        return output

    def _pitch_class_distribution(
        self,
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        duration_by_pc = {
            str(pc): 0.0 for pc in range(12)
        }
        event_count_by_pc = {
            str(pc): 0 for pc in range(12)
        }

        for item in evidence:
            pc = item.get("pitch_class")
            if pc is None:
                continue

            key = str(int(pc))
            duration_by_pc[key] += float(
                item.get("duration", 0.0)
            )
            event_count_by_pc[key] += 1

        total = sum(duration_by_pc.values())

        normalized = {
            key: (
                round(value / total, 8)
                if total > 0
                else 0.0
            )
            for key, value in duration_by_pc.items()
        }

        return {
            "duration_by_pitch_class": {
                key: round(value, 6)
                for key, value in duration_by_pc.items()
            },
            "event_count_by_pitch_class": event_count_by_pc,
            "normalized_duration_distribution": normalized,
            "total_duration": round(total, 6),
        }

    def _stable_note_evidence(
        self,
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        duration_by_pc = {
            str(pc): 0.0 for pc in range(12)
        }
        count_by_pc = {
            str(pc): 0 for pc in range(12)
        }

        for item in evidence:
            if not item.get("stable"):
                continue

            pc = item.get("pitch_class")
            if pc is None:
                continue

            key = str(int(pc))
            duration_by_pc[key] += float(
                item.get("duration", 0.0)
            )
            count_by_pc[key] += 1

        ranked = sorted(
            (
                {
                    "pitch_class": int(key),
                    "pitch_class_name": self._pc_name(
                        int(key)
                    ),
                    "duration": round(duration, 6),
                    "event_count": count_by_pc[key],
                }
                for key, duration in duration_by_pc.items()
                if count_by_pc[key] > 0
            ),
            key=lambda item: (
                item["duration"],
                item["event_count"],
            ),
            reverse=True,
        )

        return {
            "stable_event_count": sum(
                count_by_pc.values()
            ),
            "duration_by_pitch_class": {
                key: round(value, 6)
                for key, value in duration_by_pc.items()
            },
            "ranked_pitch_classes": ranked,
        }

    def _phrase_endings(
        self,
        phrases: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        output = []

        for phrase in phrases:
            events = [
                event
                for event in self._list(phrase.get("events"))
                if isinstance(event, dict)
            ]
            if not events:
                continue

            window = events[-self.cadence_window_events:]
            candidates = []

            for event in window:
                midi = self._event_midi(event)
                if midi is None:
                    continue

                start, end = self._timing(event)
                candidates.append({
                    "event_index": event.get("event_index"),
                    "midi": round(midi, 6),
                    "pitch_class": self._pitch_class(midi),
                    "pitch_class_name": self._pc_name(
                        self._pitch_class(midi)
                    ),
                    "start_time": round(start, 6),
                    "end_time": round(end, 6),
                    "duration": round(
                        self._duration(event, start, end),
                        6,
                    ),
                })

            if candidates:
                output.append({
                    "phrase_index": phrase.get("phrase_index"),
                    "phrase_start_time": phrase.get(
                        "start_time"
                    ),
                    "phrase_end_time": phrase.get(
                        "end_time"
                    ),
                    "window": candidates,
                    "final_event": candidates[-1],
                })

        return output

    def _interval_evidence(
        self,
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        valid = [
            item for item in evidence
            if item.get("midi") is not None
        ]

        directed = []

        for previous, current in zip(
            valid,
            valid[1:],
        ):
            delta = (
                float(current["midi"])
                - float(previous["midi"])
            )

            directed.append({
                "from_event_index": previous.get(
                    "event_index"
                ),
                "to_event_index": current.get(
                    "event_index"
                ),
                "semitones": round(delta, 6),
                "absolute_semitones": round(
                    abs(delta),
                    6,
                ),
                "direction": (
                    "ASCENDING"
                    if delta > 0
                    else "DESCENDING"
                    if delta < 0
                    else "STABLE"
                ),
            })

        return {
            "count": len(directed),
            "directed_intervals": directed,
            "semitone_deltas": [
                item["semitones"]
                for item in directed
            ],
        }

    def _phrase_summaries(
        self,
        phrases: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        output = []

        for phrase in phrases:
            events = [
                event
                for event in self._list(phrase.get("events"))
                if isinstance(event, dict)
            ]
            evidence = self._event_evidence(events)

            valid = [
                item
                for item in evidence
                if item.get("midi") is not None
            ]

            output.append({
                "phrase_index": phrase.get("phrase_index"),
                "start_time": phrase.get("start_time"),
                "end_time": phrase.get("end_time"),
                "duration": phrase.get("duration"),
                "event_count": len(events),
                "valid_pitch_event_count": len(valid),
                "stable_event_count": sum(
                    1
                    for item in valid
                    if item.get("stable")
                ),
                "pitch_classes": sorted({
                    int(item["pitch_class"])
                    for item in valid
                    if item.get("pitch_class") is not None
                }),
                "stable_pitch_classes": sorted({
                    int(item["pitch_class"])
                    for item in valid
                    if (
                        item.get("stable")
                        and item.get("pitch_class") is not None
                    )
                }),
                "final_pitch_class": (
                    int(valid[-1]["pitch_class"])
                    if valid
                    else None
                ),
            })

        return output

    def analyze(
        self,
        phrase_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        phrases = self._phrases(phrase_data)
        events = self._events_from_phrases(phrases)
        evidence = self._event_evidence(events)

        stable_count = sum(
            1
            for item in evidence
            if item.get("stable")
        )
        stability_available_count = sum(
            1
            for item in evidence
            if item.get("stability", {}).get(
                "evidence_available"
            )
        )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,

            "input": {
                "phrase_version": phrase_data.get(
                    "version"
                ),
                "phrase_feature_version": phrase_data.get(
                    "feature_version"
                ),
                "phrase_patch_version": phrase_data.get(
                    "patch_version"
                ),
                "phrase_count": len(phrases),
                "event_count": len(events),
            },

            "analysis": {
                "stable_max_range_semitones": (
                    self.stable_max_range_semitones
                ),
                "stable_max_deviation_semitones": (
                    self.stable_max_deviation_semitones
                ),
                "stable_min_duration": (
                    self.stable_min_duration
                ),
                "cadence_window_events": (
                    self.cadence_window_events
                ),
                "stability_evidence_available_event_count": (
                    stability_available_count
                ),
                "stable_event_count": stable_count,

                "timing_preserved": True,
                "raw_pitch_preserved": True,
                "no_pitch_correction": True,
                "no_microtonal_quantization": True,
                "no_maqam_decision": True,
                "no_jins_decision": True,
                "no_sayr_decision": True,
            },

            "evidence": {
                "event_evidence": evidence,
                "pitch_class_distribution": (
                    self._pitch_class_distribution(
                        evidence
                    )
                ),
                "stable_note_evidence": (
                    self._stable_note_evidence(
                        evidence
                    )
                ),
                "phrase_endings": (
                    self._phrase_endings(phrases)
                ),
                "interval_evidence": (
                    self._interval_evidence(evidence)
                ),
                "phrase_summaries": (
                    self._phrase_summaries(phrases)
                ),
            },

            "decision": {
                "status": "EVIDENCE_ONLY",
                "maqam": None,
                "jins": None,
                "confidence": None,
            },
        }

    def analyze_file(
        self,
        phrase_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:
        phrase_path = Path(phrase_path)
        output_path = Path(output_path)

        with phrase_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        result = self.analyze(data)

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