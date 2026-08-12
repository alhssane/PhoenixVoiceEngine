"""
PhoenixVoiceEngine
Tonic Intervallic Relationship Analyzer V1.0

Analyzes melodic interval relationships relative to candidate tonics.

IMPORTANT:
- Evidence only.
- No tonic decision.
- No maqam decision.
- No jins decision.
- No source pitch modification.
- No timing modification.
- No performance modification.

The analyzer asks:

    "How well does each candidate tonic explain
     the observed melodic interval relationships?"

It uses:
    1. Stable pitch-center coverage
    2. Pitch-class recurrence
    3. Directed transitions
    4. Relative interval distribution
    5. Tonic-connected transitions
    6. Stable-center duration

It deliberately does NOT declare a tonic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TonicIntervallicRelationshipAnalyzer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    NOTE_NAMES = (
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    )

    # ------------------------------------------------------------
    # IO
    # ------------------------------------------------------------

    @staticmethod
    def _load(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _save(path: str, data: Dict[str, Any]) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    @classmethod
    def _name(cls, pitch_class: int) -> str:
        return cls.NOTE_NAMES[int(pitch_class) % 12]

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:
        return max(
            minimum,
            min(maximum, float(value)),
        )

    @staticmethod
    def _relative_interval(
        tonic_pitch_class: int,
        pitch_class: int,
    ) -> int:
        return (
            int(pitch_class)
            - int(tonic_pitch_class)
        ) % 12

    # ------------------------------------------------------------
    # Extract stable centers
    # ------------------------------------------------------------

    def _extract_stable_centers(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        evidence = data.get("evidence", {})

        centers = evidence.get(
            "stable_pitch_centers",
            [],
        )

        if not isinstance(centers, list):
            return []

        result = []

        for item in centers:
            if not isinstance(item, dict):
                continue

            pc = item.get("pitch_class")

            if pc is None:
                continue

            try:
                pc = int(pc) % 12
            except (TypeError, ValueError):
                continue

            result.append(
                {
                    "pitch_class": pc,
                    "pitch_class_name": self._name(pc),
                    "region_count": int(
                        item.get("region_count", 0)
                    ),
                    "total_duration": float(
                        item.get("total_duration", 0.0)
                    ),
                    "sample_count": int(
                        item.get("sample_count", 0)
                    ),
                    "mean_stability_score": float(
                        item.get(
                            "mean_stability_score",
                            0.0,
                        )
                    ),
                    "center_cents": float(
                        item.get(
                            "center_cents",
                            0.0,
                        )
                    ),
                }
            )

        return result

    # ------------------------------------------------------------
    # Extract transition evidence
    # ------------------------------------------------------------

    def _extract_transitions(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        evidence = data.get("evidence", {})

        stable = evidence.get(
            "stable_transitions",
            {},
        )

        pairs = stable.get(
            "ranked_pairs",
            [],
        )

        if not isinstance(pairs, list):
            return []

        result = []

        for item in pairs:
            if not isinstance(item, dict):
                continue

            source = item.get(
                "source_pitch_class"
            )
            target = item.get(
                "target_pitch_class"
            )
            count = item.get("count")

            if source is None or target is None:
                continue

            try:
                source = int(source) % 12
                target = int(target) % 12
                count = int(count or 0)
            except (TypeError, ValueError):
                continue

            result.append(
                {
                    "source_pitch_class": source,
                    "source_pitch_class_name": self._name(
                        source
                    ),
                    "target_pitch_class": target,
                    "target_pitch_class_name": self._name(
                        target
                    ),
                    "count": count,
                }
            )

        return result

    # ------------------------------------------------------------
    # Pitch recurrence
    # ------------------------------------------------------------

    def _center_recurrence_score(
        self,
        tonic: int,
        centers: List[Dict[str, Any]],
    ) -> float:

        if not centers:
            return 0.0

        total_duration = sum(
            max(0.0, x["total_duration"])
            for x in centers
        )

        if total_duration <= 0:
            return 0.0

        tonic_duration = sum(
            max(0.0, x["total_duration"])
            for x in centers
            if x["pitch_class"] == tonic
        )

        duration_share = (
            tonic_duration
            / total_duration
        )

        # A tonic should be recurring, but we do not
        # require it to dominate the entire melody.
        return self._clamp(
            duration_share * 3.0
        )

    # ------------------------------------------------------------
    # Stable-center relationship evidence
    # ------------------------------------------------------------

    def _stable_relationships(
        self,
        tonic: int,
        centers: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        relationships = []

        for center in centers:
            pc = center["pitch_class"]

            relative = self._relative_interval(
                tonic,
                pc,
            )

            relationships.append(
                {
                    "pitch_class": pc,
                    "pitch_class_name": self._name(pc),
                    "relative_interval": relative,
                    "relative_interval_name": (
                        f"{relative} semitone"
                        if relative == 1
                        else f"{relative} semitones"
                    ),
                    "duration": center[
                        "total_duration"
                    ],
                    "region_count": center[
                        "region_count"
                    ],
                    "stability": center[
                        "mean_stability_score"
                    ],
                    "center_cents": center[
                        "center_cents"
                    ],
                }
            )

        return {
            "relationships": relationships,
            "coverage": self._clamp(
                len(relationships) / 12.0
            ),
        }

    # ------------------------------------------------------------
    # Relative interval distribution
    # ------------------------------------------------------------

    def _relative_interval_distribution(
        self,
        tonic: int,
        transitions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        counts = {
            str(i): 0
            for i in range(12)
        }

        total = 0

        for transition in transitions:

            source = transition[
                "source_pitch_class"
            ]

            target = transition[
                "target_pitch_class"
            ]

            count = transition["count"]

            if count <= 0:
                continue

            relative_source = (
                self._relative_interval(
                    tonic,
                    source,
                )
            )

            relative_target = (
                self._relative_interval(
                    tonic,
                    target,
                )
            )

            # The intervallic displacement itself is
            # independent of absolute tonic, but the
            # relative positions are tonic-dependent.
            displacement = (
                relative_target
                - relative_source
            ) % 12

            counts[str(displacement)] += count
            total += count

        distribution = {}

        if total > 0:
            for key, value in counts.items():
                distribution[key] = round(
                    value / total,
                    6,
                )
        else:
            distribution = {
                key: 0.0
                for key in counts
            }

        return {
            "counts": counts,
            "distribution": distribution,
            "total": total,
        }

    # ------------------------------------------------------------
    # Tonic-connected transition evidence
    # ------------------------------------------------------------

    def _tonic_transition_evidence(
        self,
        tonic: int,
        transitions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        incoming = 0
        outgoing = 0
        self_transition = 0

        incoming_sources: Dict[str, int] = {}
        outgoing_targets: Dict[str, int] = {}

        total = 0

        for transition in transitions:

            source = transition[
                "source_pitch_class"
            ]

            target = transition[
                "target_pitch_class"
            ]

            count = transition["count"]

            if count <= 0:
                continue

            total += count

            if target == tonic:
                incoming += count

                key = str(source)
                incoming_sources[key] = (
                    incoming_sources.get(key, 0)
                    + count
                )

            if source == tonic:
                outgoing += count

                key = str(target)
                outgoing_targets[key] = (
                    outgoing_targets.get(key, 0)
                    + count
                )

            if (
                source == tonic
                and target == tonic
            ):
                self_transition += count

        if total <= 0:
            return {
                "incoming_count": 0,
                "outgoing_count": 0,
                "self_transition_count": 0,
                "incoming_ratio": 0.0,
                "outgoing_ratio": 0.0,
                "self_ratio": 0.0,
                "incoming_sources": {},
                "outgoing_targets": {},
                "score": 0.0,
            }

        incoming_ratio = (
            incoming / total
        )

        outgoing_ratio = (
            outgoing / total
        )

        self_ratio = (
            self_transition / total
        )

        # A tonic often participates in both arrivals
        # and departures. This is descriptive evidence,
        # not a tonic decision.
        score = (
            0.45 * self._clamp(
                incoming_ratio * 8.0
            )
            + 0.35 * self._clamp(
                outgoing_ratio * 8.0
            )
            + 0.20 * self._clamp(
                self_ratio * 12.0
            )
        )

        return {
            "incoming_count": incoming,
            "outgoing_count": outgoing,
            "self_transition_count": (
                self_transition
            ),
            "incoming_ratio": round(
                incoming_ratio,
                6,
            ),
            "outgoing_ratio": round(
                outgoing_ratio,
                6,
            ),
            "self_ratio": round(
                self_ratio,
                6,
            ),
            "incoming_sources": (
                incoming_sources
            ),
            "outgoing_targets": (
                outgoing_targets
            ),
            "score": round(
                self._clamp(score),
                6,
            ),
        }

    # ------------------------------------------------------------
    # Candidate analysis
    # ------------------------------------------------------------

    def _analyze_candidate(
        self,
        tonic: int,
        centers: List[Dict[str, Any]],
        transitions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        stable = self._stable_relationships(
            tonic,
            centers,
        )

        distribution = (
            self._relative_interval_distribution(
                tonic,
                transitions,
            )
        )

        tonic_transition = (
            self._tonic_transition_evidence(
                tonic,
                transitions,
            )
        )

        recurrence = (
            self._center_recurrence_score(
                tonic,
                centers,
            )
        )

        stable_coverage = stable[
            "coverage"
        ]

        # The relationship-distribution component is
        # intentionally conservative. Since the observed
        # interval displacement itself is invariant under
        # transposition, this component mainly measures
        # evidence availability rather than pretending
        # to discriminate tonic by itself.
        relationship_availability = (
            self._clamp(
                len(transitions) / 100.0
            )
        )

        score = (
            0.30 * recurrence
            + 0.30 * tonic_transition["score"]
            + 0.20 * stable_coverage
            + 0.20 * relationship_availability
        )

        score = self._clamp(score)

        return {
            "tonic_pitch_class": tonic,
            "tonic_name": self._name(tonic),
            "score": round(score, 6),

            "components": {
                "pitch_recurrence": round(
                    recurrence,
                    6,
                ),
                "tonic_transition": round(
                    tonic_transition["score"],
                    6,
                ),
                "stable_center_coverage": round(
                    stable_coverage,
                    6,
                ),
                "relationship_availability": round(
                    relationship_availability,
                    6,
                ),
            },

            "stable_relationships": stable[
                "relationships"
            ],

            "relative_interval_distribution": (
                distribution
            ),

            "tonic_transition_evidence": (
                tonic_transition
            ),

            "evidence_only": True,
        }

    # ------------------------------------------------------------
    # Main
    # ------------------------------------------------------------

    def analyze(
        self,
        stable_data: Dict[str, Any],
        cadence_data: Optional[
            Dict[str, Any]
        ] = None,
        candidates: Optional[
            List[int]
        ] = None,
    ) -> Dict[str, Any]:

        candidates = [
            int(x) % 12
            for x in (
                candidates
                or [7, 0]
            )
        ]

        centers = (
            self._extract_stable_centers(
                stable_data
            )
        )

        transitions = (
            self._extract_transitions(
                cadence_data or {}
            )
        )

        ranking = []

        for tonic in candidates:
            ranking.append(
                self._analyze_candidate(
                    tonic,
                    centers,
                    transitions,
                )
            )

        ranking.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        top = (
            ranking[0]
            if ranking
            else None
        )

        second = (
            ranking[1]
            if len(ranking) > 1
            else None
        )

        margin = (
            round(
                top["score"]
                - second["score"],
                6,
            )
            if top and second
            else 0.0
        )

        return {
            "version": self.VERSION,
            "feature_version": (
                self.FEATURE_VERSION
            ),
            "patch_version": (
                self.PATCH_VERSION
            ),

            "input": {
                "stable_center_count": len(
                    centers
                ),
                "transition_count": len(
                    transitions
                ),
                "candidate_pitch_classes": (
                    candidates
                ),
            },

            "evidence": {
                "stable_centers": centers,
                "transitions": transitions,
            },

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
                "reason": [
                    "TONIC_INTERVALLIC_RELATIONSHIP_EVIDENCE_ONLY"
                ],
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

    # ------------------------------------------------------------
    # File API
    # ------------------------------------------------------------

    def analyze_files(
        self,
        stable_path: str,
        cadence_path: str,
        output_path: str,
        candidates: Optional[
            List[int]
        ] = None,
    ) -> Dict[str, Any]:

        stable_data = self._load(
            stable_path
        )

        cadence_data = self._load(
            cadence_path
        )

        result = self.analyze(
            stable_data,
            cadence_data,
            candidates=candidates,
        )

        self._save(
            output_path,
            result,
        )

        return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "stable_path"
    )

    parser.add_argument(
        "cadence_path"
    )

    parser.add_argument(
        "output_path"
    )

    parser.add_argument(
        "--candidates",
        nargs="+",
        type=int,
        default=[7, 0],
    )

    args = parser.parse_args()

    analyzer = (
        TonicIntervallicRelationshipAnalyzer()
    )

    result = analyzer.analyze_files(
        stable_path=args.stable_path,
        cadence_path=args.cadence_path,
        output_path=args.output_path,
        candidates=args.candidates,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )