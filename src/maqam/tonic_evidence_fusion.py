"""
PhoenixVoiceEngine
Tonic Evidence Fusion V1.0

Combines independent tonic evidence sources.

IMPORTANT:
This module is evidence-only.
It does NOT make a tonic, jins, or maqam decision.
It does NOT modify source pitch, timing, or performance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicEvidenceFusion:
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

    # ---------------------------------------------------------------
    # IO
    # ---------------------------------------------------------------

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

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------

    @classmethod
    def _name(cls, pitch_class: int) -> str:
        return cls.NOTE_NAMES[int(pitch_class) % 12]

    @staticmethod
    def _clamp(value: Any) -> float:
        try:
            value = float(value)
        except (TypeError, ValueError):
            return 0.0

        return max(0.0, min(1.0, value))

    @staticmethod
    def _get_candidate(
        data: Dict[str, Any],
        tonic: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Find a candidate record for a tonic pitch class.
        """

        candidates = []

        ranking = data.get("ranking")

        if isinstance(ranking, dict):
            candidates = ranking.get("candidates", [])

        if not candidates:
            evidence = data.get("evidence")

            if isinstance(evidence, dict):
                candidates = evidence.get(
                    "candidate_cadential_evidence",
                    [],
                )

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            pc = candidate.get("tonic_pitch_class")

            if pc is None:
                continue

            try:
                if int(pc) % 12 == int(tonic) % 12:
                    return candidate
            except (TypeError, ValueError):
                continue

        return None

    # ---------------------------------------------------------------
    # Functional evidence
    # ---------------------------------------------------------------

    def _functional_score(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> float:

        candidate = self._get_candidate(
            data,
            tonic,
        )

        if not candidate:
            return 0.0

        return self._clamp(
            candidate.get("score", 0.0)
        )

    # ---------------------------------------------------------------
    # Cadential context evidence
    # ---------------------------------------------------------------

    def _cadential_score(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> float:

        candidate = self._get_candidate(
            data,
            tonic,
        )

        if not candidate:
            return 0.0

        return self._clamp(
            candidate.get(
                "cadential_context_score",
                0.0,
            )
        )

    # ---------------------------------------------------------------
    # Stable center evidence
    # ---------------------------------------------------------------

    def _stable_center_score(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> float:

        centers = (
            data.get("evidence", {})
            .get("stable_pitch_centers", [])
        )

        for center in centers:

            if not isinstance(center, dict):
                continue

            try:
                pc = int(
                    center.get("pitch_class")
                ) % 12
            except (TypeError, ValueError):
                continue

            if pc != int(tonic) % 12:
                continue

            # Duration is useful, but stability itself is
            # also important. We deliberately keep this
            # component independent from cadence.
            duration = self._clamp(
                float(
                    center.get(
                        "total_duration",
                        0.0,
                    )
                ) / 60.0
            )

            stability = self._clamp(
                center.get(
                    "mean_stability_score",
                    0.0,
                )
            )

            return self._clamp(
                0.60 * stability
                + 0.40 * duration
            )

        return 0.0

    # ---------------------------------------------------------------
    # Raw microtonal evidence
    # ---------------------------------------------------------------

    def _microtonal_score(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> float:

        evidence = data.get("evidence", {})

        microtonal = evidence.get(
            "microtonal",
            {},
        )

        if not microtonal.get(
            "available",
            False,
        ):
            return 0.0

        nontrivial_ratio = self._clamp(
            microtonal.get(
                "nontrivial_cents_ratio",
                0.0,
            )
        )

        # The raw pitch analyzer provides evidence
        # of microtonal behavior, but it does not by
        # itself identify the tonic.
        #
        # Therefore this component is intentionally
        # conservative and acts as supporting evidence.
        return self._clamp(
            nontrivial_ratio
        )

    # ---------------------------------------------------------------
    # Raw tonic-relative evidence
    # ---------------------------------------------------------------

    def _tonic_relative_score(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> float:

        evidence = data.get("evidence", {})

        relative = evidence.get(
            "tonic_relative",
            {},
        )

        if not relative.get(
            "available",
            False,
        ):
            return 0.0

        bins = relative.get(
            "bins_25_cents",
            {},
        )

        if not isinstance(bins, dict):
            return 0.0

        # The analyzer receives a candidate tonic externally.
        # Relative bin evidence is therefore treated as
        # supporting evidence, never as a tonic decision.
        #
        # Concentration around 0 cents is the most direct
        # observable relation to the supplied candidate tonic.
        center = 0.0

        try:
            zero = float(
                bins.get("0.00", 0.0)
            )
        except (TypeError, ValueError):
            zero = 0.0

        nearby = 0.0

        for key, value in bins.items():
            try:
                offset = float(key)
                weight = float(value)
            except (TypeError, ValueError):
                continue

            distance = min(
                abs(offset),
                abs(offset - 12.0),
                abs(offset + 12.0),
            )

            if distance <= 0.50:
                nearby += weight

        return self._clamp(
            0.50 * zero
            + 0.50 * nearby
        )

    # ---------------------------------------------------------------
    # Fusion
    # ---------------------------------------------------------------

    def _fuse_candidate(
        self,
        tonic: int,
        functional: float,
        cadential: float,
        stable_center: float,
        microtonal: float,
        tonic_relative: float,
    ) -> Dict[str, Any]:

        # -----------------------------------------------------------
        # Weight design
        #
        # Functional + cadence receive the strongest influence
        # because they describe musical function.
        #
        # Stable center is supporting evidence.
        #
        # Raw microtonal / relative evidence is deliberately weaker.
        # -----------------------------------------------------------

        fused_score = (
            0.30 * functional
            + 0.30 * cadential
            + 0.20 * stable_center
            + 0.10 * microtonal
            + 0.10 * tonic_relative
        )

        fused_score = round(
            self._clamp(fused_score),
            6,
        )

        return {
            "tonic_pitch_class": int(tonic) % 12,
            "tonic_name": self._name(tonic),

            "fused_score": fused_score,

            "components": {
                "functional": round(
                    functional,
                    6,
                ),
                "cadential": round(
                    cadential,
                    6,
                ),
                "stable_center": round(
                    stable_center,
                    6,
                ),
                "microtonal": round(
                    microtonal,
                    6,
                ),
                "tonic_relative": round(
                    tonic_relative,
                    6,
                ),
            },

            "evidence_only": True,
        }

    # ---------------------------------------------------------------
    # Main analysis
    # ---------------------------------------------------------------

    def analyze(
        self,
        functional_data: Dict[str, Any],
        cadential_data: Dict[str, Any],
        stable_data: Dict[str, Any],
        raw_pitch_data: Dict[str, Any],
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        candidates = [
            int(x) % 12
            for x in (
                candidates
                or [7, 0]
            )
        ]

        ranking = []

        for tonic in candidates:

            functional = (
                self._functional_score(
                    functional_data,
                    tonic,
                )
            )

            cadential = (
                self._cadential_score(
                    cadential_data,
                    tonic,
                )
            )

            stable_center = (
                self._stable_center_score(
                    stable_data,
                    tonic,
                )
            )

            microtonal = (
                self._microtonal_score(
                    raw_pitch_data,
                    tonic,
                )
            )

            tonic_relative = (
                self._tonic_relative_score(
                    raw_pitch_data,
                    tonic,
                )
            )

            candidate = self._fuse_candidate(
                tonic=tonic,
                functional=functional,
                cadential=cadential,
                stable_center=stable_center,
                microtonal=microtonal,
                tonic_relative=tonic_relative,
            )

            ranking.append(candidate)

        ranking.sort(
            key=lambda x: x["fused_score"],
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
                top["fused_score"]
                - second["fused_score"],
                6,
            )
            if top and second
            else 0.0
        )

        # -----------------------------------------------------------
        # IMPORTANT:
        #
        # Never convert this ranking into a tonic decision here.
        # -----------------------------------------------------------

        return {
            "version": self.VERSION,

            "feature_version": (
                self.FEATURE_VERSION
            ),

            "patch_version": (
                self.PATCH_VERSION
            ),

            "input": {
                "candidate_pitch_classes": candidates,
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
                    "TONIC_EVIDENCE_FUSION_ONLY"
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

    # ---------------------------------------------------------------
    # File analysis
    # ---------------------------------------------------------------

    def analyze_files(
        self,
        functional_path: str,
        cadential_path: str,
        stable_path: str,
        raw_pitch_path: str,
        output_path: str,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        functional_data = self._load(
            functional_path
        )

        cadential_data = self._load(
            cadential_path
        )

        stable_data = self._load(
            stable_path
        )

        raw_pitch_data = self._load(
            raw_pitch_path
        )

        result = self.analyze(
            functional_data=functional_data,
            cadential_data=cadential_data,
            stable_data=stable_data,
            raw_pitch_data=raw_pitch_data,
            candidates=candidates,
        )

        self._save(
            output_path,
            result,
        )

        return result