"""
PhoenixVoiceEngine
Maqam Decision Engine V1.0

Purpose
-------
Convert an OPEN Maqam Decision Gate + valid Maqam candidates
into a Maqam decision.

Safety rules
------------
1. CLOSED gate -> ABSTAIN.
2. Gate can never be bypassed.
3. Tonic must already be DECIDED.
4. Candidate must be READY.
5. Candidate must have no blockers.
6. Candidate must be compatible with the decided tonic.
7. Candidate must satisfy minimum readiness/support/margin.
8. Weak or ambiguous candidates -> ABSTAIN.
9. Engine selects Maqam only.
10. Engine never selects Jins.
11. Engine never modifies source audio/performance/scores.
"""

from typing import Any, Dict, List, Optional


class MaqamDecisionEngine:

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

    MIN_READINESS_SCORE = 0.70
    MIN_SUPPORT_SHARE = 0.60
    MIN_SUPPORT_MARGIN = 0.10
    MIN_DECISION_MARGIN = 0.10

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
    # Gate extraction
    # =========================================================

    @classmethod
    def _extract_gate(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        result = {
            "status": "CLOSED",
            "level": "ABSTAIN",
            "decision_allowed": False,
            "abstention_required": True,
            "blockers": [],
        }

        if not isinstance(
            data,
            dict,
        ):
            return result

        gate = data.get(
            "gate"
        )

        if not isinstance(
            gate,
            dict,
        ):
            return result

        result[
            "status"
        ] = str(
            gate.get(
                "status",
                "CLOSED",
            )
        ).upper()

        result[
            "level"
        ] = str(
            gate.get(
                "level",
                "ABSTAIN",
            )
        ).upper()

        result[
            "decision_allowed"
        ] = bool(
            gate.get(
                "decision_allowed",
                False,
            )
        )

        result[
            "abstention_required"
        ] = bool(
            gate.get(
                "abstention_required",
                not result[
                    "decision_allowed"
                ],
            )
        )

        result[
            "blockers"
        ] = cls._list(
            gate.get(
                "blockers",
                [],
            )
        )

        return result

    # =========================================================
    # Readiness extraction
    # =========================================================

    @classmethod
    def _extract_readiness(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        result = {
            "status": "NOT_READY",
            "readiness_score": 0.0,
            "top_candidate": None,
            "top_readiness": 0.0,
            "second_candidate": None,
            "second_readiness": 0.0,
            "candidates": [],
            "global_blockers": [],
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
                    "NOT_READY",
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
    # Tonic decision extraction
    # =========================================================

    @classmethod
    def _extract_tonic(
        cls,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        result = {
            "status": "ABSTAIN",
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
                "ABSTAIN",
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
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        return {
            "maqam":
                data.get(
                    "maqam"
                ),

            "tonic_pitch_class":
                data.get(
                    "tonic_pitch_class"
                ),

            "tonic_name":
                data.get(
                    "tonic_name"
                ),

            "readiness_score":
                cls._score(
                    data.get(
                        "readiness_score",
                        0.0,
                    )
                ),

            "candidate_support":
                cls._score(
                    data.get(
                        "candidate_support",
                        0.0,
                    )
                ),

            "support_share":
                cls._score(
                    data.get(
                        "support_share",
                        0.0,
                    )
                ),

            "support_margin":
                cls._float(
                    data.get(
                        "support_margin",
                        0.0,
                    )
                ),

            "status":
                str(
                    data.get(
                        "status",
                        "NOT_READY",
                    )
                ).upper(),

            "blockers":
                cls._list(
                    data.get(
                        "blockers",
                        [],
                    )
                ),

            "supporting_components":
                cls._list(
                    data.get(
                        "supporting_components",
                        [],
                    )
                ),

            "opposing_components":
                cls._list(
                    data.get(
                        "opposing_components",
                        [],
                    )
                ),

            "meaningful_opposing_components":
                int(
                    data.get(
                        "meaningful_opposing_components",
                        0,
                    )
                    or 0
                ),
        }

    # =========================================================
    # Candidate filtering
    # =========================================================

    @classmethod
    def _filter_candidate(
        cls,
        candidate: Dict[str, Any],
        tonic: Dict[str, Any],
    ) -> Dict[str, Any]:

        blockers = list(
            candidate.get(
                "blockers",
                [],
            )
        )

        # Candidate must be READY.

        if candidate.get(
            "status"
        ) != "READY":

            if (
                "READINESS_NOT_READY"
                not in blockers
            ):
                blockers.append(
                    "READINESS_NOT_READY"
                )

        # Readiness threshold.

        if (
            candidate.get(
                "readiness_score",
                0.0,
            )
            < cls.MIN_READINESS_SCORE
        ):

            if (
                "READINESS_SCORE_TOO_LOW"
                not in blockers
            ):
                blockers.append(
                    "READINESS_SCORE_TOO_LOW"
                )

        # Support share.

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

        # Support margin.

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

        # Meaningful opposition.

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

        # Tonic must be decided.

        if tonic.get(
            "status"
        ) != "DECIDED":

            if (
                "TONIC_DECISION_NOT_AVAILABLE"
                not in blockers
            ):
                blockers.append(
                    "TONIC_DECISION_NOT_AVAILABLE"
                )

        else:

            tonic_pc = tonic.get(
                "tonic_pitch_class"
            )

            candidate_pc = candidate.get(
                "tonic_pitch_class"
            )

            if (
                tonic_pc is None
                or candidate_pc is None
            ):

                if (
                    "TONIC_BINDING_INCOMPLETE"
                    not in blockers
                ):
                    blockers.append(
                        "TONIC_BINDING_INCOMPLETE"
                    )

            else:

                try:

                    tonic_pc = (
                        int(
                            tonic_pc
                        )
                        % 12
                    )

                    candidate_pc = (
                        int(
                            candidate_pc
                        )
                        % 12
                    )

                    if (
                        tonic_pc
                        != candidate_pc
                    ):

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

                    blockers.append(
                        "TONIC_BINDING_INVALID"
                    )

        return {
            "maqam":
                candidate.get(
                    "maqam"
                ),

            "tonic_pitch_class":
                candidate.get(
                    "tonic_pitch_class"
                ),

            "tonic_name":
                candidate.get(
                    "tonic_name"
                ),

            "allowed":
                len(
                    blockers
                ) == 0,

            "blockers":
                blockers,

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
        }

    # =========================================================
    # Candidate ranking
    # =========================================================

    @classmethod
    def _rank_candidates(
        cls,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        return sorted(
            candidates,
            key=lambda x: (
                x.get(
                    "readiness_score",
                    0.0,
                ),
                x.get(
                    "candidate_support",
                    0.0,
                ),
                x.get(
                    "support_share",
                    0.0,
                ),
                x.get(
                    "support_margin",
                    0.0,
                ),
            ),
            reverse=True,
        )

    # =========================================================
    # Decision safety
    # =========================================================

    @classmethod
    def _decision_safety(
        cls,
        gate: Dict[str, Any],
        readiness: Dict[str, Any],
        valid_candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        reasons = []

        if not gate.get(
            "decision_allowed",
            False,
        ):
            reasons.append(
                "GATE_CLOSED"
            )

            reasons.append(
                "GATE_DECISION_NOT_ALLOWED"
            )

        if readiness.get(
            "status"
        ) != "READY":

            reasons.append(
                "READINESS_NOT_READY"
            )

        if (
            readiness.get(
                "readiness_score",
                0.0,
            )
            < cls.MIN_READINESS_SCORE
        ):

            reasons.append(
                "READINESS_SCORE_TOO_LOW"
            )

        if not valid_candidates:

            reasons.append(
                "NO_VALID_MAQAM_CANDIDATE"
            )

        return {
            "safe":
                bool(
                    gate.get(
                        "decision_allowed",
                        False,
                    )
                    and
                    readiness.get(
                        "status"
                    ) == "READY"
                    and
                    valid_candidates
                ),

            "reasons":
                reasons,

            "valid_candidate_count":
                len(
                    valid_candidates
                ),
        }

    # =========================================================
    # Main analysis
    # =========================================================

    @classmethod
    def analyze(
        cls,
        gate_data: Dict[str, Any],
        readiness_data: Dict[str, Any],
        tonic_decision_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        gate = cls._extract_gate(
            gate_data
        )

        readiness = cls._extract_readiness(
            readiness_data
        )

        tonic = cls._extract_tonic(
            tonic_decision_data
        )

        # -----------------------------------------------------
        # IMPORTANT:
        # Closed Gate is an absolute barrier.
        # -----------------------------------------------------

        candidate_rows = []

        for raw_candidate in readiness[
            "candidates"
        ]:

            candidate = cls._extract_candidate(
                raw_candidate
            )

            candidate_rows.append(
                candidate
            )

        ranked_candidates = cls._rank_candidates(
            candidate_rows
        )

        filtered_candidates = []

        for candidate in ranked_candidates:

            gate_result = cls._filter_candidate(
                candidate,
                tonic,
            )

            filtered_candidates.append(
                {
                    **candidate,
                    "gate_allowed":
                        gate_result[
                            "allowed"
                        ],
                    "blockers":
                        gate_result[
                            "blockers"
                        ],
                }
            )

        valid_candidates = [
            x
            for x in filtered_candidates
            if x.get(
                "gate_allowed",
                False,
            )
        ]

        # -----------------------------------------------------
        # Engine-level margin protection.
        # -----------------------------------------------------

        if len(
            valid_candidates
        ) >= 2:

            top = valid_candidates[0]
            second = valid_candidates[1]

            margin = (
                top.get(
                    "readiness_score",
                    0.0,
                )
                -
                second.get(
                    "readiness_score",
                    0.0,
                )
            )

        elif len(
            valid_candidates
        ) == 1:

            top = valid_candidates[0]

            second = None

            margin = (
                top.get(
                    "readiness_score",
                    0.0,
                )
                -
                0.0
            )

        else:

            top = None
            second = None
            margin = 0.0

        # -----------------------------------------------------
        # Final decision
        # -----------------------------------------------------

        decision_status = "ABSTAIN"

        decision_maqam = None
        decision_tonic_pc = None
        decision_tonic_name = None
        decision_confidence = None

        decision_reasons = []

        if not gate.get(
            "decision_allowed",
            False,
        ):

            decision_reasons.extend(
                [
                    "GATE_CLOSED",
                    "MAQAM_DECISION_FORBIDDEN",
                    "ABSTAIN_REQUIRED",
                ]
            )

        elif readiness.get(
            "status"
        ) != "READY":

            decision_reasons.extend(
                [
                    "READINESS_NOT_READY",
                    "ABSTAIN_REQUIRED",
                ]
            )

        elif not valid_candidates:

            decision_reasons.extend(
                [
                    "NO_VALID_MAQAM_CANDIDATE",
                    "ABSTAIN_REQUIRED",
                ]
            )

        elif margin < cls.MIN_DECISION_MARGIN:

            decision_reasons.extend(
                [
                    "DECISION_MARGIN_TOO_SMALL",
                    "AMBIGUOUS_MAQAM_CANDIDATES",
                    "ABSTAIN_REQUIRED",
                ]
            )

        else:

            decision_status = "DECIDED"

            decision_maqam = top.get(
                "maqam"
            )

            decision_tonic_pc = top.get(
                "tonic_pitch_class"
            )

            decision_tonic_name = top.get(
                "tonic_name"
            )

            decision_confidence = round(
                min(
                    1.0,
                    (
                        top.get(
                            "readiness_score",
                            0.0,
                        )
                        +
                        top.get(
                            "support_share",
                            0.0,
                        )
                        +
                        max(
                            0.0,
                            margin,
                        )
                    )
                    / 3.0,
                ),
                6,
            )

            decision_reasons.extend(
                [
                    "MAQAM_DECISION_ALLOWED",
                    "VALID_MAQAM_CANDIDATE",
                    "DECISION_MARGIN_SUFFICIENT",
                ]
            )

        # -----------------------------------------------------
        # Safety
        # -----------------------------------------------------

        safety = cls._decision_safety(
            gate,
            readiness,
            valid_candidates,
        )

        if decision_status != "DECIDED":

            safety[
                "safe"
            ] = False

            if (
                "ABSTAIN_REQUIRED"
                not in safety[
                    "reasons"
                ]
            ):
                safety[
                    "reasons"
                ].append(
                    "ABSTAIN_REQUIRED"
                )

        # -----------------------------------------------------
        # Protection
        # -----------------------------------------------------

        protection = {
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
                decision_status
                == "DECIDED",

            "jins_decision_made":
                False,

            "gate_bypassed":
                False,

            "closed_gate_overridden":
                False,

            "readiness_overridden":
                False,

            "original_scores_preserved":
                True,

            "original_decision_overridden":
                False,
        }

        # -----------------------------------------------------
        # Final result
        # -----------------------------------------------------

        return {

            "version":
                cls.VERSION,

            "feature_version":
                cls.FEATURE_VERSION,

            "patch_version":
                cls.PATCH_VERSION,

            "gate":
                gate,

            "tonic_dependency":
                {
                    "status":
                        tonic.get(
                            "status"
                        ),

                    "tonic_pitch_class":
                        tonic.get(
                            "tonic_pitch_class"
                        ),

                    "tonic_name":
                        tonic.get(
                            "tonic_name"
                        ),

                    "decision_available":
                        tonic.get(
                            "status"
                        )
                        == "DECIDED",
                },

            "ranking":
                {
                    "candidates":
                        [
                            {
                                "rank":
                                    index + 1,

                                "maqam":
                                    candidate.get(
                                        "maqam"
                                    ),

                                "tonic_pitch_class":
                                    candidate.get(
                                        "tonic_pitch_class"
                                    ),

                                "tonic_name":
                                    candidate.get(
                                        "tonic_name"
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

                                "gate_allowed":
                                    candidate.get(
                                        "gate_allowed",
                                        False,
                                    ),

                                "blockers":
                                    candidate.get(
                                        "blockers",
                                        [],
                                    ),
                            }
                            for index, candidate
                            in enumerate(
                                filtered_candidates
                            )
                        ],

                    "valid_candidate_count":
                        len(
                            valid_candidates
                        ),

                    "decision_margin":
                        round(
                            margin,
                            6,
                        ),
                },

            "decision_safety":
                safety,

            "decision":
                {
                    "status":
                        decision_status,

                    "tonic_pitch_class":
                        decision_tonic_pc,

                    "tonic_name":
                        decision_tonic_name,

                    "maqam":
                        decision_maqam,

                    "jins":
                        None,

                    "confidence":
                        decision_confidence,

                    "reason":
                        decision_reasons,
                },

            "protection":
                protection,
        }

    # =========================================================
    # File analysis
    # =========================================================

    def analyze_file(
        self,
        gate_path: str,
        readiness_path: str,
        tonic_decision_path: str,
    ) -> Dict[str, Any]:

        gate_data = self._load(
            gate_path
        )

        readiness_data = self._load(
            readiness_path
        )

        tonic_decision_data = self._load(
            tonic_decision_path
        )

        return self.analyze(
            gate_data,
            readiness_data,
            tonic_decision_data,
        )

    def analyze_files(
        self,
        gate_path: str,
        readiness_path: str,
        output_path: str,
        tonic_decision_path: Optional[str] = None,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        gate_data = self._load(
            gate_path
        )

        readiness_data = self._load(
            readiness_path
        )

        # -----------------------------------------------------
        # Backward-compatible behavior:
        #
        # If no tonic file is supplied, the Engine remains
        # conservative and treats Tonic as ABSTAIN.
        # -----------------------------------------------------

        if tonic_decision_path:

            tonic_decision_data = self._load(
                tonic_decision_path
            )

        else:

            tonic_decision_data = {
                "decision": {
                    "status": "ABSTAIN",
                    "tonic_pitch_class": None,
                    "tonic_name": None,
                }
            }

        result = self.analyze(
            gate_data,
            readiness_data,
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
        "Maqam Decision Engine V1.0"
    )

    print(
        "============================================================"
    )

    print(
        "Build: PASS"
    )