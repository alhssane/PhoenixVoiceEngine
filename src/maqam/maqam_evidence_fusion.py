"""
PhoenixVoiceEngine
Maqam Evidence Fusion V1.0.2

Integrates the existing Maqam Candidate Engine ranking with the newly
validated Jins/Cadence evidence.

Design:
- Never changes source pitch or timing.
- Never invents a maqam decision.
- Keeps the original candidate score visible.
- Keeps new evidence components visible.
- Uses coarse 12-TET scale compatibility only as an explicit limitation.
- If candidates remain too close, returns AMBIGUOUS.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


# Coarse 12-TET interval sets only.
# Bayati and Kurd intentionally share the same coarse representation here.
# This is a limitation, not a claim that the maqamat are musically identical.
COARSE_SCALE_12TET = {
    "BAYATI": [0, 1, 3, 5, 7, 8, 10],
    "KURD": [0, 1, 3, 5, 7, 8, 10],
    "NAHAWAND": [0, 2, 3, 5, 7, 8, 11],
    "HIJAZ": [0, 1, 4, 5, 7, 8, 11],
    "SABA": [0, 1, 3, 5, 6, 8, 10],
    "RAST": [0, 2, 4, 5, 7, 9, 10],
    "AJAM": [0, 2, 4, 5, 7, 9, 11],
    "SIKAH": [],
}


class MaqamEvidenceFusion:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.2"

    def __init__(
        self,
        original_weight: float = 0.55,
        evidence_weight: float = 0.45,
        ambiguity_margin: float = 0.025,
    ) -> None:
        if original_weight < 0 or evidence_weight < 0:
            raise ValueError("Weights must be non-negative.")
        if original_weight + evidence_weight <= 0:
            raise ValueError("At least one weight must be positive.")
        if ambiguity_margin < 0:
            raise ValueError("ambiguity_margin must be non-negative.")

        total = original_weight + evidence_weight
        self.original_weight = original_weight / total
        self.evidence_weight = evidence_weight / total
        self.ambiguity_margin = ambiguity_margin

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    @staticmethod
    def _relative_pc(source: int, tonic: int) -> int:
        return (int(source) - int(tonic)) % 12

    def _cadence_score(
        self,
        evidence: Dict[str, Any],
        tonic: int,
    ) -> Dict[str, Any]:
        cadences = evidence.get("cadences", {}).get("cadences", [])
        usable = 0
        ending = 0
        approach = 0

        for c in cadences:
            final = c.get("final_pitch_class")
            window = c.get("window_pitch_classes", [])
            if final is None:
                continue
            usable += 1
            if int(final) % 12 == tonic:
                ending += 1
                if len(window) >= 2 and int(window[-2]) % 12 != tonic:
                    approach += 1

        ending_ratio = ending / usable if usable else 0.0
        approach_ratio = approach / ending if ending else 0.0
        score = 0.70 * ending_ratio + 0.30 * approach_ratio

        return {
            "score": round(self._clamp(score), 6),
            "ending_on_tonic": ending,
            "cadence_count": usable,
            "approach_to_tonic": round(self._clamp(approach_ratio), 6),
        }

    def _final_recurrence(
        self,
        evidence: Dict[str, Any],
        tonic: int,
    ) -> Dict[str, Any]:
        counts = evidence.get("cadences", {}).get(
            "final_pitch_class_counts", {}
        )
        total = sum(int(v) for v in counts.values())
        tonic_count = int(counts.get(str(tonic), 0))
        ratio = tonic_count / total if total else 0.0

        return {
            "score": round(self._clamp(ratio), 6),
            "tonic_final_count": tonic_count,
            "final_count": total,
        }

    def _transition_score(
        self,
        evidence: Dict[str, Any],
        tonic: int,
        maqam: str,
    ) -> Dict[str, Any]:
        pairs = evidence.get("stable_transitions", {}).get(
            "ranked_pairs", []
        )

        scale = set(COARSE_SCALE_12TET.get(maqam, []))
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

            if scale and source_rel in scale and target_rel in scale:
                in_scale += count

            if source_rel == 0 or target_rel == 0:
                tonic_related += count

        in_scale_ratio = in_scale / total if total else 0.0
        tonic_ratio = tonic_related / total if total else 0.0

        # For Sikah, coarse 12-TET cannot represent the defining jins.
        # Do not pretend otherwise; use only tonic-related evidence.
        if not scale:
            score = min(1.0, tonic_ratio * 2.0)
            basis = "TONIC_ONLY_12TET_LIMITATION"
        else:
            score = (
                0.70 * in_scale_ratio
                + 0.30 * min(1.0, tonic_ratio * 2.0)
            )
            basis = "COARSE_12TET"

        return {
            "score": round(self._clamp(score), 6),
            "transition_count": total,
            "in_scale_transition_ratio": round(
                self._clamp(in_scale_ratio), 6
            ),
            "tonic_related_transition_ratio": round(
                self._clamp(tonic_ratio), 6
            ),
            "basis": basis,
        }

    def _evidence_score(
        self,
        candidate: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        tonic = int(candidate["tonic_pitch_class"])
        maqam = str(candidate["maqam"]).upper()

        cadence = self._cadence_score(
            evidence_data["evidence"], tonic
        )
        transition = self._transition_score(
            evidence_data["evidence"], tonic, maqam
        )
        recurrence = self._final_recurrence(
            evidence_data["evidence"], tonic
        )

        # These weights emphasize phrase endings and recurrence while still
        # using movement evidence.
        combined = (
            0.40 * cadence["score"]
            + 0.35 * transition["score"]
            + 0.25 * recurrence["score"]
        )

        return {
            "combined": round(self._clamp(combined), 6),
            "cadence": cadence,
            "transition": transition,
            "final_recurrence": recurrence,
        }

    def fuse(
        self,
        candidates_data: Dict[str, Any],
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        candidates = candidates_data.get("candidates", [])
        ranked: List[Dict[str, Any]] = []

        for candidate in candidates:
            original_score = float(candidate.get("score", 0.0))
            evidence = self._evidence_score(
                candidate, evidence_data
            )
            fused = (
                self.original_weight * original_score
                + self.evidence_weight * evidence["combined"]
            )

            item = dict(candidate)
            item["original_candidate_score"] = round(
                self._clamp(original_score), 6
            )
            item["new_evidence"] = evidence
            item["fused_score"] = round(
                self._clamp(fused), 6
            )
            ranked.append(item)

        ranked.sort(
            key=lambda x: x["fused_score"],
            reverse=True,
        )

        top = ranked[0] if ranked else None
        second = ranked[1] if len(ranked) > 1 else None

        margin = (
            top["fused_score"] - second["fused_score"]
            if top and second
            else 1.0
        )

        # We do not use the score alone as a permission to decide.
        # Existing candidate status/uncertainty is preserved as context.
        if not top:
            status = "NO_CANDIDATES"
            decision = None
        elif second and margin <= self.ambiguity_margin:
            status = "AMBIGUOUS"
            decision = {
                "status": status,
                "maqam": None,
                "tonic_name": None,
                "confidence": round(
                    float(top.get("confidence", 0.0)), 6
                ),
                "reason": [
                    "FUSED_CANDIDATE_AMBIGUITY",
                    "EVIDENCE_MARGIN_TOO_SMALL",
                ],
            }
        else:
            # The fusion layer reports a leading candidate, but only if the
            # original candidate engine did not explicitly reject it.
            original_status = candidates_data.get(
                "decision", {}
            ).get("status")

            if original_status in {"UNCERTAIN", "AMBIGUOUS"}:
                status = "LEADING_CANDIDATE_NOT_CONFIRMED"
                decision = {
                    "status": status,
                    "maqam": None,
                    "tonic_name": None,
                    "confidence": round(
                        float(top.get("confidence", 0.0)), 6
                    ),
                    "reason": [
                        "ORIGINAL_ENGINE_NOT_CONFIDENT",
                        "FUSION_DOES_NOT_OVERRIDE_PROTECTION",
                    ],
                }
            else:
                status = "LEADING_CANDIDATE"
                decision = {
                    "status": status,
                    "maqam": top.get("maqam"),
                    "tonic_name": top.get("tonic_name"),
                    "confidence": round(
                        float(top.get("confidence", 0.0)), 6
                    ),
                    "reason": ["FUSED_EVIDENCE_LEAD"],
                }

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "weights": {
                "original_candidate": round(self.original_weight, 6),
                "new_evidence": round(self.evidence_weight, 6),
            },
            "input": {
                "candidate_count": len(candidates),
                "evidence_status": evidence_data.get(
                    "decision", {}
                ).get("status"),
            },
            "ranking": {
                "candidates": ranked,
                "top": (
                    {
                        "maqam": top["maqam"],
                        "tonic_name": top["tonic_name"],
                        "fused_score": top["fused_score"],
                    }
                    if top else None
                ),
                "second": (
                    {
                        "maqam": second["maqam"],
                        "tonic_name": second["tonic_name"],
                        "fused_score": second["fused_score"],
                    }
                    if second else None
                ),
                "margin": round(float(margin), 6),
            },
            "decision": decision,
            "protection": {
                "source_pitch_modified": False,
                "source_timing_modified": False,
                "source_performance_modified": False,
                "original_candidate_decision_overridden": False,
                "microtonal_claim_from_12tet": False,
            },
        }

    def analyze_file(
        self,
        candidates_path: str,
        evidence_path: str,
        output_path: str,
    ) -> Dict[str, Any]:
        with open(candidates_path, "r", encoding="utf-8") as f:
            candidates = json.load(f)

        with open(evidence_path, "r", encoding="utf-8") as f:
            evidence = json.load(f)

        result = self.fuse(candidates, evidence)

        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result
