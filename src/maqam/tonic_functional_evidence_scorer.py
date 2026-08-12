"""
PhoenixVoiceEngine
Tonic Functional Evidence Scorer V1.0

Evidence-only scorer for tonic/candidate pitch-class functional strength.

This component:
- scores pitch-class functional evidence
- compares candidate tonics such as G and C
- preserves source pitch/timing/performance
- does not decide maqam
- does not decide jins
- does not correct pitch
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicFunctionalEvidenceScorer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    NOTE_NAMES = (
        "C", "C#", "D", "D#", "E", "F",
        "F#", "G", "G#", "A", "A#", "B"
    )

    def _load(self, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _clamp(value: Any, low: float = 0.0, high: float = 1.0) -> float:
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = 0.0
        return max(low, min(high, value))

    @classmethod
    def _name(cls, pc: int) -> str:
        return cls.NOTE_NAMES[int(pc) % 12]

    @staticmethod
    def _role_map(functional_data: Dict[str, Any]) -> Dict[int, Dict[str, Any]]:
        roles = (
            functional_data.get("evidence", {})
            .get("functional_roles", [])
        )
        return {
            int(x["pitch_class"]) % 12: x
            for x in roles
            if isinstance(x, dict) and "pitch_class" in x
        }

    @staticmethod
    def _transition_map(functional_data: Dict[str, Any]) -> Dict[tuple, int]:
        transitions = (
            functional_data.get("evidence", {})
            .get("transition_evidence", [])
        )
        result = {}
        for x in transitions:
            if not isinstance(x, dict):
                continue
            try:
                a = int(x["source_pitch_class"]) % 12
                b = int(x["target_pitch_class"]) % 12
                result[(a, b)] = int(x.get("count", 0))
            except (KeyError, TypeError, ValueError):
                continue
        return result

    @staticmethod
    def _stable_map(stable_data: Optional[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        if not stable_data:
            return {}
        centers = (
            stable_data.get("evidence", {})
            .get("stable_pitch_centers", [])
        )
        return {
            int(x["pitch_class"]) % 12: x
            for x in centers
            if isinstance(x, dict) and "pitch_class" in x
        }

    @staticmethod
    def _cadence_final_counts(cadence_data: Optional[Dict[str, Any]]) -> Dict[int, int]:
        if not cadence_data:
            return {}
        counts = (
            cadence_data.get("evidence", {})
            .get("cadences", {})
            .get("final_pitch_class_counts", {})
        )
        result = {}
        if isinstance(counts, dict):
            for k, v in counts.items():
                try:
                    result[int(k) % 12] = int(v)
                except (TypeError, ValueError):
                    pass
        return result

    def _approach_evidence(
        self,
        tonic: int,
        transitions: Dict[tuple, int],
    ) -> float:
        """
        Evidence that other notes resolve into the candidate tonic.

        Uses observed transition counts only. It does not assume
        a theoretically preferred interval.
        """
        incoming = sum(
            count for (source, target), count in transitions.items()
            if target == tonic and source != tonic
        )
        outgoing = sum(
            count for (source, target), count in transitions.items()
            if source == tonic and target != tonic
        )

        if incoming <= 0 and outgoing <= 0:
            return 0.0

        # Resolution evidence is weighted toward incoming movement,
        # while departure evidence prevents a tonic with no activity
        # from being rewarded.
        incoming_score = incoming / max(incoming + outgoing, 1)
        activity = min(1.0, (incoming + outgoing) / 20.0)

        return round(self._clamp(
            0.70 * incoming_score + 0.30 * activity
        ), 6)

    def _cadence_evidence(
        self,
        tonic: int,
        role: Optional[Dict[str, Any]],
        cadence_counts: Dict[int, int],
        phrase_count: int,
    ) -> float:
        role_final = (
            self._clamp(role.get("phrase_final_ratio", 0.0))
            if role else 0.0
        )

        observed_final = cadence_counts.get(tonic, 0)
        observed_ratio = (
            observed_final / phrase_count
            if phrase_count else 0.0
        )

        # Both sources describe phrase-final behavior, so keep them
        # as independent evidence channels and average them.
        return round(self._clamp(
            0.60 * role_final + 0.40 * observed_ratio
        ), 6)

    def _stable_center_evidence(
        self,
        tonic: int,
        stable_map: Dict[int, Dict[str, Any]],
    ) -> float:
        center = stable_map.get(tonic)
        if not center:
            return 0.0

        region_count = float(center.get("region_count", 0) or 0)
        duration = float(center.get("total_duration", 0.0) or 0.0)
        stability = self._clamp(center.get("mean_stability_score", 0.0))

        recurrence = min(1.0, region_count / 100.0)
        duration_score = min(1.0, duration / 40.0)

        return round(self._clamp(
            0.40 * recurrence +
            0.30 * duration_score +
            0.30 * stability
        ), 6)

    def _local_stability(
        self,
        tonic: int,
        role: Optional[Dict[str, Any]],
        transitions: Dict[tuple, int],
    ) -> float:
        if not role:
            return 0.0

        self_repetition = transitions.get((tonic, tonic), 0)
        self_rep_score = min(1.0, self_repetition / 20.0)

        duration_share = self._clamp(role.get("duration_share", 0.0))
        event_recurrence = self._clamp(role.get("event_recurrence", 0.0))

        return round(self._clamp(
            0.35 * self_rep_score +
            0.35 * duration_share +
            0.30 * event_recurrence
        ), 6)

    def _initial_evidence(
        self,
        role: Optional[Dict[str, Any]],
    ) -> float:
        if not role:
            return 0.0
        return round(self._clamp(role.get("phrase_initial_ratio", 0.0)), 6)

    def _build_candidate(
        self,
        tonic: int,
        role: Optional[Dict[str, Any]],
        transitions: Dict[tuple, int],
        stable_map: Dict[int, Dict[str, Any]],
        cadence_counts: Dict[int, int],
        phrase_count: int,
        weights: Dict[str, float],
    ) -> Dict[str, Any]:
        cadence = self._cadence_evidence(
            tonic, role, cadence_counts, phrase_count
        )
        final_strength = (
            self._clamp(role.get("phrase_final_ratio", 0.0))
            if role else 0.0
        )
        initial_strength = self._initial_evidence(role)
        local_stability = self._local_stability(
            tonic, role, transitions
        )
        approach = self._approach_evidence(tonic, transitions)
        stable_center = self._stable_center_evidence(
            tonic, stable_map
        )

        score = (
            weights["cadence"] * cadence +
            weights["final_strength"] * final_strength +
            weights["initial_strength"] * initial_strength +
            weights["local_stability"] * local_stability +
            weights["approach"] * approach +
            weights["stable_center"] * stable_center
        )

        role_duration = (
            float(role.get("duration", 0.0))
            if role else 0.0
        )

        return {
            "tonic_pitch_class": tonic,
            "tonic_name": self._name(tonic),
            "score": round(self._clamp(score), 6),
            "components": {
                "cadence_evidence": cadence,
                "final_strength": round(final_strength, 6),
                "initial_strength": initial_strength,
                "local_stability": local_stability,
                "approach_evidence": approach,
                "stable_center_evidence": stable_center,
            },
            "observed_role": {
                "event_count": int(role.get("event_count", 0))
                if role else 0,
                "duration": round(role_duration, 6),
                "duration_share": (
                    self._clamp(role.get("duration_share", 0.0))
                    if role else 0.0
                ),
                "phrase_initial_count": int(
                    role.get("phrase_initial_count", 0)
                ) if role else 0,
                "phrase_final_count": int(
                    role.get("phrase_final_count", 0)
                ) if role else 0,
            },
            "evidence_only": True,
        }

    def analyze(
        self,
        functional_data: Dict[str, Any],
        stable_data: Optional[Dict[str, Any]] = None,
        cadence_data: Optional[Dict[str, Any]] = None,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        candidates = [
            int(x) % 12 for x in (candidates or [7, 0])
        ]

        roles = self._role_map(functional_data)
        transitions = self._transition_map(functional_data)
        stable_map = self._stable_map(stable_data)
        cadence_counts = self._cadence_final_counts(cadence_data)

        phrase_count = int(
            functional_data.get("input", {}).get("phrase_count", 0)
        )

        # Deliberately explicit and inspectable weights.
        weights = {
            "cadence": 0.25,
            "final_strength": 0.20,
            "initial_strength": 0.10,
            "local_stability": 0.15,
            "approach": 0.15,
            "stable_center": 0.15,
        }

        ranking = [
            self._build_candidate(
                tonic,
                roles.get(tonic),
                transitions,
                stable_map,
                cadence_counts,
                phrase_count,
                weights,
            )
            for tonic in candidates
        ]
        ranking.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        top = ranking[0] if ranking else None
        second = ranking[1] if len(ranking) > 1 else None
        margin = (
            round(top["score"] - second["score"], 6)
            if top and second else 0.0
        )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "input": {
                "phrase_count": phrase_count,
                "candidate_pitch_classes": candidates,
                "stable_center_count": len(stable_map),
                "cadence_final_pitch_class_count": sum(
                    cadence_counts.values()
                ),
            },
            "weights": weights,
            "ranking": {
                "candidates": ranking,
                "top": top,
                "second": second,
                "margin": margin,
            },
            "decision": {
                "status": "EVIDENCE_ONLY",
                "tonic_pitch_class": None,
                "tonic_name": None,
                "maqam": None,
                "jins": None,
                "confidence": None,
                "reason": ["TONIC_FUNCTIONAL_EVIDENCE_ONLY"],
            },
            "protection": {
                "source_pitch_modified": False,
                "source_timing_modified": False,
                "source_performance_modified": False,
                "tonic_decision_made": False,
                "maqam_decision_made": False,
                "jins_decision_made": False,
            },
        }

    def analyze_files(
        self,
        functional_path: str,
        output_path: str,
        stable_path: Optional[str] = None,
        cadence_path: Optional[str] = None,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        functional_data = self._load(functional_path)
        stable_data = self._load(stable_path) if stable_path else None
        cadence_data = self._load(cadence_path) if cadence_path else None

        result = self.analyze(
            functional_data,
            stable_data=stable_data,
            cadence_data=cadence_data,
            candidates=candidates,
        )

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
