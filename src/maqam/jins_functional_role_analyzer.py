"""
PhoenixVoiceEngine
Jins Functional Role Analyzer V1.0

Evidence-only analysis of functional pitch roles inside musical phrases.

It does not:
- modify pitch
- modify timing
- correct source performance
- decide maqam/jins
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


class JinsFunctionalRoleAnalyzer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.1"

    def _load(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _pc_name(pc: int) -> str:
        return (
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B"
        )[pc % 12]

    def _phrase_events(self, phrase_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        phrases = phrase_data.get("phrases", {}).get("phrases", [])
        return phrases

    def _event_pc(self, event: Dict[str, Any]) -> Optional[int]:
        # PhoenixVoiceEngine real event schema:
        # event["melody"]["midi_note"]
        melody = event.get("melody")
        if isinstance(melody, dict):
            value = melody.get("pitch_class")
            if isinstance(value, (int, float)):
                return int(value) % 12

            value = melody.get("midi_note")
            if isinstance(value, (int, float)):
                return int(round(float(value))) % 12

            value = melody.get("midi")
            if isinstance(value, (int, float)):
                return int(round(float(value))) % 12

        # Backward-compatible flat schemas.
        for key in ("pitch_class", "midi_note", "midi"):
            value = event.get(key)
            if isinstance(value, (int, float)):
                if key == "pitch_class":
                    return int(value) % 12
                return int(round(float(value))) % 12

        # Some older schemas nest the note.
        note = event.get("note")
        if isinstance(note, dict):
            for key in ("pitch_class", "midi_note", "midi"):
                value = note.get(key)
                if isinstance(value, (int, float)):
                    if key == "pitch_class":
                        return int(value) % 12
                    return int(round(float(value))) % 12

        return None

    def _event_time(self, event: Dict[str, Any], key: str) -> Optional[float]:
        # PhoenixVoiceEngine real event schema:
        # event["timing"][key]
        timing = event.get("timing")
        if isinstance(timing, dict):
            value = timing.get(key)
            if isinstance(value, (int, float)):
                return float(value)

        # Backward-compatible flat schema.
        value = event.get(key)
        return float(value) if isinstance(value, (int, float)) else None

    def _analyze_phrase(self, phrase: Dict[str, Any]) -> Dict[str, Any]:
        events = phrase.get("events", [])
        points = []

        for index, event in enumerate(events):
            pc = self._event_pc(event)
            if pc is None:
                continue
            start = self._event_time(event, "start_time")
            end = self._event_time(event, "end_time")
            duration = self._event_time(event, "duration")
            if duration is None and start is not None and end is not None:
                duration = max(0.0, end - start)
            if duration is None:
                duration = 0.0

            points.append({
                "local_index": index,
                "pitch_class": pc,
                "pitch_class_name": self._pc_name(pc),
                "duration": duration,
                "start_time": start,
                "end_time": end,
            })

        if not points:
            return {
                "phrase_index": phrase.get("phrase_index"),
                "event_count": 0,
                "roles": {},
                "final_pitch_class": None,
                "initial_pitch_class": None,
                "transitions": [],
            }

        counts = Counter(p["pitch_class"] for p in points)
        duration_by_pc = defaultdict(float)
        for p in points:
            duration_by_pc[p["pitch_class"]] += max(0.0, p["duration"])

        final_pc = points[-1]["pitch_class"]
        initial_pc = points[0]["pitch_class"]

        transitions = []
        for a, b in zip(points, points[1:]):
            transitions.append({
                "source_pitch_class": a["pitch_class"],
                "source_pitch_class_name": a["pitch_class_name"],
                "target_pitch_class": b["pitch_class"],
                "target_pitch_class_name": b["pitch_class_name"],
            })

        roles = {}
        total_duration = sum(duration_by_pc.values())

        for pc in sorted(counts):
            count = counts[pc]
            duration = duration_by_pc[pc]
            roles[str(pc)] = {
                "pitch_class": pc,
                "pitch_class_name": self._pc_name(pc),
                "event_count": count,
                "duration": round(duration, 6),
                "event_ratio": round(count / len(points), 6),
                "duration_ratio": round(
                    duration / total_duration, 6
                ) if total_duration else 0.0,
                "is_phrase_initial": pc == initial_pc,
                "is_phrase_final": pc == final_pc,
            }

        return {
            "phrase_index": phrase.get("phrase_index"),
            "event_count": len(points),
            "roles": roles,
            "final_pitch_class": final_pc,
            "final_pitch_class_name": self._pc_name(final_pc),
            "initial_pitch_class": initial_pc,
            "initial_pitch_class_name": self._pc_name(initial_pc),
            "transitions": transitions,
        }

    def analyze(
        self,
        phrase_data: Dict[str, Any],
        cadence_data: Optional[Dict[str, Any]] = None,
        tonic_candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        phrases = self._phrase_events(phrase_data)
        phrase_roles = [
            self._analyze_phrase(phrase)
            for phrase in phrases
        ]

        aggregate_count = Counter()
        aggregate_duration = defaultdict(float)
        initial_count = Counter()
        final_count = Counter()
        transition_count = Counter()

        for result in phrase_roles:
            for pc_text, role in result["roles"].items():
                pc = int(pc_text)
                aggregate_count[pc] += role["event_count"]
                aggregate_duration[pc] += role["duration"]

            if result["initial_pitch_class"] is not None:
                initial_count[result["initial_pitch_class"]] += 1
            if result["final_pitch_class"] is not None:
                final_count[result["final_pitch_class"]] += 1

            for t in result["transitions"]:
                transition_count[
                    (t["source_pitch_class"], t["target_pitch_class"])
                ] += 1

        total_events = sum(aggregate_count.values())
        total_duration = sum(aggregate_duration.values())

        functional_roles = []
        for pc in sorted(aggregate_count):
            count = aggregate_count[pc]
            duration = aggregate_duration[pc]
            initial = initial_count[pc]
            final = final_count[pc]

            # These are descriptive evidence dimensions, not maqam labels.
            recurrence = count / total_events if total_events else 0.0
            duration_ratio = (
                duration / total_duration
                if total_duration else 0.0
            )
            phrase_initial_ratio = (
                initial / len(phrase_roles)
                if phrase_roles else 0.0
            )
            phrase_final_ratio = (
                final / len(phrase_roles)
                if phrase_roles else 0.0
            )

            functional_roles.append({
                "pitch_class": pc,
                "pitch_class_name": self._pc_name(pc),
                "event_count": count,
                "duration": round(duration, 6),
                "event_recurrence": round(recurrence, 6),
                "duration_share": round(duration_ratio, 6),
                "phrase_initial_count": initial,
                "phrase_initial_ratio": round(
                    phrase_initial_ratio, 6
                ),
                "phrase_final_count": final,
                "phrase_final_ratio": round(
                    phrase_final_ratio, 6
                ),
            })

        functional_roles.sort(
            key=lambda x: (
                x["phrase_final_ratio"],
                x["duration_share"],
                x["event_recurrence"],
            ),
            reverse=True,
        )

        transitions = [
            {
                "source_pitch_class": a,
                "source_pitch_class_name": self._pc_name(a),
                "target_pitch_class": b,
                "target_pitch_class_name": self._pc_name(b),
                "count": count,
            }
            for (a, b), count in transition_count.most_common()
        ]

        tonic_role_comparison = []
        for tonic in tonic_candidates or []:
            tonic = int(tonic) % 12
            role = next(
                (
                    x for x in functional_roles
                    if x["pitch_class"] == tonic
                ),
                None,
            )
            tonic_role_comparison.append({
                "tonic_pitch_class": tonic,
                "tonic_name": self._pc_name(tonic),
                "role": role,
                "evidence_only": True,
            })

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "input": {
                "phrase_count": len(phrases),
                "event_count": total_events,
                "duration": round(total_duration, 6),
                "tonic_candidates": [
                    int(x) % 12 for x in (tonic_candidates or [])
                ],
            },
            "evidence": {
                "functional_roles": functional_roles,
                "phrase_roles": phrase_roles,
                "transition_evidence": transitions,
                "tonic_role_comparison": tonic_role_comparison,
            },
            "analysis": {
                "purpose": "FUNCTIONAL_PITCH_ROLE_EVIDENCE",
                "source_pitch_modified": False,
                "source_timing_modified": False,
                "source_performance_modified": False,
                "maqam_decision_made": False,
                "tonic_decision_made": False,
            },
            "decision": {
                "status": "EVIDENCE_ONLY",
                "maqam": None,
                "jins": None,
                "tonic": None,
                "confidence": None,
                "reason": ["FUNCTIONAL_ROLE_EVIDENCE_ONLY"],
            },
        }

    def analyze_files(
        self,
        phrase_path: str,
        output_path: str,
        cadence_path: Optional[str] = None,
        tonic_candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        phrase_data = self._load(phrase_path)
        cadence_data = self._load(cadence_path) if cadence_path else None

        result = self.analyze(
            phrase_data,
            cadence_data=cadence_data,
            tonic_candidates=tonic_candidates,
        )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
