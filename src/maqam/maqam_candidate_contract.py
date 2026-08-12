"""
PhoenixVoiceEngine
Maqam Candidate Contract V1.0

Responsibilities
----------------
1. Normalize maqam candidates.
2. Validate maqam candidate structure.
3. Preserve original candidate evidence.
4. Bind a maqam candidate to an already-decided tonic.
5. Never make a maqam decision.
6. Never select a Jins.
7. Never modify source audio or source scores.
8. Never override an abstained tonic decision.
"""

from typing import Any, Dict, List, Optional


class MaqamCandidateContract:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    # =========================================================
    # Contract identity
    # =========================================================

    CONTRACT_NAME = "Maqam Candidate Contract"

    # =========================================================
    # Required candidate fields
    # =========================================================

    REQUIRED_FIELDS = (
        "maqam",
        "tonic_pitch_class",
        "tonic_name",
        "readiness_score",
        "candidate_support",
        "support_share",
        "support_margin",
        "support_rank",
        "supporting_components",
        "strong_candidate_components",
        "opposing_components",
        "meaningful_opposing_components",
        "blockers",
        "status",
    )

    # =========================================================
    # Supported tonic names
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

    # =========================================================
    # Maqam aliases
    # =========================================================

    MAQAM_ALIASES = {
        "rast": "Rast",
        "rast maqam": "Rast",

        "bayati": "Bayati",
        "bayyati": "Bayati",

        "hijaz": "Hijaz",

        "saba": "Saba",

        "nahawand": "Nahawand",

        "kurd": "Kurd",

        "ajam": "Ajam",

        "sikah": "Sikah",

        "segah": "Sikah",

        "iraq": "Iraq",

        "iraqi": "Iraq",

        "nikriz": "Nikriz",

        "huzam": "Huzam",

        "suznak": "Suznak",

        "homayun": "Homayun",
    }

    # =========================================================
    # Basic helpers
    # =========================================================

    @staticmethod
    def normalize_pitch_class(
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

    # =========================================================
    # Pitch-class name
    # =========================================================

    @classmethod
    def pitch_class_name(
        cls,
        value: Any,
    ) -> Optional[str]:

        pitch_class = (
            cls.normalize_pitch_class(
                value
            )
        )

        if pitch_class is None:
            return None

        return cls.PITCH_CLASS_NAMES.get(
            pitch_class
        )

    # =========================================================
    # Tonic normalization
    # =========================================================

    @classmethod
    def normalize_tonic(
        cls,
        value: Any,
    ) -> Optional[str]:

        if value is None:
            return None

        text = str(
            value
        ).strip()

        if not text:
            return None

        text_lower = text.lower()

        aliases = {
            "do": "C",
            "c": "C",

            "do#": "C#",
            "c#": "C#",
            "reb": "C#",

            "re": "D",
            "d": "D",

            "re#": "D#",
            "d#": "D#",
            "mib": "D#",

            "mi": "E",
            "e": "E",

            "fa": "F",
            "f": "F",

            "fa#": "F#",
            "f#": "F#",
            "solb": "F#",

            "sol": "G",
            "g": "G",

            "sol#": "G#",
            "g#": "G#",
            "lab": "G#",

            "la": "A",
            "a": "A",

            "la#": "A#",
            "a#": "A#",
            "sib": "A#",

            "si": "B",
            "b": "B",
        }

        return aliases.get(
            text_lower,
            text.upper()
        )

    # =========================================================
    # Maqam normalization
    # =========================================================

    @classmethod
    def normalize_maqam(
        cls,
        value: Any,
    ) -> Optional[str]:

        if value is None:
            return None

        text = str(
            value
        ).strip()

        if not text:
            return None

        key = (
            text.lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        key = " ".join(
            key.split()
        )

        return cls.MAQAM_ALIASES.get(
            key,
            text
        )

    # =========================================================
    # Status normalization
    # =========================================================

    @staticmethod
    def normalize_status(
        value: Any,
    ) -> str:

        if value is None:
            return "UNKNOWN"

        text = str(
            value
        ).strip().upper()

        aliases = {
            "READY": "READY",
            "OPEN": "READY",

            "NOT_READY": "NOT_READY",
            "NOT READY": "NOT_READY",

            "BLOCKED": "BLOCKED",

            "ABSTAIN": "ABSTAIN",

            "UNKNOWN": "UNKNOWN",
        }

        return aliases.get(
            text,
            text
        )

    # =========================================================
    # Numeric normalization
    # =========================================================

    @staticmethod
    def _float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        try:
            return float(
                value
            )

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
            0.0
        )

        return max(
            0.0,
            min(
                1.0,
                value,
            ),
        )

    @classmethod
    def _support(
        cls,
        value: Any,
    ) -> float:

        value = cls._float(
            value,
            0.0
        )

        return max(
            0.0,
            value,
        )

    # =========================================================
    # List normalization
    # =========================================================

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
            return list(
                value
            )

        if isinstance(
            value,
            tuple,
        ):
            return list(
                value
            )

        return [value]

    # =========================================================
    # Candidate builder
    # =========================================================

    @classmethod
    def build(
        cls,
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not isinstance(
            candidate,
            dict,
        ):
            candidate = {}

        result = dict(
            candidate
        )

        # -----------------------------------------------------
        # Maqam
        # -----------------------------------------------------

        maqam = cls.normalize_maqam(
            result.get(
                "maqam"
            )
        )

        result[
            "maqam"
        ] = maqam

        # -----------------------------------------------------
        # Tonic pitch class
        # -----------------------------------------------------

        tonic_pitch_class = (
            cls.normalize_pitch_class(
                result.get(
                    "tonic_pitch_class"
                )
            )
        )

        if tonic_pitch_class is None:

            tonic_pitch_class = (
                cls.normalize_pitch_class(
                    result.get(
                        "pitch_class"
                    )
                )
            )

        result[
            "tonic_pitch_class"
        ] = tonic_pitch_class

        # -----------------------------------------------------
        # Tonic name
        # -----------------------------------------------------

        tonic_name = cls.normalize_tonic(
            result.get(
                "tonic_name"
            )
        )

        if tonic_name is None:

            tonic_name = cls.normalize_tonic(
                result.get(
                    "tonic"
                )
            )

        if tonic_name is None:

            tonic_name = cls.pitch_class_name(
                tonic_pitch_class
            )

        result[
            "tonic_name"
        ] = tonic_name

        # -----------------------------------------------------
        # Core scores
        # -----------------------------------------------------

        result[
            "readiness_score"
        ] = cls._score(
            result.get(
                "readiness_score",
                0.0,
            )
        )

        result[
            "candidate_support"
        ] = cls._support(
            result.get(
                "candidate_support",
                result.get(
                    "support",
                    0.0,
                ),
            )
        )

        result[
            "support_share"
        ] = cls._score(
            result.get(
                "support_share",
                0.0,
            )
        )

        result[
            "support_margin"
        ] = cls._float(
            result.get(
                "support_margin",
                0.0,
            )
        )

        # -----------------------------------------------------
        # Rank
        # -----------------------------------------------------

        try:

            result[
                "support_rank"
            ] = int(
                result.get(
                    "support_rank",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            result[
                "support_rank"
            ] = 0

        # -----------------------------------------------------
        # Components
        # -----------------------------------------------------

        result[
            "supporting_components"
        ] = cls._list(
            result.get(
                "supporting_components",
                [],
            )
        )

        result[
            "opposing_components"
        ] = cls._list(
            result.get(
                "opposing_components",
                [],
            )
        )

        result[
            "blockers"
        ] = cls._list(
            result.get(
                "blockers",
                [],
            )
        )

        try:

            result[
                "strong_candidate_components"
            ] = int(
                result.get(
                    "strong_candidate_components",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            result[
                "strong_candidate_components"
            ] = 0

        try:

            result[
                "meaningful_opposing_components"
            ] = int(
                result.get(
                    "meaningful_opposing_components",
                    0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            result[
                "meaningful_opposing_components"
            ] = 0

        # -----------------------------------------------------
        # Status
        # -----------------------------------------------------

        result[
            "status"
        ] = cls.normalize_status(
            result.get(
                "status"
            )
        )

        return result

    # =========================================================
    # Candidate list builder
    # =========================================================

    @classmethod
    def build_candidates(
        cls,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        if not isinstance(
            candidates,
            list,
        ):
            return []

        return [
            cls.build(
                candidate
            )
            for candidate in candidates
        ]

    # =========================================================
    # Validation
    # =========================================================

    @classmethod
    def validate(
        cls,
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:

        errors: List[str] = []
        warnings: List[str] = []

        if not isinstance(
            candidate,
            dict,
        ):

            return {
                "valid": False,
                "errors": [
                    "INVALID_CANDIDATE"
                ],
                "warnings": [],
            }

        # -----------------------------------------------------
        # Required fields
        # -----------------------------------------------------

        for field in cls.REQUIRED_FIELDS:

            if field not in candidate:

                errors.append(
                    f"MISSING_FIELD:{field}"
                )

        # -----------------------------------------------------
        # Maqam
        # -----------------------------------------------------

        if not candidate.get(
            "maqam"
        ):

            errors.append(
                "MAQAM_MISSING"
            )

        # -----------------------------------------------------
        # Tonic
        # -----------------------------------------------------

        if (
            "tonic_pitch_class"
            not in candidate
        ):

            warnings.append(
                "TONIC_PITCH_CLASS_MISSING"
            )

        else:

            pc = cls.normalize_pitch_class(
                candidate.get(
                    "tonic_pitch_class"
                )
            )

            if pc is None:

                errors.append(
                    "INVALID_TONIC_PITCH_CLASS"
                )

        if not candidate.get(
            "tonic_name"
        ):

            errors.append(
                "TONIC_NAME_MISSING"
            )

        # -----------------------------------------------------
        # Scores
        # -----------------------------------------------------

        score_fields = (
            "readiness_score",
            "support_share",
        )

        for field in score_fields:

            if field not in candidate:
                continue

            try:

                value = float(
                    candidate[field]
                )

                if not (
                    0.0
                    <= value
                    <= 1.0
                ):

                    errors.append(
                        f"INVALID_SCORE_RANGE:{field}"
                    )

            except (
                TypeError,
                ValueError,
            ):

                errors.append(
                    f"INVALID_SCORE:{field}"
                )

        # -----------------------------------------------------
        # Support
        # -----------------------------------------------------

        if (
            "candidate_support"
            in candidate
        ):

            try:

                if float(
                    candidate[
                        "candidate_support"
                    ]
                ) < 0.0:

                    errors.append(
                        "INVALID_CANDIDATE_SUPPORT"
                    )

            except (
                TypeError,
                ValueError,
            ):

                errors.append(
                    "INVALID_CANDIDATE_SUPPORT"
                )

        # -----------------------------------------------------
        # Collections
        # -----------------------------------------------------

        for field in (
            "supporting_components",
            "opposing_components",
            "blockers",
        ):

            if field in candidate:

                if not isinstance(
                    candidate[field],
                    list,
                ):

                    errors.append(
                        f"INVALID_LIST:{field}"
                    )

        # -----------------------------------------------------
        # Status
        # -----------------------------------------------------

        if candidate.get(
            "status"
        ) == "UNKNOWN":

            warnings.append(
                "STATUS_UNKNOWN"
            )

        # -----------------------------------------------------
        # Final
        # -----------------------------------------------------

        return {
            "valid": len(
                errors
            ) == 0,

            "errors": errors,

            "warnings": warnings,
        }

    # =========================================================
    # Decision eligibility
    # =========================================================

    @classmethod
    def is_decision_eligible(
        cls,
        candidate: Dict[str, Any],
        tonic_decision: Optional[
            Dict[str, Any]
        ] = None,
    ) -> bool:

        validation = cls.validate(
            candidate
        )

        if not validation[
            "valid"
        ]:
            return False

        if candidate.get(
            "blockers"
        ):
            return False

        if candidate.get(
            "status"
        ) not in (
            "READY",
            "OPEN",
        ):
            return False

        # -----------------------------------------------------
        # If a tonic decision is supplied, it must be an actual
        # decision. An abstained tonic can never become a maqam
        # decision through this contract.
        # -----------------------------------------------------

        if tonic_decision is not None:

            if not isinstance(
                tonic_decision,
                dict,
            ):
                return False

            if tonic_decision.get(
                "status"
            ) != "DECIDED":
                return False

            tonic_pc = (
                cls.normalize_pitch_class(
                    tonic_decision.get(
                        "tonic_pitch_class"
                    )
                )
            )

            candidate_pc = (
                cls.normalize_pitch_class(
                    candidate.get(
                        "tonic_pitch_class"
                    )
                )
            )

            if (
                tonic_pc is None
                or candidate_pc is None
            ):
                return False

            if tonic_pc != candidate_pc:
                return False

        return True

    # =========================================================
    # Tonic binding
    # =========================================================

    @classmethod
    def bind_tonic(
        cls,
        candidate: Dict[str, Any],
        tonic_decision: Dict[str, Any],
    ) -> Dict[str, Any]:

        result = cls.build(
            candidate
        )

        # -----------------------------------------------------
        # Protection:
        # Never bind an abstained tonic.
        # -----------------------------------------------------

        if not isinstance(
            tonic_decision,
            dict,
        ):

            result[
                "tonic_binding_status"
            ] = "BLOCKED"

            result[
                "tonic_binding_reason"
            ] = [
                "INVALID_TONIC_DECISION"
            ]

            return result

        if tonic_decision.get(
            "status"
        ) != "DECIDED":

            result[
                "tonic_binding_status"
            ] = "BLOCKED"

            result[
                "tonic_binding_reason"
            ] = [
                "TONIC_DECISION_NOT_DECIDED",
                "MAQAM_CANDIDATE_CANNOT_PROMOTE_ABSTAINED_TONIC",
            ]

            return result

        tonic_pc = (
            cls.normalize_pitch_class(
                tonic_decision.get(
                    "tonic_pitch_class"
                )
            )
        )

        candidate_pc = (
            cls.normalize_pitch_class(
                result.get(
                    "tonic_pitch_class"
                )
            )
        )

        if tonic_pc is None:

            result[
                "tonic_binding_status"
            ] = "BLOCKED"

            result[
                "tonic_binding_reason"
            ] = [
                "TONIC_PITCH_CLASS_MISSING"
            ]

            return result

        if candidate_pc is None:

            result[
                "tonic_binding_status"
            ] = "BLOCKED"

            result[
                "tonic_binding_reason"
            ] = [
                "CANDIDATE_TONIC_PITCH_CLASS_MISSING"
            ]

            return result

        if tonic_pc != candidate_pc:

            result[
                "tonic_binding_status"
            ] = "BLOCKED"

            result[
                "tonic_binding_reason"
            ] = [
                "TONIC_MISMATCH"
            ]

            return result

        # -----------------------------------------------------
        # Successful binding.
        # -----------------------------------------------------

        result[
            "tonic_binding_status"
        ] = "BOUND"

        result[
            "tonic_binding_reason"
        ] = [
            "TONIC_DECISION_CONFIRMED",
            "TONIC_MATCH_CONFIRMED",
        ]

        result[
            "bound_tonic_pitch_class"
        ] = tonic_pc

        result[
            "bound_tonic_name"
        ] = cls.pitch_class_name(
            tonic_pc
        )

        return result

    # =========================================================
    # Document builder
    # =========================================================

    @classmethod
    def build_document(
        cls,
        candidates: List[Dict[str, Any]],
        tonic_decision: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict[str, Any]:

        normalized = (
            cls.build_candidates(
                candidates
            )
        )

        validations = []

        for candidate in normalized:

            validation = cls.validate(
                candidate
            )

            validations.append(
                {
                    "maqam":
                        candidate.get(
                            "maqam"
                        ),

                    "valid":
                        validation[
                            "valid"
                        ],

                    "errors":
                        validation[
                            "errors"
                        ],

                    "warnings":
                        validation[
                            "warnings"
                        ],
                }
            )

        # -----------------------------------------------------
        # Tonic binding is optional at contract construction.
        # If supplied, it is strictly validated.
        # -----------------------------------------------------

        bound_candidates = []

        if tonic_decision is not None:

            for candidate in normalized:

                bound_candidates.append(
                    cls.bind_tonic(
                        candidate,
                        tonic_decision,
                    )
                )

        return {
            "version":
                cls.VERSION,

            "feature_version":
                cls.FEATURE_VERSION,

            "patch_version":
                cls.PATCH_VERSION,

            "contract": {

                "name":
                    cls.CONTRACT_NAME,

                "decision_making":
                    False,

                "maqam_selection":
                    False,

                "jins_selection":
                    False,

                "tonic_selection":
                    False,

                "source_modification":
                    False,

                "source_score_modification":
                    False,
            },

            "candidates":
                normalized,

            "validations":
                validations,

            "tonic_binding":
                bound_candidates,

            "protection": {

                "tonic_decision_made":
                    False,

                "maqam_decision_made":
                    False,

                "jins_decision_made":
                    False,

                "contract_selected_maqam":
                    False,

                "contract_selected_tonic":
                    False,

                "contract_selected_jins":
                    False,

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

                "original_scores_preserved":
                    True,

                "original_decision_overridden":
                    False,

                "tonic_abstention_overridden":
                    False,
            },
        }