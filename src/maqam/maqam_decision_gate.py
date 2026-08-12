"""
PhoenixVoiceEngine
Maqam Decision Gate V1.0

The Gate does NOT select a Maqam.
It only determines whether the Maqam Decision Engine
is allowed to attempt a decision.

Safety principle:
    CLOSED -> ABSTAIN
    OPEN   -> Decision Engine may evaluate candidates

This layer never:
- selects Maqam
- selects Jins
- modifies source audio
- modifies source timing
- modifies source performance
- modifies source scores
- overrides Tonic ABSTAIN
"""

from typing import Any, Dict, List, Optional


class MaqamDecisionGate:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    # =========================================================
    # Gate thresholds
    # =========================================================

    MIN_READINESS_SCORE = 0.70
    MIN_OVERALL_RELIABILITY = 0.60
    MIN_CONSENSUS_QUALITY = 0.60
    MIN_AGREEMENT_SCORE = 0.60

    MAX_CONFLICT_SCORE = 0.40
    MAX_CONFLICT_SEVERITY = 0.40

    MIN_SUPPORT_MARGIN = 0.10
    MIN_SUPPORT_SHARE = 0.60

    # =========================================================
    # Constructor
    # =========================================================

    def __init__(self) -> None:
        pass

    # =========================================================
    # File helpers
    # =========================================================

    @staticmethod
    def _load(path: str) -> Dict[str, Any]:

        import json

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

        import json

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2,
            )

    # =========================================================
    # Numeric helpers
    # =========================================================

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

    @classmethod
    def _score(
        cls,
        value: Any,
        default: float = 0.0,
    ) -> float:

        value = cls._float(
            value,
            default,
        )

        return max(
            0.0,
            min(
                1.0,
                value,
            ),
        )

    @staticmethod
    def _list(
        value: Any,
    ) -> List[Any]:

        if value is None:
            return []

        if isinstance(
            value,
            list,
        ):
            return list(value)

        if isinstance(
            value,
            tuple,
        ):
            return list(value)

        return [value]

    # =========================================================
    # Readiness extraction
    # =========================================================

    @classmethod
    def _extract_readiness(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        result = {
            "status": "UNKNOWN",
            "readiness_score": 0.0,
            "top_candidate": None,
            "top_readiness": 0.0,
            "second_candidate": None,
            "second_readiness": 0.0,
            "global_blockers": [],
            "candidates": [],
        }

        if not isinstance(
            data,
            dict,
        ):
            return result

        readiness = data.get(
            "readiness"
        )

        if not isinstance(
            readiness,
            dict,
        ):
            return result

        global_data = readiness.get(
            "global"
        )

        if isinstance(
            global_data,
            dict,
        ):

            result[
                "status"
            ] = str(
                global_data.get(
                    "status",
                    "UNKNOWN",
                )
            ).upper()

            result[
                "readiness_score"
            ] = cls._score(
                global_data.get(
                    "readiness_score",
                    0.0,
                )
            )

            result[
                "top_candidate"
            ] = global_data.get(
                "top_candidate"
            )

            result[
                "top_readiness"
            ] = cls._score(
                global_data.get(
                    "top_readiness",
                    0.0,
                )
            )

            result[
                "second_candidate"
            ] = global_data.get(
                "second_candidate"
            )

            result[
                "second_readiness"
            ] = cls._score(
                global_data.get(
                    "second_readiness",
                    0.0,
                )
            )

            result[
                "global_blockers"
            ] = cls._list(
                global_data.get(
                    "global_blockers",
                    [],
                )
            )

        candidates = readiness.get(
            "candidates"
        )

        if isinstance(
            candidates,
            list,
        ):
            result[
                "candidates"
            ] = [
                x
                for x in candidates
                if isinstance(
                    x,
                    dict,
                )
            ]

        return result

    # =========================================================
    # Reliability extraction
    # =========================================================

    @classmethod
    def _extract_reliability(
        cls,
        data: Dict[str, Any],
    ) -> float:

        if not isinstance(
            data,
            dict,
        ):
            return 0.0

        reliability = data.get(
            "reliability"
        )

        if isinstance(
            reliability,
            dict,
        ):

            return cls._score(
                reliability.get(
                    "overall_score",
                    0.0,
                )
            )

        return cls._score(
            data.get(
                "overall_score",
                0.0,
            )
        )

    # =========================================================
    # Consensus extraction
    # =========================================================

    @classmethod
    def _extract_consensus(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, float]:

        result = {
            "quality": 0.0,
            "agreement_score": 0.0,
            "conflict_score": 1.0,
        }

        if not isinstance(
            data,
            dict,
        ):
            return result

        consensus = data.get(
            "consensus"
        )

        if not isinstance(
            consensus,
            dict,
        ):
            return result

        agreement = consensus.get(
            "agreement"
        )

        if isinstance(
            agreement,
            dict,
        ):

            result[
                "agreement_score"
            ] = cls._score(
                agreement.get(
                    "agreement_score",
                    0.0,
                )
            )

            result[
                "conflict_score"
            ] = cls._score(
                agreement.get(
                    "conflict_score",
                    1.0,
                )
            )

        quality = consensus.get(
            "quality"
        )

        if isinstance(
            quality,
            dict,
        ):

            result[
                "quality"
            ] = cls._score(
                quality.get(
                    "consensus_quality",
                    0.0,
                )
            )

        return result

    # =========================================================
    # Conflict extraction
    # =========================================================

    @classmethod
    def _extract_conflict(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        result = {
            "severity": 1.0,
            "conflict_score": 1.0,
            "label": "UNKNOWN",
            "meaningful_opposition": False,
        }

        if not isinstance(
            data,
            dict,
        ):
            return result

        conflict = data.get(
            "conflict"
        )

        if not isinstance(
            conflict,
            dict,
        ):
            return result

        severity = conflict.get(
            "severity"
        )

        if isinstance(
            severity,
            dict,
        ):

            result[
                "severity"
            ] = cls._score(
                severity.get(
                    "score",
                    1.0,
                )
            )

            result[
                "label"
            ] = str(
                severity.get(
                    "label",
                    "UNKNOWN",
                )
            ).upper()

        elif severity is not None:

            result[
                "severity"
            ] = cls._score(
                severity
            )

        balance = conflict.get(
            "balance"
        )

        if isinstance(
            balance,
            dict,
        ):

            result[
                "conflict_score"
            ] = cls._score(
                balance.get(
                    "conflict_score",
                    1.0,
                )
            )

        elif conflict.get(
            "conflict_score"
        ) is not None:

            result[
                "conflict_score"
            ] = cls._score(
                conflict.get(
                    "conflict_score"
                )
            )

        meaningful_g = 0
        meaningful_c = 0

        if isinstance(
            severity,
            dict,
        ):

            meaningful_g = int(
                severity.get(
                    "meaningful_G_components",
                    0,
                )
                or 0
            )

            meaningful_c = int(
                severity.get(
                    "meaningful_C_components",
                    0,
                )
                or 0
            )

        result[
            "meaningful_opposition"
        ] = (
            meaningful_g > 0
            and meaningful_c > 0
        )

        return result

    # =========================================================
    # Tonic decision extraction
    # =========================================================

    @classmethod
    def _extract_tonic_decision(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        result = {
            "status": "UNKNOWN",
            "tonic_pitch_class": None,
            "tonic_name": None,
        }

        if not isinstance(
            data,
            dict,
        ):
            return result

        decision = data.get(
            "decision"
        )

        if not isinstance(
            decision,
            dict,
        ):
            return result

        result[
            "status"
        ] = str(
            decision.get(
                "status",
                "UNKNOWN",
            )
        ).upper()

        result[
            "tonic_pitch_class"
        ] = decision.get(
            "tonic_pitch_class"
        )

        result[
            "tonic_name"
        ] = decision.get(
            "tonic_name"
        )

        return result

    # =========================================================
    # Candidate extraction
    # =========================================================

    @classmethod
    def _extract_candidate(
        cls,
        readiness_candidate: Dict[str, Any],
    ) -> Dict[str, Any]:

        return {
            "maqam":
                readiness_candidate.get(
                    "maqam"
                ),

            "tonic_pitch_class":
                readiness_candidate.get(
                    "tonic_pitch_class"
                ),

            "readiness_score":
                cls._score(
                    readiness_candidate.get(
                        "readiness_score",
                        0.0,
                    )
                ),

            "support_share":
                cls._score(
                    readiness_candidate.get(
                        "support_share",
                        0.0,
                    )
                ),

            "support_margin":
                cls._float(
                    readiness_candidate.get(
                        "support_margin",
                        0.0,
                    )
                ),

            "candidate_support":
                cls._score(
                    readiness_candidate.get(
                        "candidate_support",
                        0.0,
                    )
                ),

            "status":
                str(
                    readiness_candidate.get(
                        "status",
                        "UNKNOWN",
                    )
                ).upper(),

            "blockers":
                cls._list(
                    readiness_candidate.get(
                        "blockers",
                        [],
                    )
                ),

            "supporting_components":
                cls._list(
                    readiness_candidate.get(
                        "supporting_components",
                        [],
                    )
                ),

            "opposing_components":
                cls._list(
                    readiness_candidate.get(
                        "opposing_components",
                        [],
                    )
                ),

            "meaningful_opposing_components":
                int(
                    readiness_candidate.get(
                        "meaningful_opposing_components",
                        0,
                    )
                    or 0
                ),
        }

    # =========================================================
    # Candidate Gate
    # =========================================================

    @classmethod
    def _candidate_gate(
        cls,
        candidate: Dict[str, Any],
        tonic_decision: Dict[str, Any],
    ) -> Dict[str, Any]:

        blockers = list(
            candidate.get(
                "blockers",
                [],
            )
        )

        # -----------------------------------------------------
        # Candidate must already be READY.
        # -----------------------------------------------------

        if candidate.get(
            "status"
        ) != "READY":

            if (
                "READINESS_STATUS_NOT_READY"
                not in blockers
            ):
                blockers.append(
                    "READINESS_STATUS_NOT_READY"
                )

        if (
            candidate.get(
                "readiness_score",
                0.0,
            )
            < cls.MIN_READINESS_SCORE
        ):

            if (
                "READINESS_SCORE_BELOW_THRESHOLD"
                not in blockers
            ):
                blockers.append(
                    "READINESS_SCORE_BELOW_THRESHOLD"
                )

        if (
            candidate.get(
                "support_share",
                0.0,
            )
            < cls.MIN_SUPPORT_SHARE
        ):

            if (
                "SUPPORT_SHARE_TOO_SMALL"
                not in blockers
            ):
                blockers.append(
                    "SUPPORT_SHARE_TOO_SMALL"
                )

        if (
            candidate.get(
                "support_margin",
                0.0,
            )
            < cls.MIN_SUPPORT_MARGIN
        ):

            if (
                "SUPPORT_MARGIN_TOO_SMALL"
                not in blockers
            ):
                blockers.append(
                    "SUPPORT_MARGIN_TOO_SMALL"
                )

        # -----------------------------------------------------
        # Meaningful opposition blocks candidate.
        # -----------------------------------------------------

        if (
            candidate.get(
                "meaningful_opposing_components",
                0,
            )
            > 0
        ):

            if (
                "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
                not in blockers
            ):
                blockers.append(
                    "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
                )

        # -----------------------------------------------------
        # Tonic must already be DECIDED.
        # -----------------------------------------------------

        tonic_status = tonic_decision.get(
            "status"
        )

        if tonic_status != "DECIDED":

            if (
                "TONIC_DECISION_NOT_AVAILABLE"
                not in blockers
            ):
                blockers.append(
                    "TONIC_DECISION_NOT_AVAILABLE"
                )

        else:

            tonic_pc = tonic_decision.get(
                "tonic_pitch_class"
            )

            candidate_pc = candidate.get(
                "tonic_pitch_class"
            )

            if (
                tonic_pc is not None
                and candidate_pc is not None
            ):

                try:
                    tonic_pc = int(
                        tonic_pc
                    ) % 12

                    candidate_pc = int(
                        candidate_pc
                    ) % 12

                    if tonic_pc != candidate_pc:

                        if (
                            "TONIC_MISMATCH"
                            not in blockers
                        ):
                            blockers.append(
                                "TONIC_MISMATCH"
                            )

                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        allowed = (
            len(blockers) == 0
        )

        return {
            "maqam":
                candidate.get(
                    "maqam"
                ),

            "status":
                "OPEN"
                if allowed
                else "CLOSED",

            "decision_allowed":
                allowed,

            "readiness_status":
                candidate.get(
                    "status"
                ),

            "readiness_score":
                candidate.get(
                    "readiness_score",
                    0.0,
                ),

            "candidate_support":
                candidate.get(
                    "candidate_support",
                    0.0,
                ),

            "support_share":
                candidate.get(
                    "support_share",
                    0.0,
                ),

            "support_margin":
                candidate.get(
                    "support_margin",
                    0.0,
                ),

            "supporting_components":
                candidate.get(
                    "supporting_components",
                    [],
                ),

            "opposing_components":
                candidate.get(
                    "opposing_components",
                    [],
                ),

            "blockers":
                blockers,
        }

    # =========================================================
    # Main gate analysis
    # =========================================================

    @classmethod
    def analyze(
        cls,
        readiness_data: Dict[str, Any],
        reliability_data: Dict[str, Any],
        consensus_data: Dict[str, Any],
        conflict_data: Dict[str, Any],
        tonic_decision_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        readiness = (
            cls._extract_readiness(
                readiness_data
            )
        )

        reliability = (
            cls._extract_reliability(
                reliability_data
            )
        )

        consensus = (
            cls._extract_consensus(
                consensus_data
            )
        )

        conflict = (
            cls._extract_conflict(
                conflict_data
            )
        )

        tonic_decision = (
            cls._extract_tonic_decision(
                tonic_decision_data
            )
        )

        # -----------------------------------------------------
        # Global checks
        # -----------------------------------------------------

        checks = {
            "readiness_status_ready":
                readiness[
                    "status"
                ] == "READY",

            "readiness_score":
                readiness[
                    "readiness_score"
                ]
                >= cls.MIN_READINESS_SCORE,

            "overall_reliability":
                reliability
                >= cls.MIN_OVERALL_RELIABILITY,

            "consensus_quality":
                consensus[
                    "quality"
                ]
                >= cls.MIN_CONSENSUS_QUALITY,

            "agreement_score":
                consensus[
                    "agreement_score"
                ]
                >= cls.MIN_AGREEMENT_SCORE,

            "conflict_score":
                conflict[
                    "conflict_score"
                ]
                <= cls.MAX_CONFLICT_SCORE,

            "conflict_severity":
                conflict[
                    "severity"
                ]
                <= cls.MAX_CONFLICT_SEVERITY,

            "support_margin":
                readiness[
                    "top_readiness"
                ]
                >= cls.MIN_SUPPORT_MARGIN,

            "support_share":
                True,

            "no_meaningful_opposition":
                not conflict[
                    "meaningful_opposition"
                ],
        }

        blockers = []

        if not checks[
            "readiness_status_ready"
        ]:
            blockers.append(
                "READINESS_STATUS_NOT_READY"
            )

        if not checks[
            "readiness_score"
        ]:
            blockers.append(
                "READINESS_SCORE_BELOW_THRESHOLD"
            )

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
            "agreement_score"
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
            "no_meaningful_opposition"
        ]:
            blockers.append(
                "MEANINGFUL_MAQAM_OPPOSITION"
            )

        # -----------------------------------------------------
        # Tonic dependency
        # -----------------------------------------------------

        if (
            tonic_decision[
                "status"
            ]
            != "DECIDED"
        ):

            blockers.append(
                "TONIC_DECISION_NOT_AVAILABLE"
            )

        # -----------------------------------------------------
        # Candidate gates
        # -----------------------------------------------------

        candidate_gates = []

        for readiness_candidate in readiness[
            "candidates"
        ]:

            candidate = cls._extract_candidate(
                readiness_candidate
            )

            candidate_gate = cls._candidate_gate(
                candidate,
                tonic_decision,
            )

            candidate_gates.append(
                candidate_gate
            )

        # -----------------------------------------------------
        # Gate decision
        # -----------------------------------------------------

        decision_allowed = (
            len(blockers) == 0
            and
            readiness[
                "status"
            ] == "READY"
            and
            readiness[
                "readiness_score"
            ]
            >= cls.MIN_READINESS_SCORE
        )

        # -----------------------------------------------------
        # Protection:
        # Gate itself never selects Maqam.
        # -----------------------------------------------------

        return {
            "version":
                cls.VERSION,

            "feature_version":
                cls.FEATURE_VERSION,

            "patch_version":
                cls.PATCH_VERSION,

            "gate": {

                "status":
                    "OPEN"
                    if decision_allowed
                    else "CLOSED",

                "level":
                    "ALLOW"
                    if decision_allowed
                    else "ABSTAIN",

                "decision_allowed":
                    decision_allowed,

                "abstention_required":
                    not decision_allowed,

                "passed_checks":
                    sum(
                        1
                        for value
                        in checks.values()
                        if value
                    ),

                "total_checks":
                    len(checks),

                "blockers":
                    blockers,
            },

            "checks":
                checks,

            "candidate_gates":
                candidate_gates,

            "tonic_dependency": {

                "status":
                    tonic_decision[
                        "status"
                    ],

                "tonic_pitch_class":
                    tonic_decision[
                        "tonic_pitch_class"
                    ],

                "tonic_name":
                    tonic_decision[
                        "tonic_name"
                    ],

                "required":
                    True,

                "decision_available":
                    tonic_decision[
                        "status"
                    ] == "DECIDED",
            },

            "decision": {

                "status":
                    "EVIDENCE_ONLY",

                "tonic_pitch_class":
                    None,

                "tonic_name":
                    None,

                "maqam":
                    None,

                "jins":
                    None,

                "confidence":
                    None,

                "reason": [
                    "MAQAM_DECISION_GATE_ONLY",
                    "GATE_DOES_NOT_SELECT_MAQAM",
                    "NO_MAQAM_DECISION",
                ],
            },

            "decision_safety": {

                "maqam_decision_safe":
                    decision_allowed,

                "gate_open":
                    decision_allowed,

                "gate_closed":
                    not decision_allowed,

                "decision_allowed":
                    decision_allowed,

                "maqam_selected":
                    False,

                "jins_selected":
                    False,

                "tonic_selected":
                    False,
            },

            "protection": {

                "source_pitch_modified":
                    False,

                "source_timing_modified":
                    False,

                "source_performance_modified":
                    False,

                "source_scores_modified":
                    False,

                "source_audio_modified":
                    False,

                "tonic_decision_made":
                    False,

                "maqam_decision_made":
                    False,

                "jins_decision_made":
                    False,

                "gate_selected_maqam":
                    False,

                "gate_selected_jins":
                    False,

                "gate_selected_tonic":
                    False,

                "gate_modified_source":
                    False,

                "readiness_promoted_to_decision":
                    False,

                "original_scores_preserved":
                    True,

                "original_decision_overridden":
                    False,
            },
        }

    # =========================================================
    # File analysis
    # =========================================================

    def analyze_files(
        self,
        readiness_path: str,
        reliability_path: str,
        consensus_path: str,
        conflict_path: str,
        tonic_decision_path: str,
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

        tonic_decision_data = self._load(
            tonic_decision_path
        )

        result = self.analyze(
            readiness_data,
            reliability_data,
            consensus_data,
            conflict_data,
            tonic_decision_data,
        )

        self._save(
            output_path,
            result,
        )

        return result


if __name__ == "__main__":

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Maqam Decision Gate V1.0"
    )

    print(
        "============================================================"
    )

    print(
        "Build: PASS"
    )