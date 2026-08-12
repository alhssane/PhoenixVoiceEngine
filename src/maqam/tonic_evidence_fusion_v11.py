"""
PhoenixVoiceEngine
Tonic Evidence Fusion V1.1

Purpose
-------
Fuse previously generated tonic evidence with the new
Tonic Intervallic Relationship evidence.

IMPORTANT:
- Evidence only.
- No tonic decision.
- No maqam decision.
- No jins decision.
- No source pitch correction.
- No source timing correction.
- No performance modification.
- Original V1.0 scores are preserved as inputs.
- The new intervallic evidence is added as an independent component.

V1.1 adds:
    intervallic_relationship

V1.0 components preserved:
    functional
    cadential
    stable_center
    microtonal
    tonic_relative
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicEvidenceFusionV11:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.1.0"

    # ---------------------------------------------------------
    # Fusion weights
    # ---------------------------------------------------------

    WEIGHTS = {
        "functional": 0.20,
        "cadential": 0.20,
        "stable_center": 0.15,
        "microtonal": 0.10,
        "tonic_relative": 0.10,
        "intervallic_relationship": 0.25,
    }

    # ---------------------------------------------------------
    # IO
    # ---------------------------------------------------------

    @staticmethod
    def _load(path: str) -> Dict[str, Any]:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)

    @staticmethod
    def _save(
        path: str,
        data: Dict[str, Any],
    ) -> None:
        output = Path(path)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            output,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:
        return max(
            minimum,
            min(
                maximum,
                float(value),
            ),
        )

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        try:
            return float(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    @staticmethod
    def _safe_int(
        value: Any,
        default: int = 0,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return default

    # ---------------------------------------------------------
    # Candidate extraction
    # ---------------------------------------------------------

    def _extract_functional(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> float:
        ranking = (
            data.get("ranking", {})
            .get("candidates", [])
        )

        for item in ranking:
            if (
                self._safe_int(
                    item.get(
                        "tonic_pitch_class"
                    )
                )
                == tonic
            ):
                return self._clamp(
                    self._safe_float(
                        item.get("score")
                    )
                )

        return 0.0

    def _extract_cadential(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> float:
        ranking = (
            data.get("ranking", {})
            .get("candidates", [])
        )

        for item in ranking:
            if (
                self._safe_int(
                    item.get(
                        "tonic_pitch_class"
                    )
                )
                == tonic
            ):
                return self._clamp(
                    self._safe_float(
                        item.get(
                            "cadential_context_score"
                        )
                    )
                )

        return 0.0

    # ---------------------------------------------------------
    # V1.0 fused components
    # ---------------------------------------------------------

    def _extract_original_components(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> Dict[str, float]:

        ranking = (
            data.get("ranking", {})
            .get("candidates", [])
        )

        for item in ranking:
            if (
                self._safe_int(
                    item.get(
                        "tonic_pitch_class"
                    )
                )
                == tonic
            ):

                components = item.get(
                    "components",
                    {},
                )

                return {
                    "functional": self._clamp(
                        self._safe_float(
                            components.get(
                                "functional"
                            )
                        )
                    ),
                    "cadential": self._clamp(
                        self._safe_float(
                            components.get(
                                "cadential"
                            )
                        )
                    ),
                    "stable_center": self._clamp(
                        self._safe_float(
                            components.get(
                                "stable_center"
                            )
                        )
                    ),
                    "microtonal": self._clamp(
                        self._safe_float(
                            components.get(
                                "microtonal"
                            )
                        )
                    ),
                    "tonic_relative": self._clamp(
                        self._safe_float(
                            components.get(
                                "tonic_relative"
                            )
                        )
                    ),
                }

        return {
            "functional": 0.0,
            "cadential": 0.0,
            "stable_center": 0.0,
            "microtonal": 0.0,
            "tonic_relative": 0.0,
        }

    # ---------------------------------------------------------
    # Stable center extraction
    # ---------------------------------------------------------

    def _extract_stable_center_score(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> float:

        centers = (
            data.get("evidence", {})
            .get(
                "stable_pitch_centers",
                [],
            )
        )

        if not centers:
            return 0.0

        total_duration = 0.0
        tonic_duration = 0.0

        weighted_stability = 0.0
        stability_weight = 0.0

        for center in centers:
            pc = self._safe_int(
                center.get(
                    "pitch_class"
                ),
                -1,
            )

            duration = max(
                0.0,
                self._safe_float(
                    center.get(
                        "total_duration"
                    )
                ),
            )

            stability = self._clamp(
                self._safe_float(
                    center.get(
                        "mean_stability_score"
                    )
                )
            )

            total_duration += duration

            if pc == tonic:
                tonic_duration += duration

                weighted_stability += (
                    duration
                    * stability
                )

                stability_weight += duration

        if total_duration <= 0:
            return 0.0

        duration_share = (
            tonic_duration
            / total_duration
        )

        stability = (
            weighted_stability
            / stability_weight
            if stability_weight > 0
            else 0.0
        )

        # Same conservative principle used by
        # the V1.0 evidence fusion:
        # combine tonic duration presence
        # with observed stability.
        score = (
            0.55
            * self._clamp(
                duration_share * 3.0
            )
            + 0.45
            * stability
        )

        return self._clamp(score)

    # ---------------------------------------------------------
    # Microtonal evidence
    # ---------------------------------------------------------

    def _extract_microtonal_score(
        self,
        data: Dict[str, Any],
    ) -> float:

        microtonal = (
            data.get("evidence", {})
            .get(
                "microtonal",
                {},
            )
        )

        if not microtonal.get(
            "available",
            False,
        ):
            return 0.0

        # Preserve the existing global
        # microtonal evidence value when available.
        ratio = self._safe_float(
            microtonal.get(
                "nontrivial_cents_ratio"
            )
        )

        return self._clamp(ratio)

    # ---------------------------------------------------------
    # Tonic-relative evidence
    # ---------------------------------------------------------

    def _extract_relative_score(
        self,
        data: Dict[str, Any],
    ) -> float:

        relative = (
            data.get("evidence", {})
            .get(
                "tonic_relative",
                {},
            )
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

        if not isinstance(
            bins,
            dict,
        ) or not bins:
            return 0.0

        # Preserve the descriptive nature of this
        # evidence. We use concentration around the
        # tonic-relative grid rather than making a
        # maqam/tonic decision.
        values = []

        for value in bins.values():
            values.append(
                self._safe_float(value)
            )

        if not values:
            return 0.0

        maximum = max(values)

        # Normalize concentration.
        score = self._clamp(
            maximum * 4.0
        )

        return score

    # ---------------------------------------------------------
    # Intervallic relationship evidence
    # ---------------------------------------------------------

    def _extract_intervallic(
        self,
        data: Dict[str, Any],
        tonic: int,
    ) -> Dict[str, Any]:

        ranking = (
            data.get("ranking", {})
            .get("candidates", [])
        )

        for item in ranking:
            if (
                self._safe_int(
                    item.get(
                        "tonic_pitch_class"
                    )
                )
                == tonic
            ):

                score = self._clamp(
                    self._safe_float(
                        item.get(
                            "score"
                        )
                    )
                )

                components = item.get(
                    "components",
                    {},
                )

                return {
                    "score": score,
                    "components": {
                        "pitch_recurrence": (
                            self._clamp(
                                self._safe_float(
                                    components.get(
                                        "pitch_recurrence"
                                    )
                                )
                            )
                        ),
                        "tonic_transition": (
                            self._clamp(
                                self._safe_float(
                                    components.get(
                                        "tonic_transition"
                                    )
                                )
                            )
                        ),
                        "stable_center_coverage": (
                            self._clamp(
                                self._safe_float(
                                    components.get(
                                        "stable_center_coverage"
                                    )
                                )
                            )
                        ),
                        "relationship_availability": (
                            self._clamp(
                                self._safe_float(
                                    components.get(
                                        "relationship_availability"
                                    )
                                )
                            )
                        ),
                    },
                }

        return {
            "score": 0.0,
            "components": {
                "pitch_recurrence": 0.0,
                "tonic_transition": 0.0,
                "stable_center_coverage": 0.0,
                "relationship_availability": 0.0,
            },
        }

    # ---------------------------------------------------------
    # Fusion
    # ---------------------------------------------------------

    def _fuse_candidate(
        self,
        tonic: int,
        original_components: Dict[str, float],
        intervallic: Dict[str, Any],
    ) -> Dict[str, Any]:

        intervallic_score = self._clamp(
            intervallic.get(
                "score",
                0.0,
            )
        )

        fused_score = (
            self.WEIGHTS["functional"]
            * original_components[
                "functional"
            ]
            + self.WEIGHTS["cadential"]
            * original_components[
                "cadential"
            ]
            + self.WEIGHTS["stable_center"]
            * original_components[
                "stable_center"
            ]
            + self.WEIGHTS["microtonal"]
            * original_components[
                "microtonal"
            ]
            + self.WEIGHTS["tonic_relative"]
            * original_components[
                "tonic_relative"
            ]
            + self.WEIGHTS[
                "intervallic_relationship"
            ]
            * intervallic_score
        )

        fused_score = self._clamp(
            fused_score
        )

        return {
            "tonic_pitch_class": tonic,
            "tonic_name": (
                TonicEvidenceFusionV11
                ._pitch_name(tonic)
            ),
            "fused_score": round(
                fused_score,
                6,
            ),

            "components": {
                "functional": round(
                    original_components[
                        "functional"
                    ],
                    6,
                ),
                "cadential": round(
                    original_components[
                        "cadential"
                    ],
                    6,
                ),
                "stable_center": round(
                    original_components[
                        "stable_center"
                    ],
                    6,
                ),
                "microtonal": round(
                    original_components[
                        "microtonal"
                    ],
                    6,
                ),
                "tonic_relative": round(
                    original_components[
                        "tonic_relative"
                    ],
                    6,
                ),
                "intervallic_relationship": round(
                    intervallic_score,
                    6,
                ),
            },

            "intervallic_detail": (
                intervallic.get(
                    "components",
                    {},
                )
            ),

            "evidence_only": True,
        }

    # ---------------------------------------------------------
    # Pitch names
    # ---------------------------------------------------------

    @staticmethod
    def _pitch_name(
        pitch_class: int,
    ) -> str:
        names = (
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

        return names[
            int(pitch_class) % 12
        ]

    # ---------------------------------------------------------
    # Main analysis
    # ---------------------------------------------------------

    def analyze(
        self,
        functional_data: Dict[str, Any],
        cadential_data: Dict[str, Any],
        stable_data: Dict[str, Any],
        raw_pitch_data: Dict[str, Any],
        original_fusion_data: Dict[str, Any],
        intervallic_data: Dict[str, Any],
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

        ranking = []

        for tonic in candidates:

            original_components = (
                self._extract_original_components(
                    original_fusion_data,
                    tonic,
                )
            )

            intervallic = (
                self._extract_intervallic(
                    intervallic_data,
                    tonic,
                )
            )

            candidate = self._fuse_candidate(
                tonic,
                original_components,
                intervallic,
            )

            ranking.append(
                candidate
            )

        ranking.sort(
            key=lambda x: x[
                "fused_score"
            ],
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

        # Preserve original V1.0 decision
        # state. This layer must never override
        # a previous ambiguity or make a tonic
        # decision.
        original_decision = (
            original_fusion_data.get(
                "decision",
                {},
            )
        )

        return {
            "version": self.VERSION,
            "feature_version": (
                self.FEATURE_VERSION
            ),
            "patch_version": (
                self.PATCH_VERSION
            ),

            "fusion_version": "V1.1",

            "weights": dict(
                self.WEIGHTS
            ),

            "input": {
                "candidate_pitch_classes": (
                    candidates
                ),
                "original_fusion_status": (
                    original_decision.get(
                        "status"
                    )
                ),
                "intervallic_status": (
                    intervallic_data.get(
                        "decision",
                        {},
                    ).get(
                        "status"
                    )
                ),
            },

            "original_v10": {
                "decision": original_decision,
                "ranking": original_fusion_data.get(
                    "ranking",
                    {},
                ),
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
                    "TONIC_EVIDENCE_FUSION_V11_ONLY",
                    "INTERVALLIC_RELATIONSHIP_ADDED",
                    "NO_TONIC_DECISION",
                ],
            },

            "protection": {
                "source_pitch_modified": False,
                "source_timing_modified": False,
                "source_performance_modified": False,

                "tonic_decision_made": False,
                "maqam_decision_made": False,
                "jins_decision_made": False,

                "original_v10_decision_overridden": False,

                "original_scores_preserved": True,
                "intervallic_evidence_added": True,
            },
        }

    # ---------------------------------------------------------
    # File API
    # ---------------------------------------------------------

    def analyze_files(
        self,
        functional_path: str,
        cadential_path: str,
        stable_path: str,
        raw_pitch_path: str,
        original_fusion_path: str,
        intervallic_path: str,
        output_path: str,
        candidates: Optional[
            List[int]
        ] = None,
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

        original_fusion_data = self._load(
            original_fusion_path
        )

        intervallic_data = self._load(
            intervallic_path
        )

        result = self.analyze(
            functional_data=functional_data,
            cadential_data=cadential_data,
            stable_data=stable_data,
            raw_pitch_data=raw_pitch_data,
            original_fusion_data=original_fusion_data,
            intervallic_data=intervallic_data,
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
        "functional_path"
    )

    parser.add_argument(
        "cadential_path"
    )

    parser.add_argument(
        "stable_path"
    )

    parser.add_argument(
        "raw_pitch_path"
    )

    parser.add_argument(
        "original_fusion_path"
    )

    parser.add_argument(
        "intervallic_path"
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
        TonicEvidenceFusionV11()
    )

    result = analyzer.analyze_files(
        functional_path=args.functional_path,
        cadential_path=args.cadential_path,
        stable_path=args.stable_path,
        raw_pitch_path=args.raw_pitch_path,
        original_fusion_path=(
            args.original_fusion_path
        ),
        intervallic_path=(
            args.intervallic_path
        ),
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