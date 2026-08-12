"""
PhoenixVoiceEngine
Maqam Candidate Evidence Scorer V1.0.2

Adds cadence and transition evidence to maqam candidates.

Design rules:
- Evidence only; no source correction.
- Does not invent microtonal information.
- Uses the candidate tonic supplied by the candidate engine.
- Uses 12-TET relationships only when the source evidence is 12-TET.
- Explicitly reports when two candidates remain indistinguishable by the
  available evidence.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


class MaqamCandidateEvidenceScorer:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.2"

    def __init__(
        self,
        cadence_weight: float = 0.35,
        transition_weight: float = 0.35,
        final_recurrence_weight: float = 0.30,
    ) -> None:
        total = (
            cadence_weight
            + transition_weight
            + final_recurrence_weight
        )
        if total <= 0:
            raise ValueError("Evidence weights must have a positive sum.")

        self.cadence_weight = cadence_weight / total
        self.transition_weight = transition_weight / total
        self.final_recurrence_weight = final_recurrence_weight / total

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    @staticmethod
    def _relative_pc(source: int, tonic: int) -> int:
        return (int(source) - int(tonic)) % 12

    @staticmethod
    def _transition_direction(
        source: int,
        target: int,
    ) -> str:
        delta = (target - source) % 12
        if delta == 0:
            return "STATIONARY"
        return "ASCENDING" if delta <= 6 else "DESCENDING"

    def _cadence_score(
        self,
        evidence: Dict[str, Any],
        tonic: int,
    ) -> Dict[str, Any]:
        cadences = (
            evidence
            .get("cadences", {})
            .get("cadences", [])
        )

        if not cadences:
            return {
                "score": 0.0,
                "ending_on_tonic": 0,
                "cadence_count": 0,
                "approach_to_tonic": 0.0,
            }

        ending_count = 0
        approach_count = 0
        usable = 0

        for cadence in cadences:
            final_pc = cadence.get("final_pitch_class")
            window = cadence.get("window_pitch_classes", [])

            if final_pc is None:
                continue

            usable += 1

            if int(final_pc) % 12 == tonic:
                ending_count += 1

                if len(window) >= 2:
                    previous = int(window[-2]) % 12
                    if previous != tonic:
                        approach_count += 1

        if usable == 0:
            return {
                "score": 0.0,
                "ending_on_tonic": 0,
                "cadence_count": 0,
                "approach_to_tonic": 0.0,
            }

        ending_ratio = ending_count / usable
        approach_ratio = (
            approach_count / ending_count
            if ending_count
            else 0.0
        )

        score = (
            0.70 * ending_ratio
            + 0.30 * approach_ratio
        )

        return {
            "score": round(self._clamp(score), 6),
            "ending_on_tonic": ending_count,
            "cadence_count": usable,
            "approach_to_tonic": round(
                self._clamp(approach_ratio),
                6,
            ),
        }

    def _transition_score(
        self,
        evidence: Dict[str, Any],
        tonic: int,
        scale_intervals: List[int],
    ) -> Dict[str, Any]:
        pairs = (
            evidence
            .get("stable_transitions", {})
            .get("ranked_pairs", [])
        )

        if not pairs:
            return {
                "score": 0.0,
                "transition_count": 0,
                "in_scale_transition_ratio": 0.0,
                "tonic_related_transition_ratio": 0.0,
            }

        scale = {
            int(interval) % 12
            for interval in scale_intervals
        }

        total = 0
        in_scale = 0
        tonic_related = 0

        for pair in pairs:
            source = pair.get("source_pitch_class")
            target = pair.get("target_pitch_class")
            count = int(pair.get("count", 0))

            if source is None or target is None or count <= 0:
                continue

            total += count

            source_rel = self._relative_pc(source, tonic)
            target_rel = self._relative_pc(target, tonic)

            if source_rel in scale and target_rel in scale:
                in_scale += count

            if source_rel == 0 or target_rel == 0:
                tonic_related += count

        if total == 0:
            return {
                "score": 0.0,
                "transition_count": 0,
                "in_scale_transition_ratio": 0.0,
                "tonic_related_transition_ratio": 0.0,
            }

        in_scale_ratio = in_scale / total
        tonic_related_ratio = tonic_related / total

        score = (
            0.70 * in_scale_ratio
            + 0.30 * min(1.0, tonic_related_ratio * 2.0)
        )

        return {
            "score": round(self._clamp(score), 6),
            "transition_count": total,
            "in_scale_transition_ratio": round(
                self._clamp(in_scale_ratio),
                6,
            ),
            "tonic_related_transition_ratio": round(
                self._clamp(tonic_related_ratio),
                6,
            ),
        }

    def _final_recurrence(
        self,
        evidence: Dict[str, Any],
        tonic: int,
    ) -> Dict[str, Any]:
        counts = (
            evidence
            .get("cadences", {})
            .get("final_pitch_class_counts", {})
        )

        total = sum(int(v) for v in counts.values())
        tonic_count = int(counts.get(str(tonic), 0))

        ratio = tonic_count / total if total else 0.0

        return {
            "score": round(self._clamp(ratio), 6),
            "tonic_final_count": tonic_count,
            "final_count": total,
        }

    def score_candidate(
        self,
        candidate: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        evidence = evidence_data.get("evidence", {})
        tonic = int(candidate["tonic_pitch_class"])

        # Candidate knowledge is deliberately used as supplied by the
        # existing knowledge base. No new maqam intervals are invented here.
        knowledge = candidate.get("_knowledge", {})
        scale_intervals = knowledge.get(
            "scale_pc_intervals_12tet",
            [],
        )

        cadence = self._cadence_score(evidence, tonic)
        transition = self._transition_score(
            evidence,
            tonic,
            scale_intervals,
        )
        recurrence = self._final_recurrence(evidence, tonic)

        combined = (
            self.cadence_weight * cadence["score"]
            + self.transition_weight * transition["score"]
            + self.final_recurrence_weight * recurrence["score"]
        )

        return {
            "cadence": cadence,
            "transition": transition,
            "final_recurrence": recurrence,
            "combined": round(
                self._clamp(combined),
                6,
            ),
        }

    def enrich(
        self,
        candidates: List[Dict[str, Any]],
        evidence_data: Dict[str, Any],
        knowledge: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        enriched = []

        for original in candidates:
            candidate = dict(original)
            maqam = candidate["maqam"]

            candidate["_knowledge"] = knowledge.get(
                maqam,
                {},
            )

            evidence_score = self.score_candidate(
                candidate,
                evidence_data,
            )

            candidate["cadence_evidence"] = evidence_score

            # Preserve the original score. The new score is a separate
            # evidence channel until the integration stage is validated.
            candidate["evidence_fusion_score"] = evidence_score["combined"]

            candidate.pop("_knowledge", None)
            enriched.append(candidate)

        return enriched

    def discrimination_report(
        self,
        candidates: List[Dict[str, Any]],
        tolerance: float = 0.02,
    ) -> Dict[str, Any]:
        if not candidates:
            return {
                "status": "NO_CANDIDATES",
                "indistinguishable_groups": [],
            }

        groups = []
        used = set()

        for i, candidate in enumerate(candidates):
            if i in used:
                continue

            score = float(
                candidate.get(
                    "evidence_fusion_score",
                    0.0,
                )
            )

            group = [candidate]
            used.add(i)

            for j in range(i + 1, len(candidates)):
                if j in used:
                    continue

                other_score = float(
                    candidates[j].get(
                        "evidence_fusion_score",
                        0.0,
                    )
                )

                if abs(score - other_score) <= tolerance:
                    group.append(candidates[j])
                    used.add(j)

            if len(group) > 1:
                groups.append({
                    "candidates": [
                        {
                            "maqam": x["maqam"],
                            "tonic_name": x["tonic_name"],
                            "evidence_fusion_score": x[
                                "evidence_fusion_score"
                            ],
                        }
                        for x in group
                    ],
                    "reason": "EVIDENCE_TOO_SIMILAR_TO_DISCRIMINATE",
                })

        return {
            "status": (
                "DISCRIMINATION_LIMITED"
                if groups
                else "DISCRIMINATION_AVAILABLE"
            ),
            "indistinguishable_groups": groups,
        }
