"""
PhoenixVoiceEngine
Tonic Decision Engine V1.1

Responsibilities
----------------
1. Read the Tonic Decision Gate.
2. Read Tonic Decision Readiness.
3. Normalize candidates through Tonic Candidate Contract V1.0.
4. Filter invalid / blocked candidates.
5. Rank valid candidates.
6. Make a tonic decision ONLY when the gate is OPEN.
7. Never select Maqam.
8. Never select Jins.
9. Never modify source audio, timing, performance, or source scores.
10. Never bypass a CLOSED gate.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.maqam.tonic_candidate_contract import (
    TonicCandidateContract,
)


class TonicDecisionEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    # =========================================================
    # Decision thresholds
    # =========================================================

    MIN_READINESS_SCORE = 0.80
    MIN_SUPPORT_MARGIN = 0.15
    MIN_SUPPORT_SHARE = 0.60

    MIN_DECISION_MARGIN = 0.15

    # =========================================================
    # IO
    # =========================================================

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

    # =========================================================
    # Helpers
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

    # =========================================================
    # Pitch-class names
    # =========================================================

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

    @classmethod
    def _tonic_name(
        cls,
        pitch_class: Any,
    ) -> Optional[str]:

        try:
            pc = int(pitch_class)

        except (
            TypeError,
            ValueError,
        ):
            return None

        return cls.PITCH_CLASS_NAMES.get(
            pc % 12
        )

    # =========================================================
    # Gate extraction
    # =========================================================

    def _extract_gate(
        self,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        gate = data.get(
            "gate",
            {},
        )

        if not isinstance(
            gate,
            dict,
        ):
            gate = {}

        blockers = gate.get(
            "blockers",
            [],
        )

        if not isinstance(
            blockers,
            list,
        ):
            blockers = []

        return {
            "status": gate.get(
                "status",
                "CLOSED",
            ),

            "level": gate.get(
                "level",
                "ABSTAIN",
            ),

            "decision_allowed": bool(
                gate.get(
                    "decision_allowed",
                    False,
                )
            ),

            "abstention_required": bool(
                gate.get(
                    "abstention_required",
                    True,
                )
            ),

            "passed_checks": int(
                self._float(
                    gate.get(
                        "passed_checks",
                        0,
                    )
                )
            ),

            "total_checks": int(
                self._float(
                    gate.get(
                        "total_checks",
                        0,
                    )
                )
            ),

            "blockers": blockers,
        }

    # =========================================================
    # Readiness extraction
    # =========================================================

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

        global_data = readiness.get(
            "global",
            {},
        )

        if not isinstance(
            global_data,
            dict,
        ):
            global_data = {}

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
            "status": global_data.get(
                "status",
                "NOT_READY",
            ),

            "readiness_score": self._clamp(
                self._float(
                    global_data.get(
                        "readiness_score",
                        0.0,
                    )
                )
            ),

            "top_candidate": global_data.get(
                "top_candidate"
            ),

            "top_readiness": self._clamp(
                self._float(
                    global_data.get(
                        "top_readiness",
                        0.0,
                    )
                )
            ),

            "second_candidate": global_data.get(
                "second_candidate"
            ),

            "second_readiness": self._clamp(
                self._float(
                    global_data.get(
                        "second_readiness",
                        0.0,
                    )
                )
            ),

            "global_blockers": list(
                global_data.get(
                    "global_blockers",
                    [],
                )
            ),

            "candidates": candidates,
        }

    # =========================================================
    # Candidate normalization
    # =========================================================

    def _normalize_candidate(
        self,
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(
            candidate,
            dict,
        ):
            return {
                "tonic": None,
                "tonic_pitch_class": None,
                "readiness_score": 0.0,
                "candidate_support": 0.0,
                "supporting_components": [],
                "opposing_components": [],
                "blockers": [
                    "INVALID_CANDIDATE"
                ],
                "original": candidate,
                "contract_valid": False,
                "contract_errors": [
                    "INVALID_CANDIDATE"
                ],
            }

        # -----------------------------------------------------
        # Preserve the original source candidate.
        # -----------------------------------------------------

        original = dict(candidate)

        # -----------------------------------------------------
        # Prepare a contract-compatible candidate.
        # -----------------------------------------------------

        contract_input = dict(candidate)

        tonic = contract_input.get(
            "tonic"
        )

        pitch_class = contract_input.get(
            "tonic_pitch_class"
        )

        if pitch_class is None:
            pitch_class = contract_input.get(
                "pitch_class"
            )

        if pitch_class is None:
            pitch_class = contract_input.get(
                "pitch_class_id"
            )

        if pitch_class is not None:

            try:
                pitch_class = int(
                    pitch_class
                )

                pitch_class %= 12

                contract_input[
                    "tonic_pitch_class"
                ] = pitch_class

            except (
                TypeError,
                ValueError,
            ):
                pitch_class = None

        # -----------------------------------------------------
        # If tonic is missing, derive it from pitch class.
        # -----------------------------------------------------

        if tonic is None:
            tonic = self._tonic_name(
                pitch_class
            )

            if tonic is not None:
                contract_input[
                    "tonic"
                ] = tonic

        # -----------------------------------------------------
        # Normalize core numeric fields.
        # -----------------------------------------------------

        readiness_score = self._clamp(
            self._float(
                contract_input.get(
                    "readiness_score",
                    0.0,
                )
            )
        )

        support = contract_input.get(
            "candidate_support"
        )

        if support is None:
            support = contract_input.get(
                "support",
                0.0,
            )

        support = max(
            0.0,
            self._float(
                support
            ),
        )

        contract_input[
            "readiness_score"
        ] = readiness_score

        contract_input[
            "candidate_support"
        ] = support

        # -----------------------------------------------------
        # Normalize list fields.
        # -----------------------------------------------------

        blockers = contract_input.get(
            "blockers",
            [],
        )

        if not isinstance(
            blockers,
            list,
        ):
            blockers = []

        supporting = contract_input.get(
            "supporting_components",
            [],
        )

        if not isinstance(
            supporting,
            list,
        ):
            supporting = []

        opposing = contract_input.get(
            "opposing_components",
            [],
        )

        if not isinstance(
            opposing,
            list,
        ):
            opposing = []

        contract_input[
            "blockers"
        ] = list(blockers)

        contract_input[
            "supporting_components"
        ] = list(supporting)

        contract_input[
            "opposing_components"
        ] = list(opposing)

        # -----------------------------------------------------
        # CONTRACT INTEGRATION
        # -----------------------------------------------------

        contract_valid = False
        contract_errors: List[str] = []
        contract_warnings: List[str] = []

        try:

            normalized_contract = (
                TonicCandidateContract.build(
                    contract_input
                )
            )

            if isinstance(
                normalized_contract,
                dict,
            ):
                contract_input.update(
                    normalized_contract
                )

            validation = (
                TonicCandidateContract.validate(
                    contract_input
                )
            )

            if isinstance(
                validation,
                dict,
            ):

                contract_valid = bool(
                    validation.get(
                        "valid",
                        False,
                    )
                )

                contract_errors = list(
                    validation.get(
                        "errors",
                        [],
                    )
                )

                contract_warnings = list(
                    validation.get(
                        "warnings",
                        [],
                    )
                )

        except Exception as exc:

            # Contract failure must never silently
            # become a tonic decision.
            contract_valid = False

            contract_errors = [
                "CONTRACT_VALIDATION_ERROR"
            ]

            contract_warnings = [
                str(exc)
            ]

        # -----------------------------------------------------
        # Final normalized candidate.
        # -----------------------------------------------------

        final_tonic = contract_input.get(
            "tonic"
        )

        final_pitch_class = (
            contract_input.get(
                "tonic_pitch_class"
            )
        )

        if final_pitch_class is not None:

            try:
                final_pitch_class = (
                    int(final_pitch_class) % 12
                )

            except (
                TypeError,
                ValueError,
            ):
                final_pitch_class = None

        if final_tonic is None:
            final_tonic = self._tonic_name(
                final_pitch_class
            )

        return {
            "tonic": final_tonic,

            "tonic_pitch_class":
                final_pitch_class,

            "readiness_score":
                self._clamp(
                    self._float(
                        contract_input.get(
                            "readiness_score",
                            readiness_score,
                        )
                    )
                ),

            "candidate_support":
                max(
                    0.0,
                    self._float(
                        contract_input.get(
                            "candidate_support",
                            support,
                        )
                    ),
                ),

            "supporting_components":
                list(
                    contract_input.get(
                        "supporting_components",
                        supporting,
                    )
                ),

            "opposing_components":
                list(
                    contract_input.get(
                        "opposing_components",
                        opposing,
                    )
                ),

            "blockers":
                list(
                    contract_input.get(
                        "blockers",
                        blockers,
                    )
                ),

            "original": original,

            "contract_valid":
                contract_valid,

            "contract_errors":
                contract_errors,

            "contract_warnings":
                contract_warnings,
        }

    # =========================================================
    # Candidate extraction
    # =========================================================

    def _extract_candidates(
        self,
        readiness: Dict[str, Any],
        candidates: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:

        raw = readiness.get(
            "candidates",
            [],
        )

        result: List[Dict[str, Any]] = []

        requested = None

        if candidates is not None:

            requested = set()

            for value in candidates:

                try:

                    requested.add(
                        int(value) % 12
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    continue

        for item in raw:

            if not isinstance(
                item,
                dict,
            ):
                continue

            normalized = (
                self._normalize_candidate(
                    item
                )
            )

            pc = normalized[
                "tonic_pitch_class"
            ]

            if (
                requested is not None
                and pc is not None
                and pc not in requested
            ):
                continue

            result.append(
                normalized
            )

        return result

    # =========================================================
    # Candidate validity
    # =========================================================

    def _candidate_is_valid(
        self,
        candidate: Dict[str, Any],
    ) -> bool:

        if not candidate.get(
            "tonic"
        ):
            return False

        if candidate.get(
            "tonic_pitch_class"
        ) is None:
            return False

        # Contract failure is a hard blocker.
        if not candidate.get(
            "contract_valid",
            False,
        ):
            return False

        if candidate.get(
            "contract_errors"
        ):
            return False

        if candidate.get(
            "blockers"
        ):
            return False

        readiness_score = candidate.get(
            "readiness_score",
            0.0,
        )

        if (
            readiness_score
            < self.MIN_READINESS_SCORE
        ):
            return False

        status = candidate.get(
            "original",
            {},
        ).get(
            "status"
        )

        if status is not None:

            if status not in (
                "READY",
                "OPEN",
            ):
                return False

        return True

    # =========================================================
    # Ranking
    # =========================================================

    def _rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        ranked = sorted(
            candidates,
            key=lambda x: (
                x["readiness_score"],
                x["candidate_support"],
            ),
            reverse=True,
        )

        for index, candidate in enumerate(
            ranked,
            start=1,
        ):
            candidate[
                "rank"
            ] = index

        return ranked

    # =========================================================
    # Decision safety
    # =========================================================

    def _decision_safety(
        self,
        gate: Dict[str, Any],
        readiness: Dict[str, Any],
        ranked: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        reasons: List[str] = []

        # -----------------------------------------------------
        # Gate safety
        # -----------------------------------------------------

        if gate["status"] != "OPEN":

            reasons.append(
                "GATE_CLOSED"
            )

        if not gate[
            "decision_allowed"
        ]:

            reasons.append(
                "GATE_DECISION_NOT_ALLOWED"
            )

        if gate.get(
            "abstention_required",
            False,
        ):

            reasons.append(
                "GATE_ABSTENTION_REQUIRED"
            )

        # -----------------------------------------------------
        # Readiness safety
        # -----------------------------------------------------

        if readiness["status"] != "READY":

            reasons.append(
                "READINESS_NOT_READY"
            )

        if (
            readiness[
                "readiness_score"
            ]
            < self.MIN_READINESS_SCORE
        ):

            reasons.append(
                "READINESS_SCORE_TOO_LOW"
            )

        # -----------------------------------------------------
        # Candidate validation
        # -----------------------------------------------------

        valid = [
            x
            for x in ranked
            if self._candidate_is_valid(x)
        ]

        if not valid:

            reasons.append(
                "NO_VALID_TONIC_CANDIDATE"
            )

        # -----------------------------------------------------
        # Decision margin
        # -----------------------------------------------------

        if len(valid) >= 2:

            first = valid[0]
            second = valid[1]

            margin = (
                first[
                    "readiness_score"
                ]
                - second[
                    "readiness_score"
                ]
            )

            if (
                margin
                < self.MIN_DECISION_MARGIN
            ):

                reasons.append(
                    "TONIC_MARGIN_TOO_SMALL"
                )

        return {
            "safe": len(reasons) == 0,

            "reasons": reasons,

            "valid_candidate_count":
                len(valid),
        }

    # =========================================================
    # Decision
    # =========================================================

    def _make_decision(
        self,
        gate: Dict[str, Any],
        readiness: Dict[str, Any],
        ranked: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        safety = self._decision_safety(
            gate=gate,
            readiness=readiness,
            ranked=ranked,
        )

        if not safety["safe"]:

            return {
                "status": "ABSTAIN",

                "tonic_pitch_class": None,

                "tonic_name": None,

                "confidence": None,

                "reason": safety[
                    "reasons"
                ],
            }

        valid = [
            x
            for x in ranked
            if self._candidate_is_valid(x)
        ]

        if not valid:

            return {
                "status": "ABSTAIN",
                "tonic_pitch_class": None,
                "tonic_name": None,
                "confidence": None,
                "reason": [
                    "NO_VALID_TONIC_CANDIDATE",
                    "ABSTAIN_REQUIRED",
                ],
            }

        selected = valid[0]

        if len(valid) >= 2:

            margin = (
                selected[
                    "readiness_score"
                ]
                - valid[1][
                    "readiness_score"
                ]
            )

        else:

            margin = selected[
                "readiness_score"
            ]

        confidence = self._clamp(
            (
                selected[
                    "readiness_score"
                ]
                + self._clamp(
                    selected[
                        "candidate_support"
                    ]
                )
                + self._clamp(
                    margin
                )
            )
            / 3.0
        )

        return {
            "status": "DECIDED",

            "tonic_pitch_class":
                selected[
                    "tonic_pitch_class"
                ],

            "tonic_name":
                selected[
                    "tonic"
                ],

            "confidence":
                self._round(
                    confidence
                ),

            "selected_rank":
                selected[
                    "rank"
                ],

            "readiness_score":
                self._round(
                    selected[
                        "readiness_score"
                    ]
                ),

            "candidate_support":
                self._round(
                    selected[
                        "candidate_support"
                    ]
                ),

            "margin":
                self._round(
                    margin
                ),

            "reason": [
                "TONIC_DECISION_GATE_OPEN",
                "READINESS_CONFIRMED",
                "VALID_TONIC_CANDIDATE",
                "TONIC_CANDIDATE_CONTRACT_VALID",
                "SUFFICIENT_TONIC_SEPARATION",
            ],
        }

    # =========================================================
    # Full analysis
    # =========================================================

    def analyze(
        self,
        gate_data: Dict[str, Any],
        readiness_data: Dict[str, Any],
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        gate = self._extract_gate(
            gate_data
        )

        readiness = self._extract_readiness(
            readiness_data
        )

        extracted = self._extract_candidates(
            readiness,
            candidates=candidates,
        )

        ranked = self._rank_candidates(
            extracted
        )

        safety = self._decision_safety(
            gate=gate,
            readiness=readiness,
            ranked=ranked,
        )

        decision = self._make_decision(
            gate=gate,
            readiness=readiness,
            ranked=ranked,
        )

        # =====================================================
        # CRITICAL SAFETY ASSERTION
        # =====================================================

        # A CLOSED gate can NEVER produce a decision.
        if gate["status"] != "OPEN":

            decision = {
                "status": "ABSTAIN",

                "tonic_pitch_class": None,

                "tonic_name": None,

                "confidence": None,

                "reason": [
                    "GATE_CLOSED",
                    "TONIC_DECISION_FORBIDDEN",
                    "ABSTAIN_REQUIRED",
                ],
            }

        # =====================================================
        # Additional safety:
        # Gate must explicitly allow the decision.
        # =====================================================

        if not gate[
            "decision_allowed"
        ]:

            decision = {
                "status": "ABSTAIN",

                "tonic_pitch_class": None,

                "tonic_name": None,

                "confidence": None,

                "reason": [
                    "GATE_CLOSED",
                    "TONIC_DECISION_FORBIDDEN",
                    "ABSTAIN_REQUIRED",
                ],
            }

        # =====================================================
        # Additional safety:
        # abstention_required always wins.
        # =====================================================

        if gate.get(
            "abstention_required",
            False,
        ):

            decision = {
                "status": "ABSTAIN",

                "tonic_pitch_class": None,

                "tonic_name": None,

                "confidence": None,

                "reason": [
                    "GATE_CLOSED",
                    "TONIC_DECISION_FORBIDDEN",
                    "ABSTAIN_REQUIRED",
                ],
            }

        # =====================================================
        # Contract information
        # =====================================================

        contract_candidates = []

        for candidate in ranked:

            contract_candidates.append(
                {
                    "rank": candidate.get(
                        "rank"
                    ),

                    "tonic": candidate.get(
                        "tonic"
                    ),

                    "tonic_pitch_class":
                        candidate.get(
                            "tonic_pitch_class"
                        ),

                    "contract_valid":
                        candidate.get(
                            "contract_valid",
                            False,
                        ),

                    "contract_errors":
                        candidate.get(
                            "contract_errors",
                            [],
                        ),

                    "contract_warnings":
                        candidate.get(
                            "contract_warnings",
                            [],
                        ),
                }
            )

        # =====================================================
        # Output
        # =====================================================

        return {
            "version":
                self.VERSION,

            "feature_version":
                self.FEATURE_VERSION,

            "patch_version":
                self.PATCH_VERSION,

            "gate": {
                "status":
                    gate[
                        "status"
                    ],

                "level":
                    gate[
                        "level"
                    ],

                "decision_allowed":
                    gate[
                        "decision_allowed"
                    ],

                "abstention_required":
                    gate[
                        "abstention_required"
                    ],

                "passed_checks":
                    gate[
                        "passed_checks"
                    ],

                "total_checks":
                    gate[
                        "total_checks"
                    ],

                "blockers":
                    gate[
                        "blockers"
                    ],
            },

            "readiness": {
                "status":
                    readiness[
                        "status"
                    ],

                "readiness_score":
                    readiness[
                        "readiness_score"
                    ],

                "top_candidate":
                    readiness[
                        "top_candidate"
                    ],

                "top_readiness":
                    readiness[
                        "top_readiness"
                    ],

                "second_candidate":
                    readiness[
                        "second_candidate"
                    ],

                "second_readiness":
                    readiness[
                        "second_readiness"
                    ],

                "global_blockers":
                    readiness[
                        "global_blockers"
                    ],
            },

            "candidate_contract": {
                "name":
                    "Tonic Candidate Contract",

                "version":
                    "1.0.0",

                "applied":
                    True,

                "decision_making":
                    False,

                "maqam_selection":
                    False,

                "jins_selection":
                    False,

                "source_modification":
                    False,

                "candidates":
                    contract_candidates,
            },

            "ranking": {
                "candidates": [
                    {
                        "rank":
                            x[
                                "rank"
                            ],

                        "tonic":
                            x[
                                "tonic"
                            ],

                        "tonic_pitch_class":
                            x[
                                "tonic_pitch_class"
                            ],

                        "readiness_score":
                            self._round(
                                x[
                                    "readiness_score"
                                ]
                            ),

                        "candidate_support":
                            self._round(
                                x[
                                    "candidate_support"
                                ]
                            ),

                        "supporting_components":
                            x[
                                "supporting_components"
                            ],

                        "opposing_components":
                            x[
                                "opposing_components"
                            ],

                        "blockers":
                            x[
                                "blockers"
                            ],

                        "contract_valid":
                            x.get(
                                "contract_valid",
                                False,
                            ),

                        "contract_errors":
                            x.get(
                                "contract_errors",
                                [],
                            ),

                        "contract_warnings":
                            x.get(
                                "contract_warnings",
                                [],
                            ),
                    }

                    for x in ranked
                ],

                "top": (
                    ranked[0]
                    if ranked
                    else None
                ),

                "second": (
                    ranked[1]
                    if len(ranked) > 1
                    else None
                ),
            },

            "decision_safety":
                safety,

            "decision":
                decision,

            "protection": {

                "source_pitch_modified":
                    False,

                "source_timing_modified":
                    False,

                "source_performance_modified":
                    False,

                "source_scores_modified":
                    False,

                "tonic_decision_made":
                    (
                        decision[
                            "status"
                        ]
                        == "DECIDED"
                    ),

                "maqam_decision_made":
                    False,

                "jins_decision_made":
                    False,

                "original_scores_preserved":
                    True,

                "original_decision_overridden":
                    False,

                "gate_bypassed":
                    False,

                "closed_gate_overridden":
                    False,

                "source_audio_modified":
                    False,

                "candidate_contract_bypassed":
                    False,

                "candidate_contract_modified_source":
                    False,

                "gate_remains_authoritative":
                    True,

                "readiness_promoted_to_decision":
                    False,
            },
        }

    # =========================================================
    # File API
    # =========================================================

    def analyze_files(
        self,
        gate_path: str,
        readiness_path: str,
        output_path: str,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        gate_data = self._load(
            gate_path
        )

        readiness_data = self._load(
            readiness_path
        )

        result = self.analyze(
            gate_data=gate_data,
            readiness_data=readiness_data,
            candidates=candidates,
        )

        self._save(
            output_path,
            result,
        )

        return result

    def analyze_file(
        self,
        gate_path: str,
        readiness_path: str,
        output_path: str,
        candidates: Optional[List[int]] = None,
    ) -> Dict[str, Any]:

        return self.analyze_files(
            gate_path=gate_path,
            readiness_path=readiness_path,
            output_path=output_path,
            candidates=candidates,
        )


# =============================================================
# CLI
# =============================================================

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "PhoenixVoiceEngine "
            "Tonic Decision Engine V1.0"
        )
    )

    parser.add_argument(
        "gate_path"
    )

    parser.add_argument(
        "readiness_path"
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

    engine = TonicDecisionEngine()

    result = engine.analyze_files(
        gate_path=args.gate_path,
        readiness_path=args.readiness_path,
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