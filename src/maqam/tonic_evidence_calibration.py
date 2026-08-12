"""
PhoenixVoiceEngine
Tonic Evidence Calibration V1.0

Purpose
-------
Analyze agreement and conflict between tonic evidence components.

Evidence-only layer.

This module MUST NOT:
- modify source pitch
- modify source timing
- modify source performance
- make a tonic decision
- make a maqam decision
- make a jins decision
- modify original fusion scores
- overwrite original evidence

Input
-----
Tonic Evidence Fusion V1.1 JSON.

Evidence components:
    functional
    cadential
    stable_center
    microtonal
    tonic_relative
    intervallic_relationship
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicEvidenceCalibration:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    COMPONENTS = (
        "functional",
        "cadential",
        "stable_center",
        "microtonal",
        "tonic_relative",
        "intervallic_relationship",
    )

    # ---------------------------------------------------------
    # Calibration constants
    # ---------------------------------------------------------

    # Difference required to classify one evidence component
    # as meaningful opposition.
    OPPOSITION_THRESHOLD = 0.05

    # Difference used to classify a component as a strong
    # directional preference.
    STRONG_DIRECTION_THRESHOLD = 0.05

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
    # Safe helpers
    # ---------------------------------------------------------

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
    # Ranking extraction
    # ---------------------------------------------------------

    def _extract_candidates(
        self,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        ranking = data.get(
            "ranking",
            {},
        )

        candidates = ranking.get(
            "candidates",
            [],
        )

        if not isinstance(
            candidates,
            list,
        ):
            return []

        return candidates

    # ---------------------------------------------------------
    # Component extraction
    # ---------------------------------------------------------

    def _extract_components(
        self,
        candidate: Dict[str, Any],
    ) -> Dict[str, float]:

        components = candidate.get(
            "components",
            {},
        )

        if not isinstance(
            components,
            dict,
        ):
            components = {}

        result: Dict[str, float] = {}

        for name in self.COMPONENTS:
            result[name] = self._clamp(
                self._safe_float(
                    components.get(
                        name,
                        0.0,
                    )
                )
            )

        return result

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    @staticmethod
    def _mean(
        values: List[float],
    ) -> float:

        if not values:
            return 0.0

        return sum(values) / len(
            values
        )

    @staticmethod
    def _std(
        values: List[float],
    ) -> float:

        if len(values) <= 1:
            return 0.0

        mean = sum(values) / len(
            values
        )

        variance = sum(
            (value - mean) ** 2
            for value in values
        ) / len(values)

        return math.sqrt(
            variance
        )

    # ---------------------------------------------------------
    # Pair components
    # ---------------------------------------------------------

    def _pair_components(
        self,
        first: Dict[str, Any],
        second: Dict[str, Any],
    ) -> Dict[str, Dict[str, float]]:

        first_components = (
            self._extract_components(
                first
            )
        )

        second_components = (
            self._extract_components(
                second
            )
        )

        result = {}

        for name in self.COMPONENTS:

            first_score = first_components[
                name
            ]

            second_score = second_components[
                name
            ]

            result[name] = {
                "first": first_score,
                "second": second_score,
                "difference": (
                    second_score
                    - first_score
                ),
                "absolute_difference": abs(
                    second_score
                    - first_score
                ),
            }

        return result

    # ---------------------------------------------------------
    # Supporting evidence
    #
    # IMPORTANT:
    # Support is RELATIVE between candidates.
    #
    # Example:
    #
    # G = 0.400760
    # C = 0.369567
    #
    # Functional evidence supports G,
    # despite both absolute scores being below 0.50.
    # ---------------------------------------------------------

    def _supporting_evidence(
        self,
        first: Dict[str, Any],
        second: Dict[str, Any],
    ) -> Dict[str, List[str]]:

        pair = self._pair_components(
            first,
            second,
        )

        first_support: List[str] = []
        second_support: List[str] = []

        for name, values in pair.items():

            first_score = values[
                "first"
            ]

            second_score = values[
                "second"
            ]

            if first_score > second_score:

                first_support.append(
                    name
                )

            elif second_score > first_score:

                second_support.append(
                    name
                )

        return {
            "first": first_support,
            "second": second_support,
        }

    # ---------------------------------------------------------
    # Opposing evidence
    #
    # Opposition is directional and requires
    # a meaningful difference.
    # ---------------------------------------------------------

    def _opposing_evidence(
        self,
        first: Dict[str, Any],
        second: Dict[str, Any],
    ) -> Dict[str, List[str]]:

        pair = self._pair_components(
            first,
            second,
        )

        first_opposed: List[str] = []
        second_opposed: List[str] = []

        for name, values in pair.items():

            difference = values[
                "difference"
            ]

            # second > first by threshold:
            # this opposes the first candidate.
            if (
                difference
                >= self.OPPOSITION_THRESHOLD
            ):

                first_opposed.append(
                    name
                )

            # first > second by threshold:
            # this opposes the second candidate.
            elif (
                difference
                <= -self.OPPOSITION_THRESHOLD
            ):

                second_opposed.append(
                    name
                )

        return {
            "first": first_opposed,
            "second": second_opposed,
        }

    # ---------------------------------------------------------
    # Agreement
    #
    # Agreement measures how similar the component
    # scores are between two tonic candidates.
    #
    # High agreement:
    # components behave similarly.
    #
    # Low agreement:
    # components separate the candidates strongly.
    # ---------------------------------------------------------

    def _agreement_score(
        self,
        first: Dict[str, Any],
        second: Dict[str, Any],
    ) -> float:

        pair = self._pair_components(
            first,
            second,
        )

        if not pair:
            return 0.0

        differences = [
            values[
                "absolute_difference"
            ]
            for values in pair.values()
        ]

        mean_difference = (
            self._mean(
                differences
            )
        )

        agreement = (
            1.0
            - mean_difference
        )

        return self._clamp(
            agreement
        )

    # ---------------------------------------------------------
    # Conflict
    #
    # Conflict measures the average directional
    # separation between candidates.
    # ---------------------------------------------------------

    def _conflict_score(
        self,
        first: Dict[str, Any],
        second: Dict[str, Any],
    ) -> float:

        pair = self._pair_components(
            first,
            second,
        )

        if not pair:
            return 0.0

        differences = [
            values[
                "absolute_difference"
            ]
            for values in pair.values()
        ]

        return self._clamp(
            self._mean(
                differences
            )
        )

    # ---------------------------------------------------------
    # Evidence spread
    # ---------------------------------------------------------

    def _evidence_spread(
        self,
        candidate: Dict[str, Any],
    ) -> float:

        components = (
            self._extract_components(
                candidate
            )
        )

        values = list(
            components.values()
        )

        if not values:
            return 0.0

        return self._clamp(
            max(values)
            - min(values)
        )

    # ---------------------------------------------------------
    # Candidate statistics
    # ---------------------------------------------------------

    def _candidate_statistics(
        self,
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:

        components = (
            self._extract_components(
                candidate
            )
        )

        values = list(
            components.values()
        )

        mean = self._mean(
            values
        )

        std = self._std(
            values
        )

        spread = (
            max(values)
            - min(values)
            if values
            else 0.0
        )

        if components:

            strongest = max(
                components.items(),
                key=lambda item: item[1],
            )

            weakest = min(
                components.items(),
                key=lambda item: item[1],
            )

        else:

            strongest = (
                None,
                0.0,
            )

            weakest = (
                None,
                0.0,
            )

        return {
            "evidence_mean": round(
                mean,
                6,
            ),

            "evidence_std": round(
                std,
                6,
            ),

            "evidence_spread": round(
                spread,
                6,
            ),

            "strongest_evidence": {
                "component": strongest[0],
                "score": round(
                    strongest[1],
                    6,
                ),
            },

            "weakest_evidence": {
                "component": weakest[0],
                "score": round(
                    weakest[1],
                    6,
                ),
            },
        }

    # ---------------------------------------------------------
    # Pair calibration
    # ---------------------------------------------------------

    def _calibrate_pair(
        self,
        first: Dict[str, Any],
        second: Dict[str, Any],
    ) -> Dict[str, Any]:

        first_name = first.get(
            "tonic_name",
            self._pitch_name(
                first.get(
                    "tonic_pitch_class",
                    0,
                )
            ),
        )

        second_name = second.get(
            "tonic_name",
            self._pitch_name(
                second.get(
                    "tonic_pitch_class",
                    0,
                )
            ),
        )

        pair = self._pair_components(
            first,
            second,
        )

        supporting = (
            self._supporting_evidence(
                first,
                second,
            )
        )

        opposing = (
            self._opposing_evidence(
                first,
                second,
            )
        )

        agreement = (
            self._agreement_score(
                first,
                second,
            )
        )

        conflict = (
            self._conflict_score(
                first,
                second,
            )
        )

        directional = {}

        for name, values in pair.items():

            difference = values[
                "difference"
            ]

            if difference > 0:

                preferred = second_name

            elif difference < 0:

                preferred = first_name

            else:

                preferred = "TIE"

            directional[name] = {
                "preferred_tonic": preferred,
                "difference": round(
                    difference,
                    6,
                ),
                "absolute_difference": round(
                    abs(difference),
                    6,
                ),
                "strong_direction": (
                    abs(difference)
                    >= self.STRONG_DIRECTION_THRESHOLD
                ),
            }

        return {
            "first_tonic": first_name,

            "second_tonic": second_name,

            "supporting_evidence": {
                first_name: supporting[
                    "first"
                ],
                second_name: supporting[
                    "second"
                ],
            },

            "opposing_evidence": {
                first_name: opposing[
                    "first"
                ],
                second_name: opposing[
                    "second"
                ],
            },

            "agreement_score": round(
                agreement,
                6,
            ),

            "conflict_score": round(
                conflict,
                6,
            ),

            "directional_evidence": (
                directional
            ),

            "summary": {
                "first_support_count": len(
                    supporting[
                        "first"
                    ]
                ),

                "second_support_count": len(
                    supporting[
                        "second"
                    ]
                ),

                "first_opposition_count": len(
                    opposing[
                        "first"
                    ]
                ),

                "second_opposition_count": len(
                    opposing[
                        "second"
                    ]
                ),
            },
        }

    # ---------------------------------------------------------
    # Main analysis
    # ---------------------------------------------------------

    def analyze(
        self,
        fusion_data: Dict[str, Any],
        candidates: Optional[
            List[int]
        ] = None,
    ) -> Dict[str, Any]:

        available = (
            self._extract_candidates(
                fusion_data
            )
        )

        # -----------------------------------------------------
        # Select requested candidates.
        # -----------------------------------------------------

        if candidates is None:

            selected = list(
                available
            )

        else:

            candidate_set = {
                int(value) % 12
                for value in candidates
            }

            selected = [
                item
                for item in available
                if int(
                    item.get(
                        "tonic_pitch_class",
                        -1,
                    )
                ) % 12
                in candidate_set
            ]

        # -----------------------------------------------------
        # Add missing requested candidates.
        #
        # No evidence is invented.
        # -----------------------------------------------------

        existing = {
            int(
                item.get(
                    "tonic_pitch_class",
                    -1,
                )
            ) % 12
            for item in selected
        }

        if candidates is not None:

            for tonic in candidates:

                tonic = int(
                    tonic
                ) % 12

                if tonic not in existing:

                    selected.append(
                        {
                            "tonic_pitch_class": (
                                tonic
                            ),

                            "tonic_name": (
                                self._pitch_name(
                                    tonic
                                )
                            ),

                            "fused_score": 0.0,

                            "components": {
                                component: 0.0
                                for component in (
                                    self.COMPONENTS
                                )
                            },

                            "evidence_only": True,
                        }
                    )

        # -----------------------------------------------------
        # Individual candidate calibration.
        # -----------------------------------------------------

        calibrated_candidates = []

        for candidate in selected:

            pitch_class = int(
                candidate.get(
                    "tonic_pitch_class",
                    0,
                )
            ) % 12

            components = (
                self._extract_components(
                    candidate
                )
            )

            statistics = (
                self._candidate_statistics(
                    candidate
                )
            )

            calibrated_candidates.append(
                {
                    "tonic_pitch_class": (
                        pitch_class
                    ),

                    "tonic_name": candidate.get(
                        "tonic_name",
                        self._pitch_name(
                            pitch_class
                        ),
                    ),

                    # Preserve original fusion score.
                    "original_fused_score": (
                        self._clamp(
                            self._safe_float(
                                candidate.get(
                                    "fused_score",
                                    0.0,
                                )
                            )
                        )
                    ),

                    # Preserve original component values.
                    "components": components,

                    "evidence_mean": (
                        statistics[
                            "evidence_mean"
                        ]
                    ),

                    "evidence_std": (
                        statistics[
                            "evidence_std"
                        ]
                    ),

                    "evidence_spread": (
                        statistics[
                            "evidence_spread"
                        ]
                    ),

                    "strongest_evidence": (
                        statistics[
                            "strongest_evidence"
                        ]
                    ),

                    "weakest_evidence": (
                        statistics[
                            "weakest_evidence"
                        ]
                    ),

                    "evidence_only": True,
                }
            )

        # -----------------------------------------------------
        # Preserve original ranking order.
        # -----------------------------------------------------

        calibrated_candidates.sort(
            key=lambda item: item[
                "original_fused_score"
            ],
            reverse=True,
        )

        top = (
            calibrated_candidates[0]
            if calibrated_candidates
            else None
        )

        second = (
            calibrated_candidates[1]
            if len(
                calibrated_candidates
            ) > 1
            else None
        )

        # -----------------------------------------------------
        # Pair calibration.
        # -----------------------------------------------------

        pair_calibration = None

        if (
            top is not None
            and second is not None
        ):

            pair_calibration = (
                self._calibrate_pair(
                    top,
                    second,
                )
            )

        # -----------------------------------------------------
        # Evidence group preferences.
        # -----------------------------------------------------

        group_preferences = {}

        if (
            top is not None
            and second is not None
        ):

            for component in (
                self.COMPONENTS
            ):

                top_score = top[
                    "components"
                ][component]

                second_score = second[
                    "components"
                ][component]

                difference = (
                    second_score
                    - top_score
                )

                if top_score > second_score:

                    preferred = top[
                        "tonic_name"
                    ]

                elif second_score > top_score:

                    preferred = second[
                        "tonic_name"
                    ]

                else:

                    preferred = "TIE"

                group_preferences[
                    component
                ] = {
                    "preferred_tonic": (
                        preferred
                    ),

                    "top_score": round(
                        top_score,
                        6,
                    ),

                    "second_score": round(
                        second_score,
                        6,
                    ),

                    "difference": round(
                        difference,
                        6,
                    ),

                    "absolute_difference": round(
                        abs(difference),
                        6,
                    ),

                    "meaningful_difference": (
                        abs(difference)
                        >= self.OPPOSITION_THRESHOLD
                    ),
                }

        # -----------------------------------------------------
        # Original fusion margin.
        # -----------------------------------------------------

        margin = 0.0

        if (
            top is not None
            and second is not None
        ):

            margin = round(
                top[
                    "original_fused_score"
                ]
                - second[
                    "original_fused_score"
                ],
                6,
            )

        # -----------------------------------------------------
        # Protection metadata.
        # -----------------------------------------------------

        protection = {
            "source_pitch_modified": False,

            "source_timing_modified": False,

            "source_performance_modified": False,

            "tonic_decision_made": False,

            "maqam_decision_made": False,

            "jins_decision_made": False,

            "source_scores_modified": False,

            "original_scores_preserved": True,
        }

        # -----------------------------------------------------
        # Final evidence-only result.
        # -----------------------------------------------------

        return {
            "version": self.VERSION,

            "feature_version": (
                self.FEATURE_VERSION
            ),

            "patch_version": (
                self.PATCH_VERSION
            ),

            "calibration_version": (
                "V1.0"
            ),

            "input": {
                "source_status": (
                    fusion_data.get(
                        "decision",
                        {},
                    ).get(
                        "status"
                    )
                ),

                "candidate_count": len(
                    calibrated_candidates
                ),

                "component_names": list(
                    self.COMPONENTS
                ),
            },

            "ranking": {
                "candidates": (
                    calibrated_candidates
                ),

                "top": top,

                "second": second,

                "margin": margin,
            },

            "pair_calibration": (
                pair_calibration
            ),

            "group_preferences": (
                group_preferences
            ),

            "decision": {
                "status": (
                    "EVIDENCE_ONLY"
                ),

                "tonic_pitch_class": None,

                "tonic_name": None,

                "maqam": None,

                "jins": None,

                "confidence": None,

                "reason": [
                    "TONIC_EVIDENCE_CALIBRATION_ONLY",
                    "EVIDENCE_CONFLICT_ANALYSIS",
                    "NO_TONIC_DECISION",
                ],
            },

            "protection": protection,
        }

    # ---------------------------------------------------------
    # File API
    # ---------------------------------------------------------

    def analyze_file(
        self,
        fusion_path: str,
        output_path: str,
        candidates: Optional[
            List[int]
        ] = None,
    ) -> Dict[str, Any]:

        fusion_data = self._load(
            fusion_path
        )

        result = self.analyze(
            fusion_data,
            candidates=candidates,
        )

        self._save(
            output_path,
            result,
        )

        return result


# -------------------------------------------------------------
# CLI
# -------------------------------------------------------------

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PhoenixVoiceEngine "
            "Tonic Evidence Calibration V1.0"
        )
    )

    parser.add_argument(
        "fusion_path",
        help=(
            "Path to Tonic Evidence "
            "Fusion JSON"
        ),
    )

    parser.add_argument(
        "output_path",
        help=(
            "Output calibration JSON path"
        ),
    )

    parser.add_argument(
        "--candidates",
        nargs="+",
        type=int,
        default=None,
        help=(
            "Optional tonic pitch-class "
            "candidates"
        ),
    )

    args = parser.parse_args()

    analyzer = (
        TonicEvidenceCalibration()
    )

    result = analyzer.analyze_file(
        args.fusion_path,
        args.output_path,
        candidates=args.candidates,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )