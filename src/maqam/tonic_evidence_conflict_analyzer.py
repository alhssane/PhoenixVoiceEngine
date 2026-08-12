"""
PhoenixVoiceEngine
Tonic Evidence Conflict Analyzer V1.0

Purpose
-------
Analyze conflicts between independent tonic evidence sources.

This module is analytical only.

It does NOT:
- modify pitch
- modify timing
- modify performance
- modify source scores
- override previous decisions
- make a tonic decision
- make a maqam decision
- make a jins decision

The output remains EVIDENCE_ONLY.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicEvidenceConflictAnalyzer:
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

    TONICS = ("G", "C")

    # Separation below this value is treated as weak.
    MIN_MEANINGFUL_SEPARATION = 0.05

    # Conflict severity thresholds.
    LOW_CONFLICT = 0.25
    MODERATE_CONFLICT = 0.50
    HIGH_CONFLICT = 0.70

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
    # Numeric helpers
    # ---------------------------------------------------------

    @staticmethod
    def _float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _int(
        value: Any,
        default: int = 0,
    ) -> int:
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
        return max(
            low,
            min(high, float(value)),
        )

    @staticmethod
    def _round(
        value: float,
    ) -> float:
        return round(float(value), 6)

    # ---------------------------------------------------------
    # Preference extraction
    # ---------------------------------------------------------

    def _extract_preferences(
        self,
        consensus_data: Dict[str, Any],
        reliability_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:

        preferences = consensus_data.get(
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

        return {
            component: "TIE"
            for component in self.COMPONENTS
        }

    # ---------------------------------------------------------
    # Reliability extraction
    # ---------------------------------------------------------

    def _extract_reliability(
        self,
        reliability_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:

        result: Dict[str, Dict[str, Any]] = {}

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

        return result

    # ---------------------------------------------------------
    # Consensus extraction
    # ---------------------------------------------------------

    def _extract_consensus(
        self,
        consensus_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        consensus = consensus_data.get(
            "consensus",
            {}
        )

        if not isinstance(
            consensus,
            dict,
        ):
            consensus = {}

        agreement = consensus.get(
            "agreement",
            {}
        )

        quality = consensus.get(
            "quality",
            {}
        )

        weighted_support = consensus.get(
            "weighted_tonic_support",
            {}
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
            "dominant_tonic": agreement.get(
                "dominant_tonic"
            ),
            "dominant_share": self._clamp(
                self._float(
                    agreement.get(
                        "dominant_share",
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
            "weighted_support": {
                str(k): self._clamp(
                    self._float(v)
                )
                for k, v
                in weighted_support.items()
            },
            "top_tonic": quality.get(
                "top_tonic"
            ),
            "support_share": self._clamp(
                self._float(
                    quality.get(
                        "support_share",
                        0.0,
                    )
                )
            ),
            "support_margin": self._float(
                quality.get(
                    "support_margin",
                    0.0,
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
    # Evidence groups
    # ---------------------------------------------------------

    def _build_groups(
        self,
        preferences: Dict[str, str],
    ) -> Dict[str, List[str]]:

        groups: Dict[str, List[str]] = {
            "G": [],
            "C": [],
            "TIE": [],
            "OTHER": [],
        }

        for component in self.COMPONENTS:
            tonic = preferences.get(
                component,
                "TIE",
            )

            if tonic == "G":
                groups["G"].append(
                    component
                )
            elif tonic == "C":
                groups["C"].append(
                    component
                )
            elif tonic == "TIE":
                groups["TIE"].append(
                    component
                )
            else:
                groups["OTHER"].append(
                    component
                )

        return groups

    # ---------------------------------------------------------
    # Component conflict classification
    # ---------------------------------------------------------

    def _component_conflict_rows(
        self,
        preferences: Dict[str, str],
        reliability: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        rows: List[Dict[str, Any]] = []

        for component in self.COMPONENTS:

            tonic = preferences.get(
                component,
                "TIE",
            )

            rel = reliability.get(
                component,
                {},
            )

            row = {
                "component": component,
                "preferred_tonic": tonic,
                "reliability": self._clamp(
                    self._float(
                        rel.get(
                            "reliability_score",
                            0.0,
                        )
                    )
                ),
                "strength": self._clamp(
                    self._float(
                        rel.get(
                            "strength",
                            0.0,
                        )
                    )
                ),
                "separation": self._clamp(
                    self._float(
                        rel.get(
                            "separation",
                            0.0,
                        )
                    )
                ),
                "meaningful_separation": bool(
                    rel.get(
                        "meaningful_separation",
                        False,
                    )
                ),
                "availability": self._clamp(
                    self._float(
                        rel.get(
                            "availability",
                            0.0,
                        )
                    )
                ),
            }

            if tonic == "G":
                row["evidence_group"] = "G"
            elif tonic == "C":
                row["evidence_group"] = "C"
            else:
                row["evidence_group"] = "NEUTRAL"

            rows.append(row)

        return rows

    # ---------------------------------------------------------
    # Effective conflict weight
    # ---------------------------------------------------------

    def _effective_weight(
        self,
        row: Dict[str, Any],
    ) -> float:

        reliability = self._clamp(
            self._float(
                row.get(
                    "reliability",
                    0.0,
                )
            )
        )

        availability = self._clamp(
            self._float(
                row.get(
                    "availability",
                    0.0,
                )
            )
        )

        strength = self._clamp(
            self._float(
                row.get(
                    "strength",
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

        # Conflict analysis must consider whether the
        # component actually separates the candidates.
        separation_factor = self._clamp(
            separation / 0.25
        )

        return self._clamp(
            reliability
            * availability
            * strength
            * separation_factor
        )

    # ---------------------------------------------------------
    # Conflict balance
    # ---------------------------------------------------------

    def _conflict_balance(
        self,
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        g_support = 0.0
        c_support = 0.0

        g_components: List[str] = []
        c_components: List[str] = []

        for row in rows:

            group = row.get(
                "evidence_group"
            )

            weight = self._effective_weight(
                row
            )

            if group == "G":
                g_support += weight
                g_components.append(
                    row["component"]
                )

            elif group == "C":
                c_support += weight
                c_components.append(
                    row["component"]
                )

        total = (
            g_support
            + c_support
        )

        if total > 0:
            g_share = (
                g_support / total
            )
            c_share = (
                c_support / total
            )
        else:
            g_share = 0.0
            c_share = 0.0

        balance = (
            1.0
            - abs(
                g_share
                - c_share
            )
        )

        if total > 0:
            dominance = abs(
                g_support
                - c_support
            ) / total
        else:
            dominance = 0.0

        if (
            g_support > c_support
        ):
            preferred = "G"
        elif (
            c_support > g_support
        ):
            preferred = "C"
        else:
            preferred = "TIE"

        return {
            "G": {
                "support": self._round(
                    g_support
                ),
                "share": self._round(
                    g_share
                ),
                "components": g_components,
            },
            "C": {
                "support": self._round(
                    c_support
                ),
                "share": self._round(
                    c_share
                ),
                "components": c_components,
            },
            "total_support": self._round(
                total
            ),
            "balance": self._round(
                balance
            ),
            "dominance": self._round(
                dominance
            ),
            "weighted_preference": preferred,
        }

    # ---------------------------------------------------------
    # Conflict severity
    # ---------------------------------------------------------

    def _conflict_severity(
        self,
        balance: Dict[str, Any],
        consensus: Dict[str, Any],
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        conflict_score = self._clamp(
            self._float(
                consensus.get(
                    "conflict_score",
                    0.0,
                )
            )
        )

        balance_score = self._clamp(
            self._float(
                balance.get(
                    "balance",
                    0.0,
                )
            )
        )

        # Count meaningful opposing components.
        g_meaningful = 0
        c_meaningful = 0

        for row in rows:

            if not row.get(
                "meaningful_separation",
                False,
            ):
                continue

            if row.get(
                "evidence_group"
            ) == "G":
                g_meaningful += 1

            elif row.get(
                "evidence_group"
            ) == "C":
                c_meaningful += 1

        opposing_presence = self._clamp(
            min(
                g_meaningful,
                c_meaningful,
            ) / 2.0
        )

        severity = self._clamp(
            0.45 * conflict_score
            + 0.30 * balance_score
            + 0.25 * opposing_presence
        )

        if severity >= self.HIGH_CONFLICT:
            label = "HIGH"
        elif severity >= self.MODERATE_CONFLICT:
            label = "MODERATE"
        elif severity >= self.LOW_CONFLICT:
            label = "LOW"
        else:
            label = "MINIMAL"

        return {
            "score": self._round(
                severity
            ),
            "label": label,
            "conflict_score": self._round(
                conflict_score
            ),
            "balance_score": self._round(
                balance_score
            ),
            "meaningful_G_components": (
                g_meaningful
            ),
            "meaningful_C_components": (
                c_meaningful
            ),
            "opposing_presence": self._round(
                opposing_presence
            ),
        }

    # ---------------------------------------------------------
    # Strongest evidence on each side
    # ---------------------------------------------------------

    def _strongest_by_group(
        self,
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        result = {
            "G": None,
            "C": None,
        }

        for group in ("G", "C"):

            candidates = [
                row
                for row in rows
                if row.get(
                    "evidence_group"
                ) == group
            ]

            if not candidates:
                continue

            ordered = sorted(
                candidates,
                key=lambda row: (
                    self._effective_weight(
                        row
                    ),
                    self._float(
                        row.get(
                            "reliability",
                            0.0,
                        )
                    ),
                ),
                reverse=True,
            )

            top = ordered[0]

            result[group] = {
                "component": top[
                    "component"
                ],
                "effective_weight": self._round(
                    self._effective_weight(
                        top
                    )
                ),
                "reliability": top[
                    "reliability"
                ],
                "strength": top[
                    "strength"
                ],
                "separation": top[
                    "separation"
                ],
                "meaningful_separation": top[
                    "meaningful_separation"
                ],
            }

        return result

    # ---------------------------------------------------------
    # Decision safety
    # ---------------------------------------------------------

    def _decision_safety(
        self,
        severity: Dict[str, Any],
        balance: Dict[str, Any],
        consensus: Dict[str, Any],
    ) -> Dict[str, Any]:

        severity_score = self._clamp(
            self._float(
                severity.get(
                    "score",
                    0.0,
                )
            )
        )

        balance_score = self._clamp(
            self._float(
                balance.get(
                    "balance",
                    0.0,
                )
            )
        )

        support_margin = abs(
            self._float(
                consensus.get(
                    "support_margin",
                    0.0,
                )
            )
        )

        # A small margin combined with meaningful conflict
        # means a tonic decision is unsafe.
        unsafe = (
            severity_score >= 0.50
            or (
                balance_score >= 0.60
                and support_margin < 0.15
            )
        )

        if unsafe:
            level = "UNSAFE"
        elif severity_score >= 0.30:
            level = "CAUTION"
        else:
            level = "RELATIVELY_SAFE"

        return {
            "tonic_decision_safe": False,
            "level": level,
            "conflict_requires_abstention": unsafe,
            "reason": (
                "MEANINGFUL_EVIDENCE_CONFLICT"
                if unsafe
                else "CONSENSUS_NOT_A_DECISION"
            ),
        }

    # ---------------------------------------------------------
    # Full analysis
    # ---------------------------------------------------------

    def analyze(
        self,
        consensus_data: Dict[str, Any],
        reliability_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        preferences = (
            self._extract_preferences(
                consensus_data,
                reliability_data,
            )
        )

        reliability = (
            self._extract_reliability(
                reliability_data
            )
        )

        consensus = (
            self._extract_consensus(
                consensus_data
            )
        )

        groups = self._build_groups(
            preferences
        )

        component_rows = (
            self._component_conflict_rows(
                preferences,
                reliability,
            )
        )

        balance = self._conflict_balance(
            component_rows
        )

        severity = self._conflict_severity(
            balance,
            consensus,
            component_rows,
        )

        strongest = (
            self._strongest_by_group(
                component_rows
            )
        )

        decision_safety = (
            self._decision_safety(
                severity,
                balance,
                consensus,
            )
        )

        original_decision = (
            consensus_data.get(
                "decision",
                {}
            )
        )

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,

            "input": {
                "component_count": len(
                    self.COMPONENTS
                ),
                "reliability_available": (
                    reliability_data is not None
                ),
                "original_consensus_status": (
                    original_decision.get(
                        "status"
                    )
                ),
            },

            "evidence_preferences": preferences,

            "evidence_groups": groups,

            "components": component_rows,

            "conflict": {
                "balance": balance,
                "severity": severity,
                "strongest_by_group": strongest,
                "consensus_context": {
                    "agreement_score": consensus[
                        "agreement_score"
                    ],
                    "conflict_score": consensus[
                        "conflict_score"
                    ],
                    "weighted_agreement": consensus[
                        "weighted_agreement"
                    ],
                    "support_share": consensus[
                        "support_share"
                    ],
                    "support_margin": consensus[
                        "support_margin"
                    ],
                    "consensus_quality": consensus[
                        "consensus_quality"
                    ],
                },
            },

            "decision_safety": decision_safety,

            "decision": {
                "status": "EVIDENCE_ONLY",
                "tonic_pitch_class": None,
                "tonic_name": None,
                "maqam": None,
                "jins": None,
                "confidence": None,
                "reason": [
                    "TONIC_EVIDENCE_CONFLICT_ANALYSIS_ONLY",
                    "EVIDENCE_CONFLICT_REMAINS_VISIBLE",
                    "NO_TONIC_DECISION",
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
                "evidence_preference_changed": False,
            },
        }

    # ---------------------------------------------------------
    # File API
    # ---------------------------------------------------------

    def analyze_files(
        self,
        consensus_path: str,
        output_path: str,
        reliability_path: Optional[str] = None,
    ) -> Dict[str, Any]:

        consensus_data = self._load(
            consensus_path
        )

        reliability_data = (
            self._load(reliability_path)
            if reliability_path
            else None
        )

        result = self.analyze(
            consensus_data=consensus_data,
            reliability_data=reliability_data,
        )

        self._save(
            output_path,
            result,
        )

        return result

    def analyze_file(
        self,
        consensus_path: str,
        output_path: str,
        reliability_path: Optional[str] = None,
    ) -> Dict[str, Any]:

        return self.analyze_files(
            consensus_path=consensus_path,
            output_path=output_path,
            reliability_path=reliability_path,
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PhoenixVoiceEngine "
            "Tonic Evidence Conflict Analyzer V1.0"
        )
    )

    parser.add_argument(
        "consensus_path"
    )

    parser.add_argument(
        "output_path"
    )

    parser.add_argument(
        "--reliability"
    )

    args = parser.parse_args()

    analyzer = (
        TonicEvidenceConflictAnalyzer()
    )

    result = analyzer.analyze_files(
        consensus_path=args.consensus_path,
        output_path=args.output_path,
        reliability_path=args.reliability,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )