"""
PhoenixVoiceEngine
Maqam Candidate Engine V1.0.1

Evidence-fusion candidate ranking.

V1.0.1 fixes three V1.0 issues:
1. A mathematically convenient tonic could be selected even when the
   performance evidence did not support that tonic.
2. Different maqamat with identical coarse 12-TET templates could receive
   identical scores.
3. A single confidence value could look stronger than the evidence quality.

This version therefore:
- separates tonic evidence from scale compatibility;
- requires positive tonic evidence before reporting a supported tonic;
- reports ambiguous candidate clusters explicitly;
- treats 12-TET matching as coarse evidence only;
- keeps maqam/jins/sayr decisions explainable;
- never modifies source data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .maqam_knowledge import MAQAM_KNOWLEDGE


class MaqamCandidateEngine:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.1"

    def __init__(
        self,
        knowledge: Optional[Dict[str, Any]] = None,
        min_candidate_score: float = 0.30,
        supported_confidence: float = 0.78,
        minimum_tonic_evidence: float = 0.35,
        ambiguity_margin: float = 0.08,
        low_stable_event_count: int = 10,
    ) -> None:
        self.knowledge = knowledge or MAQAM_KNOWLEDGE
        self.min_candidate_score = float(min_candidate_score)
        self.supported_confidence = float(supported_confidence)
        self.minimum_tonic_evidence = float(minimum_tonic_evidence)
        self.ambiguity_margin = float(ambiguity_margin)
        self.low_stable_event_count = int(low_stable_event_count)

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    @staticmethod
    def _pc_name(pc: int) -> str:
        names = (
            "C", "C#", "D", "D#", "E", "F",
            "F#", "G", "G#", "A", "A#", "B",
        )
        return names[pc % 12]

    @staticmethod
    def _distribution(evidence: Dict[str, Any]) -> Dict[int, float]:
        raw = (
            evidence
            .get("pitch_class_distribution", {})
            .get("normalized_duration_distribution", {})
        )
        return {
            int(pc) % 12: float(value)
            for pc, value in raw.items()
            if float(value) > 0
        }

    @staticmethod
    def _stable_items(evidence: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            item
            for item in (
                evidence
                .get("stable_note_evidence", {})
                .get("ranked_pitch_classes", [])
            )
            if isinstance(item, dict)
        ]

    @staticmethod
    def _endings(evidence: Dict[str, Any]) -> List[int]:
        result = []
        for item in evidence.get("phrase_endings", []):
            final = item.get("final_event", {})
            pc = final.get("pitch_class")
            if pc is not None:
                result.append(int(pc) % 12)
        return result

    @staticmethod
    def _final_recurrence(
        evidence: Dict[str, Any],
        tonic: int,
    ) -> float:
        summaries = evidence.get("phrase_summaries", [])
        finals = [
            int(x["final_pitch_class"]) % 12
            for x in summaries
            if x.get("final_pitch_class") is not None
        ]
        if not finals:
            return 0.0
        return sum(pc == tonic for pc in finals) / len(finals)

    def _stable_tonic_evidence(
        self,
        evidence: Dict[str, Any],
        tonic: int,
    ) -> float:
        items = self._stable_items(evidence)
        if not items:
            return 0.0

        total = sum(float(x.get("duration", 0.0)) for x in items)
        if total <= 0:
            return 0.0

        tonic_duration = sum(
            float(x.get("duration", 0.0))
            for x in items
            if int(x.get("pitch_class", -1)) % 12 == tonic
        )
        return self._clamp(tonic_duration / total)

    def _ending_tonic_evidence(
        self,
        evidence: Dict[str, Any],
        tonic: int,
    ) -> float:
        endings = self._endings(evidence)
        if not endings:
            return 0.0
        return sum(pc == tonic for pc in endings) / len(endings)

    def _tonic_evidence(
        self,
        evidence: Dict[str, Any],
        tonic: int,
    ) -> Dict[str, float]:
        stable = self._stable_tonic_evidence(evidence, tonic)
        endings = self._ending_tonic_evidence(evidence, tonic)
        recurrence = self._final_recurrence(evidence, tonic)

        # Stable-note evidence is strongest. Phrase endings and recurrence
        # are independent supporting evidence.
        combined = (
            0.50 * stable
            + 0.30 * endings
            + 0.20 * recurrence
        )

        return {
            "stable_notes": round(stable, 6),
            "phrase_endings": round(endings, 6),
            "final_note_recurrence": round(recurrence, 6),
            "combined": round(self._clamp(combined), 6),
        }

    def _scale_compatibility(
        self,
        distribution: Dict[int, float],
        template: Dict[str, Any],
        tonic: int,
    ) -> float:
        if not distribution:
            return 0.0

        expected = {
            (tonic + int(interval)) % 12
            for interval in template["scale_pc_intervals_12tet"]
        }

        inside = sum(
            value for pc, value in distribution.items()
            if pc in expected
        )
        outside = sum(
            value for pc, value in distribution.items()
            if pc not in expected
        )

        # Avoid rewarding a template simply because it contains many
        # observed pitch classes.
        return self._clamp(inside - 0.50 * outside)

    def _jins_compatibility(
        self,
        distribution: Dict[int, float],
        template: Dict[str, Any],
        tonic: int,
    ) -> Tuple[float, str]:
        if not distribution:
            return 0.0, "NO_PITCH_DISTRIBUTION"

        expected = {
            (tonic + int(interval)) % 12
            for interval in template.get("root_jins_12tet", [])
        }

        if not expected:
            return 0.0, "NO_JINS_TEMPLATE"

        observed_weight = sum(
            value for pc, value in distribution.items()
            if pc in expected
        )
        return self._clamp(observed_weight), "COARSE_12TET_JINS_MATCH"

    def _candidate(
        self,
        evidence: Dict[str, Any],
        name: str,
        template: Dict[str, Any],
        tonic: int,
    ) -> Dict[str, Any]:
        distribution = self._distribution(evidence)
        tonic_ev = self._tonic_evidence(evidence, tonic)
        scale = self._scale_compatibility(
            distribution, template, tonic
        )
        jins, jins_basis = self._jins_compatibility(
            distribution, template, tonic
        )

        # The candidate score is deliberately not allowed to turn scale
        # compatibility into tonic evidence.
        score = (
            0.35 * tonic_ev["combined"]
            + 0.35 * scale
            + 0.20 * jins
            + 0.10 * tonic_ev["final_note_recurrence"]
        )

        stable_count = int(
            evidence.get("_stable_event_count", 0)
        )

        evidence_quality = self._clamp(
            0.50
            + 0.50 * min(
                1.0,
                stable_count / max(1, self.low_stable_event_count),
            )
        )

        confidence = self._clamp(
            score * evidence_quality
        )

        # With weak stable evidence we explicitly cap confidence.
        if stable_count < self.low_stable_event_count:
            confidence = min(confidence, 0.65)

        return {
            "maqam": name,
            "family": template.get("family"),
            "root_jins": template.get("root_jins"),
            "upper_jins": template.get("upper_jins", []),
            "tonic_pitch_class": tonic,
            "tonic_name": self._pc_name(tonic),
            "score": round(score, 6),
            "confidence": round(confidence, 6),
            "evidence_quality": round(evidence_quality, 6),
            "tonic_evidence": tonic_ev,
            "components": {
                "scale_compatibility": round(scale, 6),
                "jins_compatibility": round(jins, 6),
                "jins_basis": jins_basis,
            },
        }

    def _best_tonic_for_template(
        self,
        evidence: Dict[str, Any],
        template: Dict[str, Any],
    ) -> Tuple[int, Dict[str, float]]:
        # IMPORTANT: choose tonic from tonic evidence first, not from
        # scale overlap. This prevents an arbitrary "C" from winning.
        best_pc = 0
        best_ev = {
            "stable_notes": 0.0,
            "phrase_endings": 0.0,
            "final_note_recurrence": 0.0,
            "combined": 0.0,
        }

        for tonic in range(12):
            ev = self._tonic_evidence(evidence, tonic)
            if ev["combined"] > best_ev["combined"]:
                best_pc = tonic
                best_ev = ev

        return best_pc, best_ev

    def analyze(
        self,
        evidence_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        evidence = dict(
            evidence_data.get("evidence") or {}
        )

        stable_count = int(
            evidence_data
            .get("analysis", {})
            .get("stable_event_count", 0)
        )
        evidence["_stable_event_count"] = stable_count

        candidates: List[Dict[str, Any]] = []

        for name, template in self.knowledge.items():
            tonic, tonic_ev = self._best_tonic_for_template(
                evidence,
                template,
            )

            candidate = self._candidate(
                evidence,
                name,
                template,
                tonic,
            )

            candidate["tonic_supported"] = (
                tonic_ev["combined"]
                >= self.minimum_tonic_evidence
            )

            candidates.append(candidate)

        candidates.sort(
            key=lambda item: (
                item["confidence"],
                item["score"],
                item["tonic_evidence"]["combined"],
            ),
            reverse=True,
        )

        filtered = [
            item for item in candidates
            if item["score"] >= self.min_candidate_score
        ]

        top = filtered[0] if filtered else None
        second = filtered[1] if len(filtered) > 1 else None

        margin = (
            top["confidence"] - second["confidence"]
            if top and second
            else None
        )

        ambiguous = bool(
            top
            and second
            and margin is not None
            and margin < self.ambiguity_margin
        )

        if top is None:
            status = "UNCERTAIN"
        elif not top["tonic_supported"]:
            status = "UNCERTAIN"
        elif ambiguous:
            status = "AMBIGUOUS"
        elif (
            top["confidence"] >= self.supported_confidence
            and stable_count >= self.low_stable_event_count
        ):
            status = "SUPPORTED"
        elif top["confidence"] >= 0.50:
            status = "CANDIDATE"
        else:
            status = "UNCERTAIN"

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,

            "input": {
                "evidence_version": evidence_data.get("version"),
                "evidence_feature_version": evidence_data.get(
                    "feature_version"
                ),
                "evidence_patch_version": evidence_data.get(
                    "patch_version"
                ),
                "stable_event_count": stable_count,
            },

            "analysis": {
                "min_candidate_score": self.min_candidate_score,
                "supported_confidence": self.supported_confidence,
                "minimum_tonic_evidence": self.minimum_tonic_evidence,
                "ambiguity_margin": self.ambiguity_margin,
                "low_stable_event_count": self.low_stable_event_count,
                "tonic_selected_from_tonic_evidence": True,
                "pitch_class_matching_is_coarse_12tet": True,
                "jins_matching_is_coarse_12tet": True,
                "no_source_correction": True,
                "no_microtonal_reconstruction": True,
            },

            "candidates": filtered,

            "ranking": {
                "top": top,
                "second": second,
                "margin": (
                    round(margin, 6)
                    if margin is not None
                    else None
                ),
                "ambiguous": ambiguous,
            },

            "decision": {
                "status": status,
                "maqam": (
                    top["maqam"]
                    if status == "SUPPORTED"
                    else None
                ),
                "tonic_pitch_class": (
                    top["tonic_pitch_class"]
                    if status == "SUPPORTED"
                    else None
                ),
                "tonic_name": (
                    top["tonic_name"]
                    if status == "SUPPORTED"
                    else None
                ),
                "confidence": (
                    top["confidence"]
                    if top is not None
                    else None
                ),
                "reason": (
                    "INSUFFICIENT_TONIC_EVIDENCE"
                    if top is None or not top["tonic_supported"]
                    else "CANDIDATE_AMBIGUITY"
                    if ambiguous
                    else "SUPPORTED_BY_CURRENT_EVIDENCE"
                    if status == "SUPPORTED"
                    else "EVIDENCE_NOT_STRONG_ENOUGH",
                ),
            },
        }

    def analyze_file(
        self,
        evidence_path: str | Path,
        output_path: str | Path,
    ) -> Dict[str, Any]:
        with Path(evidence_path).open(
            "r",
            encoding="utf-8",
        ) as handle:
            data = json.load(handle)

        result = self.analyze(data)

        output = Path(output_path)
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