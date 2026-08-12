"""
PhoenixVoiceEngine
Tonic Evidence Reliability Analyzer V1.0

Purpose
-------
Estimate the reliability of each tonic-evidence component.

This is an evidence-quality layer.

It MUST NOT:
- modify source pitch
- modify source timing
- modify source performance
- make a tonic decision
- make a maqam decision
- make a jins decision
- overwrite fusion scores
- recalibrate the original evidence

Reliability dimensions
----------------------
1. Availability
2. Strength
3. Separation
4. Stability
5. Agreement
6. Conflict

Supported evidence components
-----------------------------
- functional
- cadential
- stable_center
- microtonal
- tonic_relative
- intervallic_relationship
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicEvidenceReliabilityAnalyzer:
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
    # Thresholds
    # ---------------------------------------------------------

    MIN_MEANINGFUL_SEPARATION = 0.05

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

    # ---------------------------------------------------------
    # Candidate extraction
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

        return {
            name: self._clamp(
                self._safe_float(
                    components.get(
                        name,
                        0.0,
                    )
                )
            )
            for name in self.COMPONENTS
        }

    # ---------------------------------------------------------
    # Candidate lookup
    # ---------------------------------------------------------

    def _candidate_by_pitch_class(
        self,
        candidates: List[Dict[str, Any]],
        pitch_class: int,
    ) -> Optional[Dict[str, Any]]:

        target = int(
            pitch_class
        ) % 12

        for candidate in candidates:

            try:
                pc = int(
                    candidate.get(
                        "tonic_pitch_class",
                        -1,
                    )
                ) % 12
            except (
                TypeError,
                ValueError,
            ):
                continue

            if pc == target:
                return candidate

        return None

    # ---------------------------------------------------------
    # Pairwise component separation
    # ---------------------------------------------------------

    def _component_separation(
        self,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:

        result = {}

        if len(candidates) < 2:

            for component in self.COMPONENTS:

                result[component] = {
                    "available": False,
                    "top_tonic": None,
                    "second_tonic": None,
                    "top_score": 0.0,
                    "second_score": 0.0,
                    "absolute_difference": 0.0,
                    "meaningful_separation": False,
                }

            return result

        first = candidates[0]
        second = candidates[1]

        first_name = first.get(
            "tonic_name",
        )

        second_name = second.get(
            "tonic_name",
        )

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

        for component in self.COMPONENTS:

            first_score = first_components[
                component
            ]

            second_score = second_components[
                component
            ]

            if first_score >= second_score:

                top_name = first_name
                top_score = first_score
                second_score_value = (
                    second_score
                )

            else:

                top_name = second_name
                top_score = second_score
                second_score_value = (
                    first_score
                )

            difference = abs(
                first_score
                - second_score
            )

            result[component] = {
                "available": True,
                "top_tonic": top_name,
                "second_tonic": (
                    second_name
                    if top_name == first_name
                    else first_name
                ),
                "top_score": round(
                    top_score,
                    6,
                ),
                "second_score": round(
                    second_score_value,
                    6,
                ),
                "absolute_difference": round(
                    difference,
                    6,
                ),
                "meaningful_separation": (
                    difference
                    >= self.MIN_MEANINGFUL_SEPARATION
                ),
            }

        return result

    # ---------------------------------------------------------
    # Availability
    # ---------------------------------------------------------

    def _availability_score(
        self,
        candidate_count: int,
        component_value: float,
    ) -> float:

        if candidate_count < 2:
            return 0.0

        # Presence of a component is considered available
        # when its value is explicitly present, even when
        # its numerical evidence is weak.
        #
        # The caller supplies a component value because
        # malformed/missing values are normalized to 0.
        if component_value > 0.0:
            return 1.0

        return 0.0

    # ---------------------------------------------------------
    # Strength
    # ---------------------------------------------------------

    def _strength_score(
        self,
        top_score: float,
        second_score: float,
    ) -> float:

        # Strength is based on the stronger observed evidence,
        # not on which tonic wins.
        return self._clamp(
            max(
                top_score,
                second_score,
            )
        )

    # ---------------------------------------------------------
    # Separation
    # ---------------------------------------------------------

    def _separation_score(
        self,
        first_score: float,
        second_score: float,
    ) -> float:

        return self._clamp(
            abs(
                first_score
                - second_score
            )
        )

    # ---------------------------------------------------------
    # Agreement
    #
    # Agreement means that this component behaves in the same
    # directional way as the majority of the evidence groups.
    # ---------------------------------------------------------

    def _agreement_score(
        self,
        component: str,
        component_preference: Optional[str],
        preferences: Dict[str, str],
    ) -> float:

        if not component_preference:
            return 0.0

        other_preferences = [
            value
            for name, value in preferences.items()
            if name != component
            and value not in (
                None,
                "TIE",
            )
        ]

        if not other_preferences:
            return 0.0

        matching = sum(
            1
            for value in other_preferences
            if value == component_preference
        )

        return self._clamp(
            matching
            / len(other_preferences)
        )

    # ---------------------------------------------------------
    # Conflict
    #
    # Conflict measures disagreement with the majority
    # direction of the other evidence groups.
    # ---------------------------------------------------------

    def _conflict_score(
        self,
        component: str,
        component_preference: Optional[str],
        preferences: Dict[str, str],
    ) -> float:

        if not component_preference:
            return 0.0

        other_preferences = [
            value
            for name, value in preferences.items()
            if name != component
            and value not in (
                None,
                "TIE",
            )
        ]

        if not other_preferences:
            return 0.0

        conflicts = sum(
            1
            for value in other_preferences
            if value != component_preference
        )

        return self._clamp(
            conflicts
            / len(other_preferences)
        )

    # ---------------------------------------------------------
    # Preference extraction
    # ---------------------------------------------------------

    def _component_preferences(
        self,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, str]:

        preferences: Dict[str, str] = {}

        if len(candidates) < 2:

            return {
                component: "TIE"
                for component in self.COMPONENTS
            }

        first = candidates[0]
        second = candidates[1]

        first_name = first.get(
            "tonic_name",
        )

        second_name = second.get(
            "tonic_name",
        )

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

        for component in self.COMPONENTS:

            first_score = first_components[
                component
            ]

            second_score = second_components[
                component
            ]

            if first_score > second_score:

                preferences[component] = (
                    first_name
                )

            elif second_score > first_score:

                preferences[component] = (
                    second_name
                )

            else:

                preferences[component] = "TIE"

        return preferences

    # ---------------------------------------------------------
    # Reliability
    # ---------------------------------------------------------

    def _reliability_score(
        self,
        availability: float,
        strength: float,
        separation: float,
        stability: float,
        agreement: float,
        conflict: float,
    ) -> float:

        # Reliability is deliberately conservative.
        #
        # Availability  : 15%
        # Strength      : 20%
        # Separation    : 20%
        # Stability     : 15%
        # Agreement     : 20%
        # Conflict      : 10% penalty

        value = (
            0.15 * availability
            + 0.20 * strength
            + 0.20 * separation
            + 0.15 * stability
            + 0.20 * agreement
            - 0.10 * conflict
        )

        return self._clamp(
            value
        )

    # ---------------------------------------------------------
    # Analyze
    # ---------------------------------------------------------

    def analyze(
        self,
        fusion_data: Dict[str, Any],
        calibration_data: Optional[
            Dict[str, Any]
        ] = None,
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
        # Candidate filtering
        # -----------------------------------------------------

        if candidates is None:

            selected = list(
                available
            )

        else:

            requested = {
                int(value) % 12
                for value in candidates
            }

            selected = [
                candidate
                for candidate in available
                if int(
                    candidate.get(
                        "tonic_pitch_class",
                        -1,
                    )
                ) % 12
                in requested
            ]

        # -----------------------------------------------------
        # Preserve original fusion ranking.
        # -----------------------------------------------------

        selected.sort(
            key=lambda item: self._safe_float(
                item.get(
                    "fused_score",
                    0.0,
                )
            ),
            reverse=True,
        )

        separation = (
            self._component_separation(
                selected
            )
        )

        preferences = (
            self._component_preferences(
                selected
            )
        )

        # -----------------------------------------------------
        # Build reliability records.
        # -----------------------------------------------------

        reliability = []

        candidate_count = len(
            selected
        )

        for component in self.COMPONENTS:

            component_info = separation[
                component
            ]

            top_score = self._safe_float(
                component_info.get(
                    "top_score",
                    0.0,
                )
            )

            second_score = self._safe_float(
                component_info.get(
                    "second_score",
                    0.0,
                )
            )

            separation_value = (
                self._separation_score(
                    top_score,
                    second_score,
                )
            )

            strength = (
                self._strength_score(
                    top_score,
                    second_score,
                )
            )

            availability = (
                1.0
                if component_info.get(
                    "available",
                    False,
                )
                else 0.0
            )

            preference = preferences.get(
                component,
                "TIE",
            )

            agreement = (
                self._agreement_score(
                    component,
                    preference,
                    preferences,
                )
            )

            conflict = (
                self._conflict_score(
                    component,
                    preference,
                    preferences,
                )
            )

            # V1.0 does not invent a temporal stability
            # measurement. If calibration contains an
            # evidence-spread measurement, use it only as
            # a conservative stability proxy.
            stability = 0.0

            if calibration_data:

                ranking = (
                    calibration_data.get(
                        "ranking",
                        {},
                    )
                )

                calibration_candidates = (
                    ranking.get(
                        "candidates",
                        [],
                    )
                )

                if isinstance(
                    calibration_candidates,
                    list,
                ):

                    spreads = []

                    for candidate in (
                        calibration_candidates
                    ):

                        components_data = (
                            candidate.get(
                                "components",
                                {},
                            )
                        )

                        if component in (
                            components_data
                            or {}
                        ):

                            spread = self._safe_float(
                                candidate.get(
                                    "evidence_spread",
                                    0.0,
                                )
                            )

                            spreads.append(
                                spread
                            )

                    if spreads:

                        # Smaller spread is treated as
                        # more internally stable.
                        average_spread = sum(
                            spreads
                        ) / len(spreads)

                        stability = self._clamp(
                            1.0
                            - average_spread
                        )

            reliability_score = (
                self._reliability_score(
                    availability=availability,
                    strength=strength,
                    separation=separation_value,
                    stability=stability,
                    agreement=agreement,
                    conflict=conflict,
                )
            )

            reliability.append(
                {
                    "component": component,

                    "reliability_score": round(
                        reliability_score,
                        6,
                    ),

                    "availability": round(
                        availability,
                        6,
                    ),

                    "strength": round(
                        strength,
                        6,
                    ),

                    "separation": round(
                        separation_value,
                        6,
                    ),

                    "stability": round(
                        stability,
                        6,
                    ),

                    "agreement": round(
                        agreement,
                        6,
                    ),

                    "conflict": round(
                        conflict,
                        6,
                    ),

                    "preferred_tonic": preference,

                    "top_tonic": (
                        component_info.get(
                            "top_tonic"
                        )
                    ),

                    "top_score": round(
                        top_score,
                        6,
                    ),

                    "second_score": round(
                        second_score,
                        6,
                    ),

                    "absolute_difference": round(
                        separation_value,
                        6,
                    ),

                    "meaningful_separation": (
                        component_info.get(
                            "meaningful_separation",
                            False,
                        )
                    ),

                    "evidence_only": True,
                }
            )

        # -----------------------------------------------------
        # Reliability ranking
        # -----------------------------------------------------

        reliability.sort(
            key=lambda item: item[
                "reliability_score"
            ],
            reverse=True,
        )

        # -----------------------------------------------------
        # Overall evidence reliability
        # -----------------------------------------------------

        reliability_values = [
            item[
                "reliability_score"
            ]
            for item in reliability
        ]

        if reliability_values:

            overall_reliability = (
                sum(
                    reliability_values
                )
                / len(
                    reliability_values
                )
            )

        else:

            overall_reliability = 0.0

        # -----------------------------------------------------
        # Strongest / weakest evidence
        # -----------------------------------------------------

        strongest = (
            reliability[0]
            if reliability
            else None
        )

        weakest = (
            reliability[-1]
            if reliability
            else None
        )

        # -----------------------------------------------------
        # Original decision is never overridden.
        # -----------------------------------------------------

        original_decision = (
            fusion_data.get(
                "decision",
                {},
            )
        )

        # -----------------------------------------------------
        # Final result
        # -----------------------------------------------------

        return {
            "version": self.VERSION,

            "feature_version": (
                self.FEATURE_VERSION
            ),

            "patch_version": (
                self.PATCH_VERSION
            ),

            "input": {
                "candidate_count": (
                    candidate_count
                ),

                "components": list(
                    self.COMPONENTS
                ),

                "original_decision_status": (
                    original_decision.get(
                        "status"
                    )
                ),
            },

            "reliability": {
                "overall_score": round(
                    overall_reliability,
                    6,
                ),

                "components": reliability,

                "strongest_component": (
                    strongest
                ),

                "weakest_component": (
                    weakest
                ),
            },

            "evidence_preferences": (
                preferences
            ),

            "separation": separation,

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
                    "TONIC_EVIDENCE_RELIABILITY_ONLY",
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

                "source_scores_modified": False,

                "original_scores_preserved": True,

                "original_decision_overridden": False,
            },
        }

    # ---------------------------------------------------------
    # File API
    # ---------------------------------------------------------

    def analyze_files(
        self,
        fusion_path: str,
        output_path: str,
        calibration_path: Optional[
            str
        ] = None,
        candidates: Optional[
            List[int]
        ] = None,
    ) -> Dict[str, Any]:

        fusion_data = self._load(
            fusion_path
        )

        calibration_data = None

        if calibration_path:
            calibration_data = self._load(
                calibration_path
            )

        result = self.analyze(
            fusion_data=fusion_data,
            calibration_data=calibration_data,
            candidates=candidates,
        )

        self._save(
            output_path,
            result,
        )

        return result

    # ---------------------------------------------------------
    # Compatibility API
    # ---------------------------------------------------------

    def analyze_file(
        self,
        fusion_path: str,
        output_path: str,
        calibration_path: Optional[
            str
        ] = None,
        candidates: Optional[
            List[int]
        ] = None,
    ) -> Dict[str, Any]:

        return self.analyze_files(
            fusion_path=fusion_path,
            output_path=output_path,
            calibration_path=calibration_path,
            candidates=candidates,
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PhoenixVoiceEngine "
            "Tonic Evidence Reliability Analyzer V1.0"
        )
    )

    parser.add_argument(
        "fusion_path",
        help="Tonic Evidence Fusion V1.1 JSON",
    )

    parser.add_argument(
        "output_path",
        help="Output reliability JSON",
    )

    parser.add_argument(
        "--calibration",
        dest="calibration_path",
        default=None,
        help=(
            "Optional Tonic Evidence "
            "Calibration V1.0 JSON"
        ),
    )

    parser.add_argument(
        "--candidates",
        nargs="+",
        type=int,
        default=None,
        help="Optional tonic candidates",
    )

    args = parser.parse_args()

    analyzer = (
        TonicEvidenceReliabilityAnalyzer()
    )

    result = analyzer.analyze_files(
        fusion_path=args.fusion_path,
        output_path=args.output_path,
        calibration_path=(
            args.calibration_path
        ),
        candidates=args.candidates,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )