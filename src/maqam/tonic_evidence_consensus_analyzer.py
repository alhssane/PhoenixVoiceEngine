"""
PhoenixVoiceEngine
Tonic Evidence Consensus Analyzer V1.0

Purpose
-------
Aggregate tonic evidence into an interpretable consensus report.

IMPORTANT
---------
This module is NOT a tonic decision engine.

It does NOT:
- modify pitch
- modify timing
- modify performance
- modify source scores
- override previous decisions
- select a final tonic
- select a maqam
- select a jins

It only analyzes:
- evidence preferences
- agreement
- conflict
- reliability
- separation
- evidence strength
- consensus quality

The final result remains EVIDENCE_ONLY.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicEvidenceConsensusAnalyzer:
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

    MIN_MEANINGFUL_SEPARATION = 0.05

    # ---------------------------------------------------------
    # IO
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def _float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _int(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _clamp(
        value: float,
        low: float = 0.0,
        high: float = 1.0,
    ) -> float:
        return max(low, min(high, float(value)))

    @staticmethod
    def _mean(values: List[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _round(value: float) -> float:
        return round(float(value), 6)

    # ---------------------------------------------------------
    # Candidate extraction
    # ---------------------------------------------------------

    def _extract_candidates(
        self,
        fusion_data: Dict[str, Any],
        candidates: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:

        rows = (
            fusion_data
            .get("ranking", {})
            .get("candidates", [])
        )

        if not isinstance(rows, list):
            return []

        if candidates is not None:
            wanted = {
                int(x) % 12
                for x in candidates
            }

            rows = [
                row
                for row in rows
                if self._int(
                    row.get(
                        "tonic_pitch_class",
                        -1,
                    ),
                    -1,
                ) % 12 in wanted
            ]

        return list(rows)

    # ---------------------------------------------------------
    # Preference extraction
    # ---------------------------------------------------------

    def _extract_preferences(
        self,
        reliability_data: Optional[Dict[str, Any]],
        fusion_data: Dict[str, Any],
    ) -> Dict[str, str]:

        if reliability_data:
            preferences = reliability_data.get(
                "evidence_preferences"
            )

            if isinstance(preferences, dict):
                return {
                    component: str(
                        preferences.get(
                            component,
                            "TIE",
                        )
                    )
                    for component in self.COMPONENTS
                }

        # Fallback directly from fusion scores.
        candidates = self._extract_candidates(
            fusion_data
        )

        if len(candidates) < 2:
            return {
                component: "TIE"
                for component in self.COMPONENTS
            }

        first = candidates[0]
        second = candidates[1]

        first_components = first.get(
            "components",
            {},
        )
        second_components = second.get(
            "components",
            {},
        )

        first_name = first.get(
            "tonic_name"
        )
        second_name = second.get(
            "tonic_name"
        )

        result = {}

        for component in self.COMPONENTS:
            a = self._float(
                first_components.get(
                    component,
                    0.0,
                )
            )
            b = self._float(
                second_components.get(
                    component,
                    0.0,
                )
            )

            if a > b:
                result[component] = first_name
            elif b > a:
                result[component] = second_name
            else:
                result[component] = "TIE"

        return result

    # ---------------------------------------------------------
    # Reliability extraction
    # ---------------------------------------------------------

    def _extract_reliability(
        self,
        reliability_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:

        result = {}

        if not reliability_data:
            return result

        rows = (
            reliability_data
            .get("reliability", {})
            .get("components", [])
        )

        if not isinstance(rows, list):
            return result

        for row in rows:
            component = row.get(
                "component"
            )

            if component not in self.COMPONENTS:
                continue

            result[component] = {
                "reliability_score": self._clamp(
                    self._float(
                        row.get(
                            "reliability_score"
                        )
                    )
                ),
                "availability": self._clamp(
                    self._float(
                        row.get(
                            "availability"
                        )
                    )
                ),
                "strength": self._clamp(
                    self._float(
                        row.get(
                            "strength"
                        )
                    )
                ),
                "separation": self._clamp(
                    self._float(
                        row.get(
                            "separation"
                        )
                    )
                ),
                "stability": self._clamp(
                    self._float(
                        row.get(
                            "stability"
                        )
                    )
                ),
                "agreement": self._clamp(
                    self._float(
                        row.get(
                            "agreement"
                        )
                    )
                ),
                "conflict": self._clamp(
                    self._float(
                        row.get(
                            "conflict"
                        )
                    )
                ),
                "preferred_tonic": row.get(
                    "preferred_tonic",
                    "TIE",
                ),
                "meaningful_separation": bool(
                    row.get(
                        "meaningful_separation",
                        False,
                    )
                ),
            }

        return result

    # ---------------------------------------------------------
    # Separation extraction
    # ---------------------------------------------------------

    def _extract_separation(
        self,
        reliability_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:

        result = {}

        if reliability_data:
            separation = reliability_data.get(
                "separation",
                {},
            )

            if isinstance(separation, dict):
                for component in self.COMPONENTS:
                    item = separation.get(
                        component
                    )

                    if isinstance(item, dict):
                        result[component] = {
                            "difference": self._clamp(
                                self._float(
                                    item.get(
                                        "difference"
                                    )
                                )
                            ),
                            "meaningful": bool(
                                item.get(
                                    "meaningful",
                                    False,
                                )
                            ),
                            "top_tonic": item.get(
                                "top_tonic"
                            ),
                            "second_tonic": item.get(
                                "second_tonic"
                            ),
                        }

        return result

    # ---------------------------------------------------------
    # Consensus groups
    # ---------------------------------------------------------

    def _groups(
        self,
        preferences: Dict[str, str],
    ) -> Dict[str, List[str]]:

        groups: Dict[str, List[str]] = {}

        for component, tonic in preferences.items():

            if tonic in (
                None,
                "",
                "TIE",
            ):
                continue

            groups.setdefault(
                tonic,
                [],
            ).append(component)

        return groups

    # ---------------------------------------------------------
    # Agreement metrics
    # ---------------------------------------------------------

    def _agreement_metrics(
        self,
        preferences: Dict[str, str],
        reliability: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:

        groups = self._groups(
            preferences
        )

        decisive = [
            component
            for component, tonic
            in preferences.items()
            if tonic not in (
                None,
                "",
                "TIE",
            )
        ]

        tie_components = [
            component
            for component, tonic
            in preferences.items()
            if tonic in (
                None,
                "",
                "TIE",
            )
        ]

        if not decisive:
            return {
                "decisive_component_count": 0,
                "tie_component_count": len(
                    tie_components
                ),
                "agreement_score": 0.0,
                "conflict_score": 0.0,
                "dominant_tonic": None,
                "dominant_count": 0,
                "dominant_share": 0.0,
                "groups": groups,
            }

        counts = {
            tonic: len(items)
            for tonic, items
            in groups.items()
        }

        dominant_tonic = max(
            counts,
            key=counts.get,
        )

        dominant_count = counts[
            dominant_tonic
        ]

        dominant_share = (
            dominant_count
            / len(decisive)
        )

        # Agreement is not allowed to become 1.0 merely
        # because one group has many weak components.
        weighted_total = 0.0
        weighted_dominant = 0.0

        for component in decisive:

            row = reliability.get(
                component,
                {},
            )

            weight = self._clamp(
                self._float(
                    row.get(
                        "reliability_score",
                        0.0,
                    )
                )
            )

            weighted_total += weight

            if (
                preferences.get(component)
                == dominant_tonic
            ):
                weighted_dominant += weight

        if weighted_total > 0:
            weighted_agreement = (
                weighted_dominant
                / weighted_total
            )
        else:
            weighted_agreement = 0.0

        agreement_score = self._clamp(
            0.5 * dominant_share
            + 0.5 * weighted_agreement
        )

        conflict_score = self._clamp(
            1.0 - agreement_score
        )

        return {
            "decisive_component_count": len(
                decisive
            ),
            "tie_component_count": len(
                tie_components
            ),
            "agreement_score": self._round(
                agreement_score
            ),
            "conflict_score": self._round(
                conflict_score
            ),
            "dominant_tonic": dominant_tonic,
            "dominant_count": dominant_count,
            "dominant_share": self._round(
                dominant_share
            ),
            "weighted_agreement": self._round(
                weighted_agreement
            ),
            "groups": groups,
        }

    # ---------------------------------------------------------
    # Reliability-weighted consensus
    # ---------------------------------------------------------

    def _weighted_tonic_support(
        self,
        preferences: Dict[str, str],
        reliability: Dict[str, Dict[str, Any]],
    ) -> Dict[str, float]:

        support: Dict[str, float] = {}

        for component, tonic in preferences.items():

            if tonic in (
                None,
                "",
                "TIE",
            ):
                continue

            row = reliability.get(
                component,
                {},
            )

            reliability_score = self._clamp(
                self._float(
                    row.get(
                        "reliability_score",
                        0.0,
                    )
                )
            )

            separation = self._clamp(
                self._float(
                    row.get(
                        "separation",
                        0.0,
                    )
                )
            )

            meaningful = bool(
                row.get(
                    "meaningful_separation",
                    False,
                )
            )

            # A component that has no meaningful separation
            # must not contribute its full reliability.
            separation_factor = (
                separation
                if not meaningful
                else max(
                    separation,
                    self.MIN_MEANINGFUL_SEPARATION,
                )
            )

            contribution = (
                reliability_score
                * self._clamp(
                    separation_factor
                    / 0.25
                )
            )

            support[tonic] = (
                support.get(tonic, 0.0)
                + contribution
            )

        return {
            tonic: self._round(score)
            for tonic, score
            in support.items()
        }

    # ---------------------------------------------------------
    # Consensus quality
    # ---------------------------------------------------------

    def _consensus_quality(
        self,
        agreement_score: float,
        conflict_score: float,
        weighted_support: Dict[str, float],
        reliability_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if weighted_support:
            ordered = sorted(
                weighted_support.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            top_tonic = ordered[0][0]
            top_support = ordered[0][1]

            if len(ordered) > 1:
                second_support = ordered[1][1]
            else:
                second_support = 0.0

            total = sum(
                weighted_support.values()
            )

            if total > 0:
                support_share = (
                    top_support / total
                )
            else:
                support_share = 0.0

            support_margin = (
                top_support
                - second_support
            )

        else:
            top_tonic = None
            top_support = 0.0
            second_support = 0.0
            support_share = 0.0
            support_margin = 0.0

        if reliability_data:
            overall_reliability = self._clamp(
                self._float(
                    reliability_data
                    .get("reliability", {})
                    .get(
                        "overall_score",
                        0.0,
                    )
                )
            )
        else:
            overall_reliability = 0.0

        quality = self._clamp(
            0.30 * agreement_score
            + 0.25 * support_share
            + 0.20 * self._clamp(
                support_margin / 0.25
            )
            + 0.25 * overall_reliability
        )

        return {
            "top_tonic": top_tonic,
            "top_support": self._round(
                top_support
            ),
            "second_support": self._round(
                second_support
            ),
            "support_share": self._round(
                support_share
            ),
            "support_margin": self._round(
                support_margin
            ),
            "overall_reliability": self._round(
                overall_reliability
            ),
            "consensus_quality": self._round(
                quality
            ),
        }

    # ---------------------------------------------------------
    # Interpretive status
    # ---------------------------------------------------------

    def _status(
        self,
        agreement: float,
        conflict: float,
        support_share: float,
        support_margin: float,
    ) -> str:

        if support_share >= 0.75 and (
            support_margin >= 0.15
        ):
            return "STRONG_CONSENSUS"

        if support_share >= 0.60 and (
            support_margin >= 0.05
        ):
            return "MODERATE_CONSENSUS"

        if conflict >= 0.55:
            return "CONFLICTING_EVIDENCE"

        if agreement >= 0.50:
            return "PARTIAL_CONSENSUS"

        return "INSUFFICIENT_CONSENSUS"

    # ---------------------------------------------------------
    # Full analysis
    # ---------------------------------------------------------

    def analyze(
        self,
        fusion_data: Dict[str, Any],
        reliability_data: Optional[Dict[str, Any]] = None,
        calibration_data: Optional[Dict[str, Any]] = None,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        selected_candidates = self._extract_candidates(
            fusion_data,
            candidates,
        )

        preferences = self._extract_preferences(
            reliability_data,
            fusion_data,
        )

        reliability = self._extract_reliability(
            reliability_data
        )

        separation = self._extract_separation(
            reliability_data
        )

        agreement = self._agreement_metrics(
            preferences,
            reliability,
        )

        weighted_support = (
            self._weighted_tonic_support(
                preferences,
                reliability,
            )
        )

        consensus = self._consensus_quality(
            agreement_score=self._float(
                agreement.get(
                    "agreement_score"
                )
            ),
            conflict_score=self._float(
                agreement.get(
                    "conflict_score"
                )
            ),
            weighted_support=weighted_support,
            reliability_data=reliability_data,
        )

        status = self._status(
            agreement=self._float(
                agreement.get(
                    "agreement_score"
                )
            ),
            conflict=self._float(
                agreement.get(
                    "conflict_score"
                )
            ),
            support_share=self._float(
                consensus.get(
                    "support_share"
                )
            ),
            support_margin=self._float(
                consensus.get(
                    "support_margin"
                )
            ),
        )

        original_decision = fusion_data.get(
            "decision",
            {},
        )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,

            "input": {
                "candidate_count": len(
                    selected_candidates
                ),
                "candidate_tonics": [
                    {
                        "pitch_class": self._int(
                            row.get(
                                "tonic_pitch_class"
                            )
                        ) % 12,
                        "name": row.get(
                            "tonic_name"
                        ),
                    }
                    for row in selected_candidates
                ],
                "component_count": len(
                    self.COMPONENTS
                ),
                "calibration_available": (
                    calibration_data is not None
                ),
                "reliability_available": (
                    reliability_data is not None
                ),
                "original_decision_status": (
                    original_decision.get(
                        "status"
                    )
                ),
            },

            "evidence_preferences": preferences,

            "reliability": {
                component: reliability.get(
                    component,
                    {
                        "reliability_score": 0.0,
                        "preferred_tonic": "TIE",
                    },
                )
                for component
                in self.COMPONENTS
            },

            "separation": separation,

            "consensus": {
                "status": status,
                "agreement": agreement,
                "weighted_tonic_support": (
                    weighted_support
                ),
                "quality": consensus,
            },

            "decision": {
                "status": "EVIDENCE_ONLY",
                "tonic_pitch_class": None,
                "tonic_name": None,
                "maqam": None,
                "jins": None,
                "confidence": None,
                "reason": [
                    "TONIC_EVIDENCE_CONSENSUS_ONLY",
                    "NO_TONIC_DECISION",
                    "EVIDENCE_CONFLICT_MUST_REMAIN_VISIBLE",
                ],
            },

            "protection": {
                "source_pitch_modified": False,
                "source_timing_modified": False,
                "source_performance_modified": False,
                "source_scores_modified": False,
                "tonic_decision_made": False,
                "maqam_decision_made": False,
                "jins_decision_made": False,
                "original_scores_preserved": True,
                "original_decision_overridden": False,
                "evidence_conflict_hidden": False,
            },
        }

    # ---------------------------------------------------------
    # File API
    # ---------------------------------------------------------

    def analyze_files(
        self,
        fusion_path: str,
        reliability_path: str,
        output_path: str,
        calibration_path: Optional[str] = None,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        fusion_data = self._load(
            fusion_path
        )

        reliability_data = self._load(
            reliability_path
        )

        calibration_data = (
            self._load(calibration_path)
            if calibration_path
            else None
        )

        result = self.analyze(
            fusion_data=fusion_data,
            reliability_data=reliability_data,
            calibration_data=calibration_data,
            candidates=candidates,
        )

        self._save(
            output_path,
            result,
        )

        return result

    def analyze_file(
        self,
        fusion_path: str,
        reliability_path: str,
        output_path: str,
        **kwargs,
    ) -> Dict[str, Any]:

        return self.analyze_files(
            fusion_path,
            reliability_path,
            output_path,
            **kwargs,
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PhoenixVoiceEngine "
            "Tonic Evidence Consensus Analyzer V1.0"
        )
    )

    parser.add_argument(
        "fusion_path"
    )

    parser.add_argument(
        "reliability_path"
    )

    parser.add_argument(
        "output_path"
    )

    parser.add_argument(
        "--calibration"
    )

    parser.add_argument(
        "--candidates",
        nargs="+",
        type=int,
    )

    args = parser.parse_args()

    analyzer = (
        TonicEvidenceConsensusAnalyzer()
    )

    result = analyzer.analyze_files(
        fusion_path=args.fusion_path,
        reliability_path=args.reliability_path,
        output_path=args.output_path,
        calibration_path=args.calibration,
        candidates=args.candidates,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )