"""
PhoenixVoiceEngine
Jins & Cadence Evidence Analyzer V1.0.2

Evidence-only analysis layer.
Reads musical event notes from the actual Phrase Analyzer schema:
event["melody"]["midi_note"]

Important:
- No timing correction.
- No pitch correction.
- No maqam decision.
- Performance contour is not rewritten.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


PITCH_CLASS_NAMES = [
    "C", "C#", "D", "D#", "E", "F",
    "F#", "G", "G#", "A", "A#", "B",
]


class JinsCadenceEvidenceAnalyzer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.2"

    def __init__(self, cadence_window: int = 3) -> None:
        if cadence_window < 2:
            raise ValueError("cadence_window must be >= 2")
        self.cadence_window = int(cadence_window)

    @staticmethod
    def _pitch_class(midi: float) -> int:
        return int(round(float(midi))) % 12

    @staticmethod
    def _extract_midi(event: Dict[str, Any]) -> Optional[float]:
        """
        Read the canonical Phrase Analyzer field first.

        Current real schema:
            event["melody"]["midi_note"]

        Fallbacks are deliberately read-only compatibility paths.
        """
        melody = event.get("melody")
        if isinstance(melody, dict):
            value = melody.get("midi_note")
            if value is not None:
                return float(value)

            value = melody.get("midi_mean")
            if value is not None:
                return float(value)

            value = melody.get("midi")
            if value is not None:
                return float(value)

        value = event.get("midi_note")
        if value is not None:
            return float(value)

        value = event.get("midi")
        if value is not None:
            return float(value)

        return None

    @staticmethod
    def _extract_event_order(event: Dict[str, Any], fallback: int) -> int:
        value = event.get("event_index", fallback)
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    def _flatten_events(self, phrases_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        root = phrases_data.get("phrases", {})
        phrases = root.get("phrases", []) if isinstance(root, dict) else []

        records: List[Dict[str, Any]] = []
        fallback_index = 0

        for phrase in phrases:
            phrase_index = phrase.get("phrase_index")
            events = phrase.get("events", [])
            for event in events:
                fallback_index += 1
                midi = self._extract_midi(event)
                if midi is None:
                    continue

                records.append({
                    "event_index": self._extract_event_order(event, fallback_index),
                    "phrase_index": phrase_index,
                    "midi": midi,
                    "pitch_class": self._pitch_class(midi),
                    "start_time": self._extract_time(event, "start_time"),
                    "end_time": self._extract_time(event, "end_time"),
                })

        records.sort(key=lambda x: (x["event_index"], x["start_time"] or 0.0))
        return records

    @staticmethod
    def _extract_time(event: Dict[str, Any], name: str) -> Optional[float]:
        timing = event.get("timing")
        if isinstance(timing, dict) and timing.get(name) is not None:
            return float(timing[name])

        melody = event.get("melody")
        if isinstance(melody, dict) and melody.get(name) is not None:
            return float(melody[name])

        if event.get(name) is not None:
            return float(event[name])

        return None

    def _interval_evidence(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        interval_counts: Counter[str] = Counter()
        directed_counts: Counter[str] = Counter()

        for a, b in zip(events, events[1:]):
            delta = int(round(b["midi"] - a["midi"]))
            if delta == 0:
                continue

            distance = abs(delta)
            interval_counts[str(distance)] += 1
            direction = "ASCENDING" if delta > 0 else "DESCENDING"
            directed_counts[f"{direction}:{distance}"] += 1

        return {
            "transition_count": sum(interval_counts.values()),
            "interval_counts": dict(sorted(interval_counts.items(), key=lambda x: int(x[0]))),
            "directed_interval_counts": dict(directed_counts),
        }

    def _transition_evidence(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        pairs: Counter[tuple[int, int]] = Counter()

        for a, b in zip(events, events[1:]):
            if a["midi"] == b["midi"]:
                continue
            pairs[(a["pitch_class"], b["pitch_class"])] += 1

        ranked = []
        for (source, target), count in pairs.most_common():
            ranked.append({
                "source_pitch_class": source,
                "source_pitch_class_name": PITCH_CLASS_NAMES[source],
                "target_pitch_class": target,
                "target_pitch_class_name": PITCH_CLASS_NAMES[target],
                "count": count,
            })

        return {
            "transition_pair_count": sum(pairs.values()),
            "ranked_pairs": ranked,
        }

    def _cadence_evidence(self, phrases: List[Dict[str, Any]]) -> Dict[str, Any]:
        cadences: List[Dict[str, Any]] = []
        final_counts: Counter[str] = Counter()

        for phrase in phrases:
            events = phrase.get("events", [])
            usable = []
            for event in events:
                midi = self._extract_midi(event)
                if midi is not None:
                    usable.append((event, midi))

            if not usable:
                continue

            selected = usable[-self.cadence_window:]
            pitch_classes = [self._pitch_class(midi) for _, midi in selected]
            final_pc = pitch_classes[-1]
            final_counts[str(final_pc)] += 1

            motion = []
            for a, b in zip(pitch_classes, pitch_classes[1:]):
                delta = (b - a) % 12
                if delta == 0:
                    direction = "STATIONARY"
                elif delta <= 6:
                    direction = "ASCENDING"
                else:
                    direction = "DESCENDING"
                motion.append(direction)

            cadences.append({
                "phrase_index": phrase.get("phrase_index"),
                "window_pitch_classes": pitch_classes,
                "window_pitch_class_names": [PITCH_CLASS_NAMES[x] for x in pitch_classes],
                "final_pitch_class": final_pc,
                "final_pitch_class_name": PITCH_CLASS_NAMES[final_pc],
                "motion": motion,
            })

        return {
            "phrase_count": len(cadences),
            "cadences": cadences,
            "final_pitch_class_counts": dict(final_counts),
        }

    def analyze(self, phrases_data: Dict[str, Any]) -> Dict[str, Any]:
        root = phrases_data.get("phrases", {})
        phrases = root.get("phrases", []) if isinstance(root, dict) else []
        events = self._flatten_events(phrases_data)

        intervals = self._interval_evidence(events)
        transitions = self._transition_evidence(events)
        cadences = self._cadence_evidence(phrases)

        # Evidence-only contract: this module never decides maqam/jins.
        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "input": {
                "phrase_count": len(phrases),
                "event_count": len(events),
            },
            "evidence": {
                "intervals": intervals,
                "stable_transitions": transitions,
                "cadences": cadences,
            },
            "analysis": {
                "source_timing_preserved": True,
                "source_pitch_preserved": True,
                "no_auto_correction": True,
                "no_maqam_decision": True,
                "pitch_source": "melody.midi_note",
            },
            "decision": {
                "status": "EVIDENCE_ONLY",
                "maqam": None,
                "jins": None,
                "confidence": None,
            },
        }

    def analyze_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        result = self.analyze(data)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
