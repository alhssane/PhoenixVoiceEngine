"""
PhoenixVoiceEngine
Tonic Decision Readiness Analyzer V1.0

Purpose
-------
Determine whether the accumulated tonic evidence is sufficiently
reliable, separated, consensual, and safe for a future tonic decision.

This module is a READINESS GATE only.

It does NOT:
- choose a tonic
- modify pitch
- modify timing
- modify performance
- modify source scores
- override previous decisions
- choose maqam
- choose jins

Output remains EVIDENCE_ONLY / NOT_READY unless a future decision
engine explicitly consumes this readiness result.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicDecisionReadinessAnalyzer:
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
    # Readiness thresholds
    # ---------------------------------------------------------

    MIN_OVERALL_RELIABILITY = 0.55
    MIN_CONSENSUS_QUALITY = 0.60
    MIN_CONSENSUS_AGREEMENT = 0.60

    MAX_CONFLICT_SCORE = 0.35
    MAX_CONFLICT_SEVERITY = 0.40

    MIN_SUPPORT_MARGIN = 0.15
    MIN_SUPPORT_SHARE = 0.60

    MIN_MEANINGFUL_COMPONENTS = 2
    MIN_DOMINANT_COMPONENT_SHARE = 0.60

    # A candidate should not be accepted merely because it has
    # one strong component when a reliable opposing component exists.
    MAX_OPPOSING_MEANINGFUL_COMPONENTS = 0

    # ---------------------------------------------------------
    # IO
    # ---------------------------------------------------------

    @staticmethod
    def _load(path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as f:
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
    # Numeric helpers
    # ---------------------------------------------------------

    @staticmethod
    def _float(
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
        low: float = 0.0,
        high: float = 1.0,
    ) -> float:
        return max(
            low,
            min(
                high,
                float(value),
            ),
        )

    @staticmethod
    def _round(
        value: float,
    ) -> float:
        return round(
            float(value),
            6,
        )

    # ---------------------------------------------------------
    # Generic nested extraction
    # ---------------------------------------------------------

    @staticmethod
    def _nested(
        data: Dict[str, Any],
        *keys: str,
        default: Any = None,
    ) -> Any:
        current: Any = data

        for key in keys:
            if not isinstance(
                current,
                dict,
            ):
                return default

            current = current.get(key)

            if current is None:
                return default

        return current

    # ---------------------------------------------------------
    # Consensus extraction
    # ---------------------------------------------------------

    def _extract_consensus(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        consensus = data.get(
            "consensus",
            {},
        )

        if not isinstance(
            consensus,
            dict,
        ):
            consensus = {}

        agreement = consensus.get(
            "agreement",
            {},
        )

        if not isinstance(
            agreement,
            dict,
        ):
            agreement = {}

        quality = consensus.get(
            "quality",
            {},
        )

        if not isinstance(
            quality,
            dict,
        ):
            quality = {}

        weighted_support = consensus.get(
            "weighted_tonic_support",
            {},
        )

        if not isinstance(
            weighted_support,
            dict,
        ):
            weighted_support = {}

        support = {
            str(k): self._clamp(
                self._float(v)
            )
            for k, v
            in weighted_support.items()
        }

        top_tonic = quality.get(
            "top_tonic"
        )

        if top_tonic is None:
            top_tonic = agreement.get(
                "dominant_tonic"
            )

        return {
            "status": consensus.get(
                "status",
                "UNKNOWN",
            ),
            "agreement_score": self._clamp(
                self._float(
                    agreement.get(
                        "agreement_score",
                        0.0,
                    )
                )
            ),
            "conflict_score": self._clamp(
                self._float(
                    agreement.get(
                        "conflict_score",
                        0.0,
                    )
                )
            ),
            "weighted_agreement": self._clamp(
                self._float(
                    agreement.get(
                        "weighted_agreement",
                        0.0,
                    )
                )
            ),
            "dominant_tonic": (
                agreement.get(
                    "dominant_tonic"
                )
            ),
            "dominant_share": self._clamp(
                self._float(
                    agreement.get(
                        "dominant_share",
                        0.0,
                    )
                )
            ),
            "weighted_support": support,
            "top_tonic": top_tonic,
            "support_share": self._clamp(
                self._float(
                    quality.get(
                        "support_share",
                        0.0,
                    )
                )
            ),
            "support_margin": abs(
                self._float(
                    quality.get(
                        "support_margin",
                        0.0,
                    )
                )
            ),
            "consensus_quality": self._clamp(
                self._float(
                    quality.get(
                        "consensus_quality",
                        0.0,
                    )
                )
            ),
        }

    # ---------------------------------------------------------
    # Reliability extraction
    # ---------------------------------------------------------

    def _extract_reliability(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        reliability = data.get(
            "reliability",
            {},
        )

        if not isinstance(
            reliability,
            dict,
        ):
            reliability = {}

        rows = reliability.get(
            "components",
            [],
        )

        if not isinstance(
            rows,
            list,
        ):
            rows = []

        components: Dict[str, Dict[str, Any]] = {}

        for row in rows:

            if not isinstance(
                row,
                dict,
            ):
                continue

            component = row.get(
                "component"
            )

            if component not in self.COMPONENTS:
                continue

            components[component] = {
                "reliability_score": self._clamp(
                    self._float(
                        row.get(
                            "reliability_score",
                            0.0,
                        )
                    )
                ),
                "availability": self._clamp(
                    self._float(
                        row.get(
                            "availability",
                            0.0,
                        )
                    )
                ),
                "strength": self._clamp(
                    self._float(
                        row.get(
                            "strength",
                            0.0,
                        )
                    )
                ),
                "separation": self._clamp(
                    self._float(
                        row.get(
                            "separation",
                            0.0,
                        )
                    )
                ),
                "stability": self._clamp(
                    self._float(
                        row.get(
                            "stability",
                            0.0,
                        )
                    )
                ),
                "agreement": self._clamp(
                    self._float(
                        row.get(
                            "agreement",
                            0.0,
                        )
                    )
                ),
                "conflict": self._clamp(
                    self._float(
                        row.get(
                            "conflict",
                            0.0,
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

        overall = self._clamp(
            self._float(
                reliability.get(
                    "overall_score",
                    0.0,
                )
            )
        )

        return {
            "overall_score": overall,
            "components": components,
        }

    # ---------------------------------------------------------
    # Conflict extraction
    # ---------------------------------------------------------

    def _extract_conflict(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        conflict = data.get(
            "conflict",
            {},
        )

        if not isinstance(
            conflict,
            dict,
        ):
            conflict = {}

        balance = conflict.get(
            "balance",
            {},
        )

        if not isinstance(
            balance,
            dict,
        ):
            balance = {}

        severity = conflict.get(
            "severity",
            {},
        )

        if not isinstance(
            severity,
            dict,
        ):
            severity = {}

        strongest = conflict.get(
            "strongest_by_group",
            {},
        )

        if not isinstance(
            strongest,
            dict,
        ):
            strongest = {}

        g = balance.get(
            "G",
            {},
        )

        c = balance.get(
            "C",
            {},
        )

        if not isinstance(
            g,
            dict,
        ):
            g = {}

        if not isinstance(
            c,
            dict,
        ):
            c = {}

        return {
            "severity_score": self._clamp(
                self._float(
                    severity.get(
                        "score",
                        0.0,
                    )
                )
            ),
            "severity_label": severity.get(
                "label",
                "UNKNOWN",
            ),
            "conflict_score": self._clamp(
                self._float(
                    self._nested(
                        data,
                        "conflict",
                        "consensus_context",
                        "conflict_score",
                        default=0.0,
                    )
                )
            ),
            "balance": self._clamp(
                self._float(
                    balance.get(
                        "balance",
                        0.0,
                    )
                )
            ),
            "dominance": self._clamp(
                self._float(
                    balance.get(
                        "dominance",
                        0.0,
                    )
                )
            ),
            "weighted_preference": balance.get(
                "weighted_preference",
                "TIE",
            ),
            "G_support": self._float(
                g.get(
                    "support",
                    0.0,
                )
            ),
            "C_support": self._float(
                c.get(
                    "support",
                    0.0,
                )
            ),
            "G_share": self._clamp(
                self._float(
                    g.get(
                        "share",
                        0.0,
                    )
                )
            ),
            "C_share": self._clamp(
                self._float(
                    c.get(
                        "share",
                        0.0,
                    )
                )
            ),
            "G_components": list(
                g.get(
                    "components",
                    [],
                )
            ),
            "C_components": list(
                c.get(
                    "components",
                    [],
                )
            ),
            "meaningful_G_components": self._int_like(
                severity.get(
                    "meaningful_G_components",
                    0,
                )
            ),
            "meaningful_C_components": self._int_like(
                severity.get(
                    "meaningful_C_components",
                    0,
                )
            ),
            "strongest_by_group": strongest,
        }

    @staticmethod
    def _int_like(
        value: Any,
    ) -> int:
        try:
            return int(value)
        except (
            TypeError,
            ValueError,
        ):
            return 0

    # ---------------------------------------------------------
    # Evidence preference extraction
    # ---------------------------------------------------------

    def _extract_preferences(
        self,
        *sources: Dict[str, Any],
    ) -> Dict[str, str]:

        result = {
            component: "TIE"
            for component in self.COMPONENTS
        }

        for source in sources:

            if not isinstance(
                source,
                dict,
            ):
                continue

            preferences = source.get(
                "evidence_preferences"
            )

            if not isinstance(
                preferences,
                dict,
            ):
                continue

            for component in self.COMPONENTS:

                value = preferences.get(
                    component
                )

                if value in (
                    "G",
                    "C",
                    "TIE",
                ):
                    result[component] = value

        return result

    # ---------------------------------------------------------
    # Meaningful component count
    # ---------------------------------------------------------

    def _meaningful_component_count(
        self,
        reliability: Dict[str, Any],
    ) -> int:

        components = reliability.get(
            "components",
            {},
        )

        if not isinstance(
            components,
            dict,
        ):
            return 0

        count = 0

        for row in components.values():

            if not isinstance(
                row,
                dict,
            ):
                continue

            if (
                row.get(
                    "meaningful_separation",
                    False,
                )
                and row.get(
                    "preferred_tonic",
                    "TIE",
                )
                in ("G", "C")
            ):
                count += 1

        return count

    # ---------------------------------------------------------
    # Candidate readiness
    # ---------------------------------------------------------

    def _candidate_readiness(
        self,
        tonic: str,
        consensus: Dict[str, Any],
        reliability: Dict[str, Any],
        conflict: Dict[str, Any],
        preferences: Dict[str, str],
    ) -> Dict[str, Any]:

        weighted_support = consensus.get(
            "weighted_support",
            {},
        )

        candidate_support = self._clamp(
            self._float(
                weighted_support.get(
                    tonic,
                    0.0,
                )
            )
        )

        top_support = max(
            [
                self._float(
                    value
                )
                for value
                in weighted_support.values()
            ]
            or [0.0]
        )

        second_support = 0.0

        ordered_supports = sorted(
            [
                self._float(v)
                for v in weighted_support.values()
            ],
            reverse=True,
        )

        if len(
            ordered_supports
        ) > 1:
            second_support = (
                ordered_supports[1]
            )

        if (
            candidate_support
            >= top_support
        ):
            candidate_margin = (
                top_support
                - second_support
            )
        else:
            candidate_margin = (
                candidate_support
                - top_support
            )

        support_share = (
            candidate_support
            / max(
                candidate_support
                + second_support,
                1e-12,
            )
        )

        candidate_components = [
            component
            for component, preferred
            in preferences.items()
            if preferred == tonic
        ]

        opposing_tonic = (
            "C"
            if tonic == "G"
            else "G"
        )

        opposing_components = [
            component
            for component, preferred
            in preferences.items()
            if preferred == opposing_tonic
        ]

        meaningful_opposing = 0

        reliability_components = reliability.get(
            "components",
            {},
        )

        for component in opposing_components:

            row = reliability_components.get(
                component,
                {},
            )

            if row.get(
                "meaningful_separation",
                False,
            ):
                meaningful_opposing += 1

        strong_candidate_components = 0

        for component in candidate_components:

            row = reliability_components.get(
                component,
                {},
            )

            if (
                row.get(
                    "meaningful_separation",
                    False,
                )
                and self._float(
                    row.get(
                        "reliability_score",
                        0.0,
                    )
                )
                >= 0.30
            ):
                strong_candidate_components += 1

        checks = {
            "candidate_has_support": (
                candidate_support > 0.0
            ),
            "overall_reliability": (
                self._float(
                    reliability.get(
                        "overall_score",
                        0.0,
                    )
                )
                >= self.MIN_OVERALL_RELIABILITY
            ),
            "consensus_quality": (
                consensus.get(
                    "consensus_quality",
                    0.0,
                )
                >= self.MIN_CONSENSUS_QUALITY
            ),
            "agreement": (
                consensus.get(
                    "agreement_score",
                    0.0,
                )
                >= self.MIN_CONSENSUS_AGREEMENT
            ),
            "conflict_score": (
                consensus.get(
                    "conflict_score",
                    1.0,
                )
                <= self.MAX_CONFLICT_SCORE
            ),
            "conflict_severity": (
                conflict.get(
                    "severity_score",
                    1.0,
                )
                <= self.MAX_CONFLICT_SEVERITY
            ),
            "support_margin": (
                candidate_margin
                >= self.MIN_SUPPORT_MARGIN
            ),
            "support_share": (
                support_share
                >= self.MIN_SUPPORT_SHARE
            ),
            "candidate_component_support": (
                len(
                    candidate_components
                )
                >= self.MIN_MEANINGFUL_COMPONENTS
            ),
            "strong_candidate_components": (
                strong_candidate_components
                >= 1
            ),
            "no_meaningful_opposition": (
                meaningful_opposing
                <= self.MAX_OPPOSING_MEANINGFUL_COMPONENTS
            ),
        }

        passed = sum(
            1
            for value in checks.values()
            if value
        )

        total = len(checks)

        readiness_score = (
            passed / total
            if total
            else 0.0
        )

        blockers: List[str] = []

        if not checks[
            "overall_reliability"
        ]:
            blockers.append(
                "OVERALL_RELIABILITY_BELOW_THRESHOLD"
            )

        if not checks[
            "consensus_quality"
        ]:
            blockers.append(
                "CONSENSUS_QUALITY_BELOW_THRESHOLD"
            )

        if not checks[
            "agreement"
        ]:
            blockers.append(
                "AGREEMENT_BELOW_THRESHOLD"
            )

        if not checks[
            "conflict_score"
        ]:
            blockers.append(
                "CONFLICT_SCORE_TOO_HIGH"
            )

        if not checks[
            "conflict_severity"
        ]:
            blockers.append(
                "CONFLICT_SEVERITY_TOO_HIGH"
            )

        if not checks[
            "support_margin"
        ]:
            blockers.append(
                "SUPPORT_MARGIN_TOO_SMALL"
            )

        if not checks[
            "support_share"
        ]:
            blockers.append(
                "SUPPORT_SHARE_TOO_SMALL"
            )

        if not checks[
            "candidate_component_support"
        ]:
            blockers.append(
                "INSUFFICIENT_MEANINGFUL_COMPONENT_SUPPORT"
            )

        if not checks[
            "strong_candidate_components"
        ]:
            blockers.append(
                "NO_STRONG_CANDIDATE_COMPONENT"
            )

        if not checks[
            "no_meaningful_opposition"
        ]:
            blockers.append(
                "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
            )

        if not blockers:
            status = "READY"
        elif readiness_score >= 0.60:
            status = "CONDITIONALLY_READY"
        else:
            status = "NOT_READY"

        return {
            "tonic": tonic,
            "candidate_support": self._round(
                candidate_support
            ),
            "support_share": self._round(
                support_share
            ),
            "support_margin": self._round(
                candidate_margin
            ),
            "support_rank": (
                1
                if candidate_support >= top_support
                else 2
            ),
            "supporting_components": (
                candidate_components
            ),
            "strong_candidate_components": (
                strong_candidate_components
            ),
            "opposing_components": (
                opposing_components
            ),
            "meaningful_opposing_components": (
                meaningful_opposing
            ),
            "checks": checks,
            "passed_checks": passed,
            "total_checks": total,
            "readiness_score": self._round(
                readiness_score
            ),
            "status": status,
            "blockers": blockers,
        }

    # ---------------------------------------------------------
    # Global readiness
    # ---------------------------------------------------------

    def _global_readiness(
        self,
        candidate_results: List[Dict[str, Any]],
        consensus: Dict[str, Any],
        reliability: Dict[str, Any],
        conflict: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not candidate_results:
            return {
                "status": "NOT_READY",
                "readiness_score": 0.0,
                "top_candidate": None,
                "top_readiness": 0.0,
                "reason": [
                    "NO_CANDIDATE_EVIDENCE"
                ],
            }

        ordered = sorted(
            candidate_results,
            key=lambda row: (
                row.get(
                    "readiness_score",
                    0.0,
                ),
                row.get(
                    "candidate_support",
                    0.0,
                ),
            ),
            reverse=True,
        )

        top = ordered[0]

        if len(ordered) > 1:
            second = ordered[1]
        else:
            second = None

        readiness = self._clamp(
            self._float(
                top.get(
                    "readiness_score",
                    0.0,
                )
            )
        )

        global_blockers: List[str] = []

        if (
            reliability.get(
                "overall_score",
                0.0,
            )
            < self.MIN_OVERALL_RELIABILITY
        ):
            global_blockers.append(
                "OVERALL_RELIABILITY_BELOW_THRESHOLD"
            )

        if (
            consensus.get(
                "consensus_quality",
                0.0,
            )
            < self.MIN_CONSENSUS_QUALITY
        ):
            global_blockers.append(
                "CONSENSUS_QUALITY_BELOW_THRESHOLD"
            )

        if (
            consensus.get(
                "agreement_score",
                0.0,
            )
            < self.MIN_CONSENSUS_AGREEMENT
        ):
            global_blockers.append(
                "CONSENSUS_AGREEMENT_BELOW_THRESHOLD"
            )

        if (
            conflict.get(
                "severity_score",
                1.0,
            )
            > self.MAX_CONFLICT_SEVERITY
        ):
            global_blockers.append(
                "CONFLICT_SEVERITY_TOO_HIGH"
            )

        if (
            conflict.get(
                "conflict_score",
                1.0,
            )
            > self.MAX_CONFLICT_SCORE
        ):
            global_blockers.append(
                "CONFLICT_SCORE_TOO_HIGH"
            )

        if (
            conflict.get(
                "meaningful_G_components",
                0,
            )
            > 0
            and conflict.get(
                "meaningful_C_components",
                0,
            )
            > 0
        ):
            global_blockers.append(
                "MEANINGFUL_G_C_CONFLICT"
            )

        if global_blockers:
            status = "NOT_READY"
        elif readiness >= 0.80:
            status = "READY"
        elif readiness >= 0.60:
            status = "CONDITIONALLY_READY"
        else:
            status = "NOT_READY"

        return {
            "status": status,
            "readiness_score": self._round(
                readiness
            ),
            "top_candidate": top.get(
                "tonic"
            ),
            "top_readiness": self._round(
                readiness
            ),
            "second_candidate": (
                second.get("tonic")
                if second
                else None
            ),
            "second_readiness": (
                self._round(
                    second.get(
                        "readiness_score",
                        0.0,
                    )
                )
                if second
                else 0.0
            ),
            "global_blockers": global_blockers,
        }

    # ---------------------------------------------------------
    # Full analysis
    # ---------------------------------------------------------

    def analyze(
        self,
        consensus_data: Dict[str, Any],
        reliability_data: Dict[str, Any],
        conflict_data: Dict[str, Any],
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        consensus = self._extract_consensus(
            consensus_data
        )

        reliability = (
            self._extract_reliability(
                reliability_data
            )
        )

        conflict = (
            self._extract_conflict(
                conflict_data
            )
        )

        preferences = (
            self._extract_preferences(
                consensus_data,
                reliability_data,
                conflict_data,
            )
        )

        # This analyzer currently supports the two
        # candidate tonic names used throughout the
        # evidence pipeline.
        tonic_candidates = [
            "G",
            "C",
        ]

        if candidates:
            # Preserve known ordering when supplied.
            # 7 = G, 0 = C.
            mapped: List[str] = []

            for value in candidates:
                try:
                    pc = int(value) % 12
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                if pc == 7:
                    mapped.append("G")
                elif pc == 0:
                    mapped.append("C")

            if mapped:
                tonic_candidates = list(
                    dict.fromkeys(mapped)
                )

        candidate_results = []

        for tonic in tonic_candidates:
            candidate_results.append(
                self._candidate_readiness(
                    tonic=tonic,
                    consensus=consensus,
                    reliability=reliability,
                    conflict=conflict,
                    preferences=preferences,
                )
            )

        global_result = (
            self._global_readiness(
                candidate_results,
                consensus,
                reliability,
                conflict,
            )
        )

        # Readiness is never a tonic decision.
        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,

            "input": {
                "candidate_count": len(
                    candidate_results
                ),
                "candidates": tonic_candidates,
                "consensus_status": consensus[
                    "status"
                ],
                "reliability": reliability[
                    "overall_score"
                ],
                "conflict_severity": conflict[
                    "severity_score"
                ],
            },

            "thresholds": {
                "min_overall_reliability": (
                    self.MIN_OVERALL_RELIABILITY
                ),
                "min_consensus_quality": (
                    self.MIN_CONSENSUS_QUALITY
                ),
                "min_consensus_agreement": (
                    self.MIN_CONSENSUS_AGREEMENT
                ),
                "max_conflict_score": (
                    self.MAX_CONFLICT_SCORE
                ),
                "max_conflict_severity": (
                    self.MAX_CONFLICT_SEVERITY
                ),
                "min_support_margin": (
                    self.MIN_SUPPORT_MARGIN
                ),
                "min_support_share": (
                    self.MIN_SUPPORT_SHARE
                ),
                "min_meaningful_components": (
                    self.MIN_MEANINGFUL_COMPONENTS
                ),
                "max_opposing_meaningful_components": (
                    self.MAX_OPPOSING_MEANINGFUL_COMPONENTS
                ),
            },

            "evidence_preferences": preferences,

            "readiness": {
                "global": global_result,
                "candidates": candidate_results,
            },

            "decision": {
                "status": "EVIDENCE_ONLY",
                "tonic_pitch_class": None,
                "tonic_name": None,
                "maqam": None,
                "jins": None,
                "confidence": None,
                "reason": [
                    "TONIC_DECISION_READINESS_ONLY",
                    "READINESS_IS_NOT_A_TONIC_DECISION",
                    (
                        "NO_TONIC_DECISION"
                    ),
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
                "conflict_hidden": False,
                "readiness_promoted_to_decision": False,
            },
        }

    # ---------------------------------------------------------
    # File API
    # ---------------------------------------------------------

    def analyze_files(
        self,
        consensus_path: str,
        reliability_path: str,
        conflict_path: str,
        output_path: str,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        consensus_data = self._load(
            consensus_path
        )

        reliability_data = self._load(
            reliability_path
        )

        conflict_data = self._load(
            conflict_path
        )

        result = self.analyze(
            consensus_data=consensus_data,
            reliability_data=reliability_data,
            conflict_data=conflict_data,
            candidates=candidates,
        )

        self._save(
            output_path,
            result,
        )

        return result

    def analyze_file(
        self,
        consensus_path: str,
        reliability_path: str,
        conflict_path: str,
        output_path: str,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        return self.analyze_files(
            consensus_path=consensus_path,
            reliability_path=reliability_path,
            conflict_path=conflict_path,
            output_path=output_path,
            candidates=candidates,
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PhoenixVoiceEngine "
            "Tonic Decision Readiness "
            "Analyzer V1.0"
        )
    )

    parser.add_argument(
        "consensus_path"
    )

    parser.add_argument(
        "reliability_path"
    )

    parser.add_argument(
        "conflict_path"
    )

    parser.add_argument(
        "output_path"
    )

    parser.add_argument(
        "--candidates",
        nargs="*",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    analyzer = (
        TonicDecisionReadinessAnalyzer()
    )

    result = analyzer.analyze_files(
        consensus_path=args.consensus_path,
        reliability_path=args.reliability_path,
        conflict_path=args.conflict_path,
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