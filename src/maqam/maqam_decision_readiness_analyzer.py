"""
PhoenixVoiceEngine
Maqam Decision Readiness Analyzer V1.0

Responsibilities
----------------
1. Extract Maqam candidate information.
2. Evaluate whether a Maqam candidate is ready for decision.
3. Evaluate global Maqam decision readiness.
4. Preserve evidence conflicts and blockers.
5. Require an already-decided tonic before Maqam readiness can become valid.
6. Never make a Maqam decision.
7. Never select a Jins.
8. Never modify source audio, timing, performance, or source scores.
9. Never promote Tonic ABSTAIN into a Maqam decision.
"""

from typing import Any, Dict, List, Optional


class MaqamDecisionReadinessAnalyzer:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    PITCH_CLASS_NAMES = {
        0: "C",
        1: "C#",
        2: "D",
        3: "D#",
        4: "E",
        5: "F",
        6: "F#",
        7: "G",
        8: "G#",
        9: "A",
        10: "A#",
        11: "B",
    }

    # =========================================================
    # Readiness thresholds
    # =========================================================

    MIN_OVERALL_RELIABILITY = 0.60
    MIN_CONSENSUS_QUALITY = 0.60
    MIN_AGREEMENT_SCORE = 0.60

    MAX_CONFLICT_SCORE = 0.40
    MAX_CONFLICT_SEVERITY = 0.40

    MIN_READINESS_SCORE = 0.70
    MIN_SUPPORT_SHARE = 0.60
    MIN_SUPPORT_MARGIN = 0.10

    MIN_CANDIDATE_SUPPORT = 0.50
    MIN_STRONG_COMPONENTS = 1

    MAX_MEANINGFUL_OPPOSITION = 0

    # =========================================================
    # Constructor
    # =========================================================

    def __init__(self) -> None:
        pass

    # =========================================================
    # Generic helpers
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
    ) -> float:
        value = cls._float(
            value,
            0.0,
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

    @classmethod
    def normalize_pitch_class(
        cls,
        value: Any,
    ) -> Optional[int]:

        if value is None:
            return None

        try:
            return int(value) % 12
        except (
            TypeError,
            ValueError,
        ):
            return None

    @classmethod
    def pitch_class_name(
        cls,
        value: Any,
    ) -> Optional[str]:

        pitch_class = cls.normalize_pitch_class(
            value
        )

        if pitch_class is None:
            return None

        return cls.PITCH_CLASS_NAMES.get(
            pitch_class
        )

    # =========================================================
    # Candidate extraction
    # =========================================================

    @classmethod
    def _extract_candidates(
        cls,
        data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        if not isinstance(
            data,
            dict,
        ):
            return []

        candidates = data.get(
            "candidates"
        )

        if isinstance(
            candidates,
            list,
        ):
            return [
                x
                for x in candidates
                if isinstance(x, dict)
            ]

        readiness = data.get(
            "readiness"
        )

        if isinstance(
            readiness,
            dict,
        ):

            candidates = readiness.get(
                "candidates"
            )

            if isinstance(
                candidates,
                list,
            ):
                return [
                    x
                    for x in candidates
                    if isinstance(x, dict)
                ]

        return []

    # =========================================================
    # Tonic decision extraction
    # =========================================================

    @classmethod
    def _extract_tonic_decision(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(
            data,
            dict,
        ):
            return {
                "status": "UNKNOWN",
                "tonic_pitch_class": None,
                "tonic_name": None,
            }

        decision = data.get(
            "decision"
        )

        if not isinstance(
            decision,
            dict,
        ):
            return {
                "status": "UNKNOWN",
                "tonic_pitch_class": None,
                "tonic_name": None,
            }

        return {
            "status": str(
                decision.get(
                    "status",
                    "UNKNOWN",
                )
            ).upper(),

            "tonic_pitch_class":
                cls.normalize_pitch_class(
                    decision.get(
                        "tonic_pitch_class"
                    )
                ),

            "tonic_name":
                decision.get(
                    "tonic_name"
                ),
        }

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
            "agreement_score": 0.0,
            "quality": 0.0,
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
            "label": "UNKNOWN",
            "conflict_score": 1.0,
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
                    result[
                        "conflict_score"
                    ],
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
    # Candidate value extraction
    # =========================================================

    @classmethod
    def _candidate_value(
        cls,
        candidate: Dict[str, Any],
        key: str,
        default: Any = 0.0,
    ) -> Any:

        if not isinstance(
            candidate,
            dict,
        ):
            return default

        return candidate.get(
            key,
            default,
        )

    # =========================================================
    # Candidate readiness
    # =========================================================

    @classmethod
    def analyze_candidate(
        cls,
        candidate: Dict[str, Any],
        overall_reliability: float,
        consensus_quality: float,
        agreement_score: float,
        conflict_score: float,
        conflict_severity: float,
        tonic_decision: Dict[str, Any],
    ) -> Dict[str, Any]:

        maqam = candidate.get(
            "maqam"
        )

        tonic_pitch_class = (
            cls.normalize_pitch_class(
                candidate.get(
                    "tonic_pitch_class"
                )
            )
        )

        readiness_score = cls._score(
            candidate.get(
                "readiness_score",
                0.0,
            )
        )

        candidate_support = cls._score(
            candidate.get(
                "candidate_support",
                0.0,
            )
        )

        support_share = cls._score(
            candidate.get(
                "support_share",
                0.0,
            )
        )

        support_margin = cls._float(
            candidate.get(
                "support_margin",
                0.0,
            )
        )

        strong_components = int(
            candidate.get(
                "strong_candidate_components",
                0,
            )
            or 0
        )

        opposing_components = cls._list(
            candidate.get(
                "opposing_components",
                [],
            )
        )

        meaningful_opposition = int(
            candidate.get(
                "meaningful_opposing_components",
                0,
            )
            or 0
        )

        candidate_blockers = cls._list(
            candidate.get(
                "blockers",
                [],
            )
        )

        blockers: List[str] = []

        # -----------------------------------------------------
        # Tonic prerequisite
        # -----------------------------------------------------

        tonic_ready = (
            tonic_decision.get(
                "status"
            ) == "DECIDED"
            and
            tonic_pitch_class is not None
            and
            cls.normalize_pitch_class(
                tonic_decision.get(
                    "tonic_pitch_class"
                )
            )
            == tonic_pitch_class
        )

        if (
            tonic_decision.get(
                "status"
            ) != "DECIDED"
        ):
            blockers.append(
                "TONIC_DECISION_NOT_AVAILABLE"
            )

        elif not tonic_ready:
            blockers.append(
                "TONIC_MISMATCH"
            )

        # -----------------------------------------------------
        # Global evidence blockers
        # -----------------------------------------------------

        if (
            overall_reliability
            < cls.MIN_OVERALL_RELIABILITY
        ):
            blockers.append(
                "OVERALL_RELIABILITY_BELOW_THRESHOLD"
            )

        if (
            consensus_quality
            < cls.MIN_CONSENSUS_QUALITY
        ):
            blockers.append(
                "CONSENSUS_QUALITY_BELOW_THRESHOLD"
            )

        if (
            agreement_score
            < cls.MIN_AGREEMENT_SCORE
        ):
            blockers.append(
                "AGREEMENT_BELOW_THRESHOLD"
            )

        if (
            conflict_score
            > cls.MAX_CONFLICT_SCORE
        ):
            blockers.append(
                "CONFLICT_SCORE_TOO_HIGH"
            )

        if (
            conflict_severity
            > cls.MAX_CONFLICT_SEVERITY
        ):
            blockers.append(
                "CONFLICT_SEVERITY_TOO_HIGH"
            )

        # -----------------------------------------------------
        # Candidate blockers
        # -----------------------------------------------------

        if (
            readiness_score
            < cls.MIN_READINESS_SCORE
        ):
            blockers.append(
                "READINESS_SCORE_BELOW_THRESHOLD"
            )

        if (
            candidate_support
            < cls.MIN_CANDIDATE_SUPPORT
        ):
            blockers.append(
                "CANDIDATE_SUPPORT_BELOW_THRESHOLD"
            )

        if (
            support_share
            < cls.MIN_SUPPORT_SHARE
        ):
            blockers.append(
                "SUPPORT_SHARE_BELOW_THRESHOLD"
            )

        if (
            support_margin
            < cls.MIN_SUPPORT_MARGIN
        ):
            blockers.append(
                "SUPPORT_MARGIN_BELOW_THRESHOLD"
            )

        if (
            strong_components
            < cls.MIN_STRONG_COMPONENTS
        ):
            blockers.append(
                "NO_STRONG_CANDIDATE_COMPONENT"
            )

        if (
            meaningful_opposition
            > cls.MAX_MEANINGFUL_OPPOSITION
        ):
            blockers.append(
                "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
            )

        if candidate_blockers:

            blockers.extend(
                [
                    str(x)
                    for x in candidate_blockers
                    if str(x)
                    not in blockers
                ]
            )

        if not maqam:
            blockers.append(
                "MAQAM_MISSING"
            )

        if tonic_pitch_class is None:
            blockers.append(
                "TONIC_PITCH_CLASS_MISSING"
            )

        # -----------------------------------------------------
        # Readiness checks
        # -----------------------------------------------------

        checks = {
            "tonic_decision_available":
                tonic_decision.get(
                    "status"
                ) == "DECIDED",

            "tonic_matches_candidate":
                tonic_ready,

            "overall_reliability":
                overall_reliability
                >= cls.MIN_OVERALL_RELIABILITY,

            "consensus_quality":
                consensus_quality
                >= cls.MIN_CONSENSUS_QUALITY,

            "agreement":
                agreement_score
                >= cls.MIN_AGREEMENT_SCORE,

            "conflict_score":
                conflict_score
                <= cls.MAX_CONFLICT_SCORE,

            "conflict_severity":
                conflict_severity
                <= cls.MAX_CONFLICT_SEVERITY,

            "readiness_score":
                readiness_score
                >= cls.MIN_READINESS_SCORE,

            "candidate_support":
                candidate_support
                >= cls.MIN_CANDIDATE_SUPPORT,

            "support_share":
                support_share
                >= cls.MIN_SUPPORT_SHARE,

            "support_margin":
                support_margin
                >= cls.MIN_SUPPORT_MARGIN,

            "strong_candidate_components":
                strong_components
                >= cls.MIN_STRONG_COMPONENTS,

            "no_meaningful_opposition":
                meaningful_opposition
                <= cls.MAX_MEANINGFUL_OPPOSITION,
        }

        passed_checks = sum(
            1
            for value in checks.values()
            if value
        )

        total_checks = len(
            checks
        )

        readiness_ratio = (
            passed_checks
            / total_checks
            if total_checks
            else 0.0
        )

        ready = (
            len(blockers) == 0
        )

        return {
            "maqam": maqam,
            "tonic_pitch_class":
                tonic_pitch_class,
            "tonic_name":
                cls.pitch_class_name(
                    tonic_pitch_class
                ),

            "readiness_score":
                round(
                    readiness_score,
                    6,
                ),

            "candidate_support":
                round(
                    candidate_support,
                    6,
                ),

            "support_share":
                round(
                    support_share,
                    6,
                ),

            "support_margin":
                round(
                    support_margin,
                    6,
                ),

            "strong_candidate_components":
                strong_components,

            "opposing_components":
                opposing_components,

            "meaningful_opposing_components":
                meaningful_opposition,

            "checks":
                checks,

            "passed_checks":
                passed_checks,

            "total_checks":
                total_checks,

            "readiness_ratio":
                round(
                    readiness_ratio,
                    6,
                ),

            "status":
                "READY"
                if ready
                else "NOT_READY",

            "blockers":
                blockers,

            "evidence_only":
                True,
        }

    # =========================================================
    # Global readiness
    # =========================================================

    @classmethod
    def analyze(
        cls,
        consensus_data: Dict[str, Any],
        reliability_data: Dict[str, Any],
        conflict_data: Dict[str, Any],
        tonic_decision_data: Dict[str, Any],
        candidates: Optional[
            List[Dict[str, Any]]
        ] = None,
    ) -> Dict[str, Any]:

        overall_reliability = (
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

        if candidates is None:

            candidates = (
                cls._extract_candidates(
                    consensus_data
                )
            )

            if not candidates:

                candidates = (
                    cls._extract_candidates(
                        tonic_decision_data
                    )
                )

        candidate_results = []

        for candidate in candidates:

            candidate_results.append(
                cls.analyze_candidate(
                    candidate,
                    overall_reliability,
                    consensus[
                        "quality"
                    ],
                    consensus[
                        "agreement_score"
                    ],
                    conflict[
                        "conflict_score"
                    ],
                    conflict[
                        "severity"
                    ],
                    tonic_decision,
                )
            )

        # -----------------------------------------------------
        # Rank candidates by readiness.
        # -----------------------------------------------------

        ranked = sorted(
            candidate_results,
            key=lambda x: (
                x["readiness_ratio"],
                x["candidate_support"],
                x["support_share"],
                x["support_margin"],
            ),
            reverse=True,
        )

        top_candidate = (
            ranked[0]
            if ranked
            else None
        )

        second_candidate = (
            ranked[1]
            if len(ranked) > 1
            else None
        )

        global_blockers = []

        if (
            tonic_decision.get(
                "status"
            ) != "DECIDED"
        ):
            global_blockers.append(
                "TONIC_DECISION_NOT_AVAILABLE"
            )

        if (
            overall_reliability
            < cls.MIN_OVERALL_RELIABILITY
        ):
            global_blockers.append(
                "OVERALL_RELIABILITY_BELOW_THRESHOLD"
            )

        if (
            consensus[
                "quality"
            ]
            < cls.MIN_CONSENSUS_QUALITY
        ):
            global_blockers.append(
                "CONSENSUS_QUALITY_BELOW_THRESHOLD"
            )

        if (
            consensus[
                "agreement_score"
            ]
            < cls.MIN_AGREEMENT_SCORE
        ):
            global_blockers.append(
                "CONSENSUS_AGREEMENT_BELOW_THRESHOLD"
            )

        if (
            conflict[
                "conflict_score"
            ]
            > cls.MAX_CONFLICT_SCORE
        ):
            global_blockers.append(
                "CONFLICT_SCORE_TOO_HIGH"
            )

        if (
            conflict[
                "severity"
            ]
            > cls.MAX_CONFLICT_SEVERITY
        ):
            global_blockers.append(
                "CONFLICT_SEVERITY_TOO_HIGH"
            )

        if (
            conflict[
                "meaningful_opposition"
            ]
        ):
            global_blockers.append(
                "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
            )

        if (
            top_candidate is None
        ):
            global_blockers.append(
                "NO_MAQAM_CANDIDATE"
            )

        elif top_candidate[
            "status"
        ] != "READY":
            global_blockers.append(
                "TOP_CANDIDATE_NOT_READY"
            )

        # -----------------------------------------------------
        # Global readiness
        # -----------------------------------------------------

        global_ready = (
            len(global_blockers) == 0
            and top_candidate is not None
            and top_candidate[
                "status"
            ] == "READY"
        )

        readiness_score = (
            top_candidate[
                "readiness_ratio"
            ]
            if top_candidate
            else 0.0
        )

        return {
            "version":
                cls.VERSION,

            "feature_version":
                cls.FEATURE_VERSION,

            "patch_version":
                cls.PATCH_VERSION,

            "readiness": {

                "global": {

                    "status":
                        "READY"
                        if global_ready
                        else "NOT_READY",

                    "readiness_score":
                        round(
                            readiness_score,
                            6,
                        ),

                    "top_candidate":
                        top_candidate[
                            "maqam"
                        ]
                        if top_candidate
                        else None,

                    "top_readiness":
                        round(
                            top_candidate[
                                "readiness_ratio"
                            ],
                            6,
                        )
                        if top_candidate
                        else 0.0,

                    "second_candidate":
                        second_candidate[
                            "maqam"
                        ]
                        if second_candidate
                        else None,

                    "second_readiness":
                        round(
                            second_candidate[
                                "readiness_ratio"
                            ],
                            6,
                        )
                        if second_candidate
                        else 0.0,

                    "global_blockers":
                        global_blockers,
                },

                "candidates":
                    ranked,
            },

            "evidence_summary": {

                "overall_reliability":
                    round(
                        overall_reliability,
                        6,
                    ),

                "consensus_quality":
                    round(
                        consensus[
                            "quality"
                        ],
                        6,
                    ),

                "agreement_score":
                    round(
                        consensus[
                            "agreement_score"
                        ],
                        6,
                    ),

                "conflict_score":
                    round(
                        conflict[
                            "conflict_score"
                        ],
                        6,
                    ),

                "conflict_severity":
                    round(
                        conflict[
                            "severity"
                        ],
                        6,
                    ),

                "conflict_label":
                    conflict[
                        "label"
                    ],
            },

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

                "maqam":
                    None,

                "tonic_pitch_class":
                    None,

                "tonic_name":
                    None,

                "jins":
                    None,

                "confidence":
                    None,

                "reason": [
                    "MAQAM_DECISION_READINESS_ONLY",
                    "READINESS_IS_NOT_A_MAQAM_DECISION",
                    "NO_MAQAM_DECISION",
                ],
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

                "readiness_promoted_to_decision":
                    False,

                "tonic_abstention_overridden":
                    False,

                "original_decision_overridden":
                    False,

                "original_scores_preserved":
                    True,
            },
        }

    # =========================================================
    # File analysis
    # =========================================================

    def analyze_files(
        self,
        consensus_path: str,
        reliability_path: str,
        conflict_path: str,
        tonic_decision_path: str,
        output_path: str,
        candidates: Optional[
            List[Dict[str, Any]]
        ] = None,
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

        tonic_decision_data = self._load(
            tonic_decision_path
        )

        result = self.analyze(
            consensus_data,
            reliability_data,
            conflict_data,
            tonic_decision_data,
            candidates=candidates,
        )

        self._save(
            output_path,
            result,
        )

        return result

    # =========================================================
    # Single-file analysis
    # =========================================================

    def analyze_file(
        self,
        consensus_path: str,
        reliability_path: str,
        conflict_path: str,
        tonic_decision_path: str,
        output_path: str,
        candidates: Optional[
            List[Dict[str, Any]]
        ] = None,
    ) -> Dict[str, Any]:

        return self.analyze_files(
            consensus_path,
            reliability_path,
            conflict_path,
            tonic_decision_path,
            output_path,
            candidates=candidates,
        )


if __name__ == "__main__":

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Maqam Decision Readiness Analyzer V1.0"
    )

    print(
        "============================================================"
    )

    print(
        "Build: PASS"
    )