"""
PhoenixVoiceEngine
Tonic Evidence Reliability Analyzer V1.1

Purpose
-------
Estimate source-specific reliability for tonic evidence.

V1.1 improves V1.0 by deriving reliability dimensions
from the actual evidence characteristics instead of
using one generic stability proxy.

IMPORTANT:
This module NEVER:
- modifies pitch
- modifies timing
- modifies performance
- modifies source evidence
- modifies original fusion scores
- makes a tonic decision
- makes a maqam decision
- makes a jins decision

It is an evidence-quality analyzer only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicEvidenceReliabilityAnalyzerV11:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.1.0"
    PATCH_VERSION = "1.1.0"

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
    # Safe helpers
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

    # ---------------------------------------------------------
    # Fusion candidates
    # ---------------------------------------------------------

    def _candidates(
        self,
        fusion_data: Dict[str, Any],
        candidates: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:

        ranking = fusion_data.get("ranking", {})
        rows = ranking.get("candidates", [])

        if not isinstance(rows, list):
            return []

        if candidates is None:
            selected = list(rows)
        else:
            wanted = {int(x) % 12 for x in candidates}

            selected = [
                row
                for row in rows
                if self._int(
                    row.get("tonic_pitch_class"),
                    -1,
                ) % 12 in wanted
            ]

        selected.sort(
            key=lambda x: self._float(
                x.get("fused_score", 0.0)
            ),
            reverse=True,
        )

        return selected

    # ---------------------------------------------------------
    # Component values
    # ---------------------------------------------------------

    def _components(
        self,
        candidate: Dict[str, Any],
    ) -> Dict[str, float]:

        values = candidate.get("components", {})

        if not isinstance(values, dict):
            values = {}

        return {
            name: self._clamp(
                self._float(
                    values.get(name, 0.0)
                )
            )
            for name in self.COMPONENTS
        }

    # ---------------------------------------------------------
    # Component separation
    # ---------------------------------------------------------

    def _separation(
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
                    "difference": 0.0,
                    "meaningful": False,
                }
            return result

        first = candidates[0]
        second = candidates[1]

        first_values = self._components(first)
        second_values = self._components(second)

        for component in self.COMPONENTS:
            a = first_values[component]
            b = second_values[component]

            if a > b:
                top = first.get("tonic_name")
                second_name = second.get("tonic_name")
                top_score = a
                second_score = b
            elif b > a:
                top = second.get("tonic_name")
                second_name = first.get("tonic_name")
                top_score = b
                second_score = a
            else:
                top = None
                second_name = None
                top_score = a
                second_score = b

            difference = abs(a - b)

            result[component] = {
                "available": True,
                "top_tonic": top,
                "second_tonic": second_name,
                "top_score": round(top_score, 6),
                "second_score": round(second_score, 6),
                "difference": round(difference, 6),
                "meaningful": (
                    difference
                    >= self.MIN_MEANINGFUL_SEPARATION
                ),
            }

        return result

    # ---------------------------------------------------------
    # Preference
    # ---------------------------------------------------------

    def _preferences(
        self,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, str]:

        if len(candidates) < 2:
            return {
                component: "TIE"
                for component in self.COMPONENTS
            }

        first = self._components(candidates[0])
        second = self._components(candidates[1])

        first_name = candidates[0].get("tonic_name")
        second_name = candidates[1].get("tonic_name")

        result = {}

        for component in self.COMPONENTS:
            if first[component] > second[component]:
                result[component] = first_name
            elif second[component] > first[component]:
                result[component] = second_name
            else:
                result[component] = "TIE"

        return result

    # ---------------------------------------------------------
    # Agreement / conflict
    # ---------------------------------------------------------

    def _agreement(
        self,
        component: str,
        preference: str,
        preferences: Dict[str, str],
    ) -> float:

        if preference in (None, "TIE"):
            return 0.0

        others = [
            value
            for name, value in preferences.items()
            if name != component
            and value not in (None, "TIE")
        ]

        if not others:
            return 0.0

        return self._clamp(
            sum(
                1
                for value in others
                if value == preference
            )
            / len(others)
        )

    def _conflict(
        self,
        component: str,
        preference: str,
        preferences: Dict[str, str],
    ) -> float:

        if preference in (None, "TIE"):
            return 1.0

        others = [
            value
            for name, value in preferences.items()
            if name != component
            and value not in (None, "TIE")
        ]

        if not others:
            return 0.0

        return self._clamp(
            sum(
                1
                for value in others
                if value != preference
            )
            / len(others)
        )

    # =========================================================
    # SOURCE-SPECIFIC RELIABILITY
    # =========================================================

    # ---------------------------------------------------------
    # Functional
    # ---------------------------------------------------------

    def _functional_reliability(
        self,
        data: Optional[Dict[str, Any]],
        tonic_pc: int,
    ) -> Dict[str, float]:

        if not data:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        role = None

        comparisons = (
            data.get("evidence", {})
            .get("tonic_role_comparison", [])
        )

        if isinstance(comparisons, list):
            for item in comparisons:
                if self._int(
                    item.get("tonic_pitch_class"),
                    -1,
                ) % 12 == tonic_pc:
                    role = item.get("role")
                    break

        if not role:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        event_count = self._int(
            role.get("event_count")
        )

        duration_share = self._float(
            role.get("duration_share")
        )

        initial_ratio = self._float(
            role.get("phrase_initial_ratio")
        )

        final_ratio = self._float(
            role.get("phrase_final_ratio")
        )

        availability = self._clamp(
            min(
                1.0,
                event_count / 50.0,
            )
        )

        strength = self._clamp(
            0.40 * duration_share
            + 0.30 * initial_ratio
            + 0.30 * final_ratio
        )

        stability = self._clamp(
            0.5 * availability
            + 0.5 * min(
                1.0,
                (initial_ratio + final_ratio)
                / 0.5,
            )
        )

        return {
            "availability": availability,
            "strength": strength,
            "stability": stability,
        }

    # ---------------------------------------------------------
    # Cadential
    # ---------------------------------------------------------

    def _cadential_reliability(
        self,
        data: Optional[Dict[str, Any]],
        tonic_pc: int,
    ) -> Dict[str, float]:

        if not data:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        candidate = None

        rows = (
            data.get("ranking", {})
            .get("candidates", [])
        )

        for row in rows:
            if self._int(
                row.get("tonic_pitch_class"),
                -1,
            ) % 12 == tonic_pc:
                candidate = row
                break

        if not candidate:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        ending_ratio = self._float(
            candidate.get("ending_phrase_ratio")
        )

        contexts = candidate.get(
            "recurring_contexts",
            [],
        )

        context_strengths = []

        if isinstance(contexts, list):
            for context in contexts:
                count = self._int(
                    context.get("count")
                )
                ending_ratio_context = self._float(
                    context.get("ending_ratio")
                )

                context_strengths.append(
                    self._clamp(
                        0.5 * min(
                            1.0,
                            count / 4.0,
                        )
                        + 0.5
                        * ending_ratio_context
                    )
                )

        context_stability = self._mean(
            context_strengths
        )

        availability = self._clamp(
            ending_ratio / 0.30
        )

        strength = self._clamp(
            0.60 * ending_ratio
            + 0.40 * context_stability
        )

        stability = self._clamp(
            0.50 * availability
            + 0.50 * context_stability
        )

        return {
            "availability": availability,
            "strength": strength,
            "stability": stability,
        }

    # ---------------------------------------------------------
    # Stable center
    # ---------------------------------------------------------

    def _stable_center_reliability(
        self,
        data: Optional[Dict[str, Any]],
        tonic_pc: int,
    ) -> Dict[str, float]:

        if not data:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        rows = (
            data.get("evidence", {})
            .get("stable_pitch_centers", [])
        )

        target = None

        for row in rows:
            if self._int(
                row.get("pitch_class"),
                -1,
            ) % 12 == tonic_pc:
                target = row
                break

        if not target:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        region_count = self._int(
            target.get("region_count")
        )

        duration = self._float(
            target.get("total_duration")
        )

        deviation = self._float(
            target.get(
                "median_region_deviation_cents"
            )
        )

        stability_score = self._float(
            target.get(
                "mean_stability_score"
            )
        )

        availability = self._clamp(
            0.5 * min(
                1.0,
                region_count / 50.0,
            )
            + 0.5 * min(
                1.0,
                duration / 30.0,
            )
        )

        deviation_quality = self._clamp(
            1.0
            - min(
                1.0,
                deviation / 30.0,
            )
        )

        strength = self._clamp(
            0.40 * availability
            + 0.30 * stability_score
            + 0.30 * deviation_quality
        )

        stability = self._clamp(
            0.60 * stability_score
            + 0.40 * deviation_quality
        )

        return {
            "availability": availability,
            "strength": strength,
            "stability": stability,
        }

    # ---------------------------------------------------------
    # Microtonal
    # ---------------------------------------------------------

    def _microtonal_reliability(
        self,
        stable_data: Optional[Dict[str, Any]],
        tonic_pc: int,
    ) -> Dict[str, float]:

        if not stable_data:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        rows = (
            stable_data.get("evidence", {})
            .get("stable_pitch_centers", [])
        )

        target = None

        for row in rows:
            if self._int(
                row.get("pitch_class"),
                -1,
            ) % 12 == tonic_pc:
                target = row
                break

        if not target:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        raw_hz_count = self._int(
            target.get("raw_hz_sample_count")
        )

        center_cents = abs(
            self._float(
                target.get("center_cents")
            )
        )

        deviation = self._float(
            target.get(
                "median_region_deviation_cents"
            )
        )

        availability = self._clamp(
            raw_hz_count / 3000.0
        )

        center_quality = self._clamp(
            1.0
            - min(
                1.0,
                center_cents / 50.0,
            )
        )

        reproducibility = self._clamp(
            1.0
            - min(
                1.0,
                deviation / 30.0,
            )
        )

        strength = self._clamp(
            0.40 * availability
            + 0.30 * center_quality
            + 0.30 * reproducibility
        )

        stability = self._clamp(
            0.50 * center_quality
            + 0.50 * reproducibility
        )

        return {
            "availability": availability,
            "strength": strength,
            "stability": stability,
        }

    # ---------------------------------------------------------
    # Tonic relative
    # ---------------------------------------------------------

    def _tonic_relative_reliability(
        self,
        data: Optional[Dict[str, Any]],
        tonic_pc: int,
    ) -> Dict[str, float]:

        if not data:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        candidates = (
            data.get("ranking", {})
            .get("candidates", [])
        )

        target = None

        for row in candidates:
            if self._int(
                row.get("tonic_pitch_class"),
                -1,
            ) % 12 == tonic_pc:
                target = row
                break

        if target is None:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        score = self._float(
            target.get(
                "relative_evidence_score",
                target.get("score", 0.0),
            )
        )

        availability = 1.0 if score > 0.0 else 0.0

        strength = self._clamp(score)

        # V1.1 intentionally treats a very weak relative
        # signal as low reliability rather than inventing
        # stability from unrelated evidence.
        stability = self._clamp(
            score
        )

        return {
            "availability": availability,
            "strength": strength,
            "stability": stability,
        }

    # ---------------------------------------------------------
    # Intervallic
    # ---------------------------------------------------------

    def _intervallic_reliability(
        self,
        data: Optional[Dict[str, Any]],
        tonic_pc: int,
    ) -> Dict[str, float]:

        if not data:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        rows = (
            data.get("ranking", {})
            .get("candidates", [])
        )

        target = None

        for row in rows:
            if self._int(
                row.get("tonic_pitch_class"),
                -1,
            ) % 12 == tonic_pc:
                target = row
                break

        if not target:
            return {
                "availability": 0.0,
                "strength": 0.0,
                "stability": 0.0,
            }

        components = target.get(
            "components",
            {},
        )

        detail = target.get(
            "intervallic_detail",
            {},
        )

        pitch_recurrence = self._float(
            detail.get(
                "pitch_recurrence",
                components.get(
                    "pitch_recurrence",
                    0.0,
                ),
            )
        )

        tonic_transition = self._float(
            detail.get(
                "tonic_transition",
                components.get(
                    "tonic_transition",
                    0.0,
                ),
            )
        )

        coverage = self._float(
            detail.get(
                "stable_center_coverage",
                components.get(
                    "stable_center_coverage",
                    0.0,
                ),
            )
        )

        availability_value = self._float(
            detail.get(
                "relationship_availability",
                components.get(
                    "relationship_availability",
                    0.0,
                ),
            )
        )

        availability = self._clamp(
            availability_value
        )

        strength = self._clamp(
            0.30 * pitch_recurrence
            + 0.30 * tonic_transition
            + 0.20 * coverage
            + 0.20 * availability_value
        )

        stability = self._clamp(
            0.50 * pitch_recurrence
            + 0.25 * coverage
            + 0.25 * availability_value
        )

        return {
            "availability": availability,
            "strength": strength,
            "stability": stability,
        }

    # ---------------------------------------------------------
    # Generic source extraction
    # ---------------------------------------------------------

    def _source_reliability(
        self,
        component: str,
        tonic_pc: int,
        sources: Dict[str, Optional[Dict[str, Any]]],
    ) -> Dict[str, float]:

        if component == "functional":
            return self._functional_reliability(
                sources.get("functional"),
                tonic_pc,
            )

        if component == "cadential":
            return self._cadential_reliability(
                sources.get("cadential"),
                tonic_pc,
            )

        if component == "stable_center":
            return self._stable_center_reliability(
                sources.get("stable_center"),
                tonic_pc,
            )

        if component == "microtonal":
            return self._microtonal_reliability(
                sources.get("stable_center"),
                tonic_pc,
            )

        if component == "tonic_relative":
            return self._tonic_relative_reliability(
                sources.get("tonic_relative"),
                tonic_pc,
            )

        if component == "intervallic_relationship":
            return self._intervallic_reliability(
                sources.get("intervallic_relationship"),
                tonic_pc,
            )

        return {
            "availability": 0.0,
            "strength": 0.0,
            "stability": 0.0,
        }

    # ---------------------------------------------------------
    # Reliability score
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

        value = (
            0.15 * availability
            + 0.20 * strength
            + 0.20 * separation
            + 0.20 * stability
            + 0.15 * agreement
            - 0.10 * conflict
        )

        return self._clamp(value)

    # ---------------------------------------------------------
    # Analyze
    # ---------------------------------------------------------

    def analyze(
        self,
        fusion_data: Dict[str, Any],
        functional_data: Optional[Dict[str, Any]] = None,
        cadential_data: Optional[Dict[str, Any]] = None,
        stable_center_data: Optional[Dict[str, Any]] = None,
        tonic_relative_data: Optional[Dict[str, Any]] = None,
        intervallic_data: Optional[Dict[str, Any]] = None,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        selected = self._candidates(
            fusion_data,
            candidates,
        )

        separation = self._separation(
            selected
        )

        preferences = self._preferences(
            selected
        )

        sources = {
            "functional": functional_data,
            "cadential": cadential_data,
            "stable_center": stable_center_data,
            "microtonal": stable_center_data,
            "tonic_relative": tonic_relative_data,
            "intervallic_relationship": intervallic_data,
        }

        records = []

        for component in self.COMPONENTS:

            sep = separation[component]

            preference = preferences.get(
                component,
                "TIE",
            )

            agreement = self._agreement(
                component,
                preference,
                preferences,
            )

            conflict = self._conflict(
                component,
                preference,
                preferences,
            )

            source_values = []

            # Calculate source-specific values for
            # every candidate and aggregate conservatively.
            for candidate in selected:

                tonic_pc = (
                    self._int(
                        candidate.get(
                            "tonic_pitch_class",
                            -1,
                        )
                    )
                    % 12
                )

                values = self._source_reliability(
                    component,
                    tonic_pc,
                    sources,
                )

                source_values.append(values)

            if source_values:

                availability = self._mean([
                    x["availability"]
                    for x in source_values
                ])

                strength = self._mean([
                    x["strength"]
                    for x in source_values
                ])

                stability = self._mean([
                    x["stability"]
                    for x in source_values
                ])

            else:

                availability = 0.0
                strength = 0.0
                stability = 0.0

            separation_value = self._clamp(
                sep["difference"]
            )

            reliability = (
                self._reliability_score(
                    availability=availability,
                    strength=strength,
                    separation=separation_value,
                    stability=stability,
                    agreement=agreement,
                    conflict=conflict,
                )
            )

            records.append({
                "component": component,
                "reliability_score": round(
                    reliability,
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
                "top_tonic": sep["top_tonic"],
                "top_score": sep["top_score"],
                "second_score": sep["second_score"],
                "meaningful_separation": sep[
                    "meaningful"
                ],
                "evidence_only": True,
            })

        records.sort(
            key=lambda x: x[
                "reliability_score"
            ],
            reverse=True,
        )

        overall = self._mean([
            x["reliability_score"]
            for x in records
        ])

        strongest = (
            records[0]
            if records
            else None
        )

        weakest = (
            records[-1]
            if records
            else None
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
                    selected
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
                    overall,
                    6,
                ),
                "components": records,
                "strongest_component": strongest,
                "weakest_component": weakest,
            },

            "evidence_preferences": preferences,

            "separation": separation,

            "decision": {
                "status": "EVIDENCE_ONLY",
                "tonic_pitch_class": None,
                "tonic_name": None,
                "maqam": None,
                "jins": None,
                "confidence": None,
                "reason": [
                    "TONIC_EVIDENCE_RELIABILITY_V11_ONLY",
                    "SOURCE_SPECIFIC_RELIABILITY",
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
        functional_path: Optional[str] = None,
        cadential_path: Optional[str] = None,
        stable_center_path: Optional[str] = None,
        tonic_relative_path: Optional[str] = None,
        intervallic_path: Optional[str] = None,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        fusion_data = self._load(
            fusion_path
        )

        functional_data = (
            self._load(functional_path)
            if functional_path
            else None
        )

        cadential_data = (
            self._load(cadential_path)
            if cadential_path
            else None
        )

        stable_center_data = (
            self._load(stable_center_path)
            if stable_center_path
            else None
        )

        tonic_relative_data = (
            self._load(tonic_relative_path)
            if tonic_relative_path
            else None
        )

        intervallic_data = (
            self._load(intervallic_path)
            if intervallic_path
            else None
        )

        result = self.analyze(
            fusion_data=fusion_data,
            functional_data=functional_data,
            cadential_data=cadential_data,
            stable_center_data=stable_center_data,
            tonic_relative_data=tonic_relative_data,
            intervallic_data=intervallic_data,
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
        output_path: str,
        **kwargs,
    ) -> Dict[str, Any]:

        return self.analyze_files(
            fusion_path,
            output_path,
            **kwargs,
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PhoenixVoiceEngine "
            "Tonic Evidence Reliability Analyzer V1.1"
        )
    )

    parser.add_argument(
        "fusion_path"
    )

    parser.add_argument(
        "output_path"
    )

    parser.add_argument(
        "--functional"
    )

    parser.add_argument(
        "--cadential"
    )

    parser.add_argument(
        "--stable-center"
    )

    parser.add_argument(
        "--tonic-relative"
    )

    parser.add_argument(
        "--intervallic"
    )

    parser.add_argument(
        "--candidates",
        nargs="+",
        type=int,
    )

    args = parser.parse_args()

    analyzer = (
        TonicEvidenceReliabilityAnalyzerV11()
    )

    result = analyzer.analyze_files(
        fusion_path=args.fusion_path,
        output_path=args.output_path,
        functional_path=args.functional,
        cadential_path=args.cadential,
        stable_center_path=args.stable_center,
        tonic_relative_path=args.tonic_relative,
        intervallic_path=args.intervallic,
        candidates=args.candidates,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )