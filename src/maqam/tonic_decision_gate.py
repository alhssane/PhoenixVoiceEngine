"""
PhoenixVoiceEngine
Tonic Decision Gate V1.0

Purpose
-------
Safety gate between evidence/readiness analysis and a future
Tonic Decision Engine.

This module DOES NOT:
- select a tonic
- modify pitch
- modify timing
- modify performance
- modify source scores
- select maqam
- select jins
- override previous decisions

It only determines whether a tonic decision is permitted.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TonicDecisionGate:
    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    # ---------------------------------------------------------
    # Gate thresholds
    # ---------------------------------------------------------

    MIN_READINESS_SCORE = 0.80
    MIN_OVERALL_RELIABILITY = 0.55
    MIN_CONSENSUS_QUALITY = 0.60
    MIN_AGREEMENT_SCORE = 0.60

    MAX_CONFLICT_SCORE = 0.35
    MAX_CONFLICT_SEVERITY = 0.40

    MIN_SUPPORT_MARGIN = 0.15
    MIN_SUPPORT_SHARE = 0.60

    # Meaningful opposing evidence blocks the gate.
    MAX_MEANINGFUL_OPPOSING_COMPONENTS = 0

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
    def _bool(
        value: Any,
        default: bool = False,
    ) -> bool:

        if isinstance(
            value,
            bool,
        ):
            return value

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
    # Readiness extraction
    # ---------------------------------------------------------

    def _extract_readiness(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        readiness = data.get(
            "readiness",
            {},
        )

        if not isinstance(
            readiness,
            dict,
        ):
            readiness = {}

        global_result = readiness.get(
            "global",
            {},
        )

        if not isinstance(
            global_result,
            dict,
        ):
            global_result = {}

        candidates = readiness.get(
            "candidates",
            [],
        )

        if not isinstance(
            candidates,
            list,
        ):
            candidates = []

        return {
            "status": global_result.get(
                "status",
                "UNKNOWN",
            ),
            "readiness_score": self._clamp(
                self._float(
                    global_result.get(
                        "readiness_score",
                        0.0,
                    )
                )
            ),
            "top_candidate": global_result.get(
                "top_candidate"
            ),
            "top_readiness": self._clamp(
                self._float(
                    global_result.get(
                        "top_readiness",
                        0.0,
                    )
                )
            ),
            "second_candidate": global_result.get(
                "second_candidate"
            ),
            "second_readiness": self._clamp(
                self._float(
                    global_result.get(
                        "second_readiness",
                        0.0,
                    )
                )
            ),
            "global_blockers": list(
                global_result.get(
                    "global_blockers",
                    [],
                )
            ),
            "candidates": candidates,
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

        return {
            "overall_score": self._clamp(
                self._float(
                    reliability.get(
                        "overall_score",
                        0.0,
                    )
                )
            )
        }

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
            "top_tonic": quality.get(
                "top_tonic"
            ),
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
            "meaningful_G_components": int(
                self._float(
                    severity.get(
                        "meaningful_G_components",
                        0,
                    )
                )
            ),
            "meaningful_C_components": int(
                self._float(
                    severity.get(
                        "meaningful_C_components",
                        0,
                    )
                )
            ),
            "weighted_preference": balance.get(
                "weighted_preference",
                "TIE",
            ),
            "dominance": self._clamp(
                self._float(
                    balance.get(
                        "dominance",
                        0.0,
                    )
                )
            ),
        }

    # ---------------------------------------------------------
    # Gate checks
    # ---------------------------------------------------------

    def _build_checks(
        self,
        readiness: Dict[str, Any],
        reliability: Dict[str, Any],
        consensus: Dict[str, Any],
        conflict: Dict[str, Any],
    ) -> Dict[str, bool]:

        meaningful_opposition = (
            conflict[
                "meaningful_G_components"
            ] > 0
            and
            conflict[
                "meaningful_C_components"
            ] > 0
        )

        return {
            "readiness_status_ready": (
                readiness["status"]
                == "READY"
            ),

            "readiness_score": (
                readiness[
                    "readiness_score"
                ]
                >= self.MIN_READINESS_SCORE
            ),

            "overall_reliability": (
                reliability[
                    "overall_score"
                ]
                >= self.MIN_OVERALL_RELIABILITY
            ),

            "consensus_quality": (
                consensus[
                    "consensus_quality"
                ]
                >= self.MIN_CONSENSUS_QUALITY
            ),

            "agreement_score": (
                consensus[
                    "agreement_score"
                ]
                >= self.MIN_AGREEMENT_SCORE
            ),

            "conflict_score": (
                consensus[
                    "conflict_score"
                ]
                <= self.MAX_CONFLICT_SCORE
            ),

            "conflict_severity": (
                conflict[
                    "severity_score"
                ]
                <= self.MAX_CONFLICT_SEVERITY
            ),

            "support_margin": (
                consensus[
                    "support_margin"
                ]
                >= self.MIN_SUPPORT_MARGIN
            ),

            "support_share": (
                consensus[
                    "support_share"
                ]
                >= self.MIN_SUPPORT_SHARE
            ),

            "no_meaningful_G_C_conflict": (
                not meaningful_opposition
            ),
        }

    # ---------------------------------------------------------
    # Blocker extraction
    # ---------------------------------------------------------

    def _build_blockers(
        self,
        checks: Dict[str, bool],
        readiness: Dict[str, Any],
    ) -> List[str]:

        blockers: List[str] = []

        mapping = {
            "readiness_status_ready":
                "READINESS_STATUS_NOT_READY",

            "readiness_score":
                "READINESS_SCORE_BELOW_THRESHOLD",

            "overall_reliability":
                "OVERALL_RELIABILITY_BELOW_THRESHOLD",

            "consensus_quality":
                "CONSENSUS_QUALITY_BELOW_THRESHOLD",

            "agreement_score":
                "AGREEMENT_BELOW_THRESHOLD",

            "conflict_score":
                "CONFLICT_SCORE_TOO_HIGH",

            "conflict_severity":
                "CONFLICT_SEVERITY_TOO_HIGH",

            "support_margin":
                "SUPPORT_MARGIN_TOO_SMALL",

            "support_share":
                "SUPPORT_SHARE_TOO_SMALL",

            "no_meaningful_G_C_conflict":
                "MEANINGFUL_G_C_CONFLICT",
        }

        for key, reason in mapping.items():

            if not checks.get(
                key,
                False,
            ):
                blockers.append(reason)

        # Preserve blockers already discovered by
        # the readiness analyzer.
        for blocker in readiness.get(
            "global_blockers",
            [],
        ):

            if blocker not in blockers:
                blockers.append(
                    blocker
                )

        return blockers

    # ---------------------------------------------------------
    # Gate status
    # ---------------------------------------------------------

    def _evaluate_gate(
        self,
        checks: Dict[str, bool],
        blockers: List[str],
    ) -> Dict[str, Any]:

        all_passed = all(
            checks.values()
        )

        if all_passed:
            status = "OPEN"
            level = "ALLOW"

        else:
            status = "CLOSED"
            level = "ABSTAIN"

        return {
            "status": status,
            "level": level,
            "decision_allowed": all_passed,
            "abstention_required": not all_passed,
            "passed_checks": sum(
                1
                for value in checks.values()
                if value
            ),
            "total_checks": len(
                checks
            ),
            "blockers": blockers,
        }

    # ---------------------------------------------------------
    # Candidate gate
    # ---------------------------------------------------------

    def _candidate_gate(
        self,
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:

        checks = candidate.get(
            "checks",
            {},
        )

        if not isinstance(
            checks,
            dict,
        ):
            checks = {}

        status = candidate.get(
            "status",
            "NOT_READY",
        )

        readiness_score = self._clamp(
            self._float(
                candidate.get(
                    "readiness_score",
                    0.0,
                )
            )
        )

        allowed = (
            status == "READY"
            and
            readiness_score
            >= self.MIN_READINESS_SCORE
            and
            all(
                bool(v)
                for v in checks.values()
            )
        )

        return {
            "tonic": candidate.get(
                "tonic"
            ),
            "status": (
                "OPEN"
                if allowed
                else "CLOSED"
            ),
            "decision_allowed": allowed,
            "readiness_status": status,
            "readiness_score": self._round(
                readiness_score
            ),
            "supporting_components": list(
                candidate.get(
                    "supporting_components",
                    [],
                )
            ),
            "opposing_components": list(
                candidate.get(
                    "opposing_components",
                    [],
                )
            ),
            "blockers": list(
                candidate.get(
                    "blockers",
                    [],
                )
            ),
        }

    # ---------------------------------------------------------
    # Full analysis
    # ---------------------------------------------------------

    def analyze(
        self,
        readiness_data: Dict[str, Any],
        reliability_data: Dict[str, Any],
        consensus_data: Dict[str, Any],
        conflict_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        readiness = (
            self._extract_readiness(
                readiness_data
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

        conflict = (
            self._extract_conflict(
                conflict_data
            )
        )

        checks = self._build_checks(
            readiness=readiness,
            reliability=reliability,
            consensus=consensus,
            conflict=conflict,
        )

        blockers = self._build_blockers(
            checks=checks,
            readiness=readiness,
        )

        gate = self._evaluate_gate(
            checks=checks,
            blockers=blockers,
        )

        candidate_gates = []

        for candidate in readiness.get(
            "candidates",
            [],
        ):

            if isinstance(
                candidate,
                dict,
            ):
                candidate_gates.append(
                    self._candidate_gate(
                        candidate
                    )
                )

        # The gate never converts an OPEN state
        # into an actual tonic decision.
        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,

            "input": {
                "readiness_status": readiness[
                    "status"
                ],
                "readiness_score": readiness[
                    "readiness_score"
                ],
                "overall_reliability": reliability[
                    "overall_score"
                ],
                "consensus_quality": consensus[
                    "consensus_quality"
                ],
                "agreement_score": consensus[
                    "agreement_score"
                ],
                "conflict_score": consensus[
                    "conflict_score"
                ],
                "conflict_severity": conflict[
                    "severity_score"
                ],
            },

            "thresholds": {
                "min_readiness_score":
                    self.MIN_READINESS_SCORE,

                "min_overall_reliability":
                    self.MIN_OVERALL_RELIABILITY,

                "min_consensus_quality":
                    self.MIN_CONSENSUS_QUALITY,

                "min_agreement_score":
                    self.MIN_AGREEMENT_SCORE,

                "max_conflict_score":
                    self.MAX_CONFLICT_SCORE,

                "max_conflict_severity":
                    self.MAX_CONFLICT_SEVERITY,

                "min_support_margin":
                    self.MIN_SUPPORT_MARGIN,

                "min_support_share":
                    self.MIN_SUPPORT_SHARE,

                "max_meaningful_opposing_components":
                    self.MAX_MEANINGFUL_OPPOSING_COMPONENTS,
            },

            "gate": gate,

            "checks": checks,

            "candidate_gates": candidate_gates,

            "readiness_context": {
                "status": readiness[
                    "status"
                ],
                "score": readiness[
                    "readiness_score"
                ],
                "top_candidate": readiness[
                    "top_candidate"
                ],
                "global_blockers": readiness[
                    "global_blockers"
                ],
            },

            "decision": {
                "status": "EVIDENCE_ONLY",
                "tonic_pitch_class": None,
                "tonic_name": None,
                "maqam": None,
                "jins": None,
                "confidence": None,
                "reason": [
                    "TONIC_DECISION_GATE_ONLY",
                    (
                        "GATE_DOES_NOT_SELECT_TONIC"
                    ),
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
                "readiness_promoted_to_decision": False,
                "gate_selected_tonic": False,
                "gate_modified_source": False,
            },
        }

    # ---------------------------------------------------------
    # File API
    # ---------------------------------------------------------

    def analyze_files(
        self,
        readiness_path: str,
        reliability_path: str,
        consensus_path: str,
        conflict_path: str,
        output_path: str,
    ) -> Dict[str, Any]:

        readiness_data = self._load(
            readiness_path
        )

        reliability_data = self._load(
            reliability_path
        )

        consensus_data = self._load(
            consensus_path
        )

        conflict_data = self._load(
            conflict_path
        )

        result = self.analyze(
            readiness_data=readiness_data,
            reliability_data=reliability_data,
            consensus_data=consensus_data,
            conflict_data=conflict_data,
        )

        self._save(
            output_path,
            result,
        )

        return result

    def analyze_file(
        self,
        readiness_path: str,
        reliability_path: str,
        consensus_path: str,
        conflict_path: str,
        output_path: str,
    ) -> Dict[str, Any]:

        return self.analyze_files(
            readiness_path=readiness_path,
            reliability_path=reliability_path,
            consensus_path=consensus_path,
            conflict_path=conflict_path,
            output_path=output_path,
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PhoenixVoiceEngine "
            "Tonic Decision Gate V1.0"
        )
    )

    parser.add_argument(
        "readiness_path"
    )

    parser.add_argument(
        "reliability_path"
    )

    parser.add_argument(
        "consensus_path"
    )

    parser.add_argument(
        "conflict_path"
    )

    parser.add_argument(
        "output_path"
    )

    args = parser.parse_args()

    analyzer = TonicDecisionGate()

    result = analyzer.analyze_files(
        readiness_path=args.readiness_path,
        reliability_path=args.reliability_path,
        consensus_path=args.consensus_path,
        conflict_path=args.conflict_path,
        output_path=args.output_path,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )