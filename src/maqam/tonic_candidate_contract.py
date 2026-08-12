"""
PhoenixVoiceEngine
Tonic Candidate Contract V1.0

Purpose
-------
Defines a stable, normalized contract for tonic candidates
moving through the tonic decision pipeline.

Pipeline
--------
Evidence
    ↓
Fusion
    ↓
Reliability
    ↓
Consensus
    ↓
Conflict
    ↓
Readiness
    ↓
Tonic Candidate Contract
    ↓
Gate
    ↓
Decision Engine
    ↓
Maqam Decision

Safety
------
- This module does not make a tonic decision.
- This module does not modify source audio.
- This module does not modify pitch.
- This module does not modify timing.
- This module does not select Maqam.
- This module does not select Jins.
- It only normalizes and validates candidate data.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class TonicCandidateContract:
    """
    Tonic Candidate Contract V1.0.

    A normalized candidate always exposes:

        tonic
        tonic_pitch_class
        readiness_score
        candidate_support
        support_share
        support_margin
        support_rank
        supporting_components
        strong_candidate_components
        opposing_components
        meaningful_opposing_components
        blockers
        status

    The contract is descriptive only.
    It never decides the tonic.
    """

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

    REQUIRED_FIELDS = (
        "tonic",
        "tonic_pitch_class",
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

    # ---------------------------------------------------------
    # Basic helpers
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
    # Pitch class
    # ---------------------------------------------------------

    @classmethod
    def normalize_pitch_class(
        cls,
        value: Any,
    ) -> Optional[int]:

        if value is None:
            return None

        try:
            value = int(value)
        except (TypeError, ValueError):
            return None

        return value % 12

    @classmethod
    def pitch_class_name(
        cls,
        pitch_class: Any,
    ) -> Optional[str]:

        pc = cls.normalize_pitch_class(
            pitch_class
        )

        if pc is None:
            return None

        return cls.PITCH_CLASS_NAMES.get(pc)

    @classmethod
    def normalize_tonic(
        cls,
        value: Any,
    ) -> Optional[str]:

        if value is None:
            return None

        value = str(value).strip()

        if not value:
            return None

        # Normalize common textual representations.
        aliases = {
            "DO": "C",
            "RE": "D",
            "MI": "E",
            "FA": "F",
            "SOL": "G",
            "LA": "A",
            "SI": "B",
            "TI": "B",
        }

        upper = value.upper()

        if upper in aliases:
            return aliases[upper]

        # Normalize pitch names.
        canonical = {
            "C": "C",
            "C#": "C#",
            "DB": "C#",
            "D": "D",
            "D#": "D#",
            "EB": "D#",
            "E": "E",
            "F": "F",
            "F#": "F#",
            "GB": "F#",
            "G": "G",
            "G#": "G#",
            "AB": "G#",
            "A": "A",
            "A#": "A#",
            "BB": "A#",
            "B": "B",
            "CB": "B",
        }

        return canonical.get(
            upper,
            value,
        )

    # ---------------------------------------------------------
    # Field extraction
    # ---------------------------------------------------------

    @classmethod
    def _extract_pitch_class(
        cls,
        candidate: Dict[str, Any],
    ) -> Optional[int]:

        keys = (
            "tonic_pitch_class",
            "pitch_class",
            "pitch_class_id",
            "tonic_pc",
        )

        for key in keys:
            if key in candidate:
                pc = cls.normalize_pitch_class(
                    candidate.get(key)
                )

                if pc is not None:
                    return pc

        return None

    @classmethod
    def _extract_tonic(
        cls,
        candidate: Dict[str, Any],
        pitch_class: Optional[int],
    ) -> Optional[str]:

        for key in (
            "tonic",
            "tonic_name",
            "name",
        ):
            value = candidate.get(key)

            normalized = cls.normalize_tonic(
                value
            )

            if normalized:
                return normalized

        return cls.pitch_class_name(
            pitch_class
        )

    # ---------------------------------------------------------
    # Component lists
    # ---------------------------------------------------------

    @staticmethod
    def _list(
        value: Any,
    ) -> List[Any]:

        if isinstance(value, list):
            return list(value)

        if value is None:
            return []

        return [value]

    # ---------------------------------------------------------
    # Build
    # ---------------------------------------------------------

    @classmethod
    def build(
        cls,
        candidate: Dict[str, Any],
        *,
        rank: Optional[int] = None,
    ) -> Dict[str, Any]:

        if not isinstance(
            candidate,
            dict,
        ):
            raise TypeError(
                "candidate must be a dictionary"
            )

        pitch_class = cls._extract_pitch_class(
            candidate
        )

        tonic = cls._extract_tonic(
            candidate,
            pitch_class,
        )

        readiness_score = cls._clamp(
            cls._float(
                candidate.get(
                    "readiness_score",
                    candidate.get(
                        "readiness",
                        0.0,
                    ),
                )
            )
        )

        candidate_support = max(
            0.0,
            cls._float(
                candidate.get(
                    "candidate_support",
                    candidate.get(
                        "support",
                        0.0,
                    ),
                )
            ),
        )

        support_share = cls._clamp(
            cls._float(
                candidate.get(
                    "support_share",
                    0.0,
                )
            )
        )

        support_margin = cls._float(
            candidate.get(
                "support_margin",
                0.0,
            )
        )

        support_rank = cls._int(
            candidate.get(
                "support_rank",
                rank if rank is not None else 0,
            )
        )

        supporting_components = cls._list(
            candidate.get(
                "supporting_components",
                [],
            )
        )

        strong_candidate_components = cls._int(
            candidate.get(
                "strong_candidate_components",
                len(supporting_components),
            )
        )

        opposing_components = cls._list(
            candidate.get(
                "opposing_components",
                [],
            )
        )

        meaningful_opposing_components = cls._int(
            candidate.get(
                "meaningful_opposing_components",
                0,
            )
        )

        blockers = cls._list(
            candidate.get(
                "blockers",
                [],
            )
        )

        status = candidate.get(
            "status",
            "NOT_READY",
        )

        status = str(
            status
        ).strip().upper()

        return {
            "contract_version": cls.VERSION,

            "tonic": tonic,

            "tonic_pitch_class": pitch_class,

            "readiness_score": cls._round(
                readiness_score
            ),

            "candidate_support": cls._round(
                candidate_support
            ),

            "support_share": cls._round(
                support_share
            ),

            "support_margin": cls._round(
                support_margin
            ),

            "support_rank": support_rank,

            "supporting_components": (
                supporting_components
            ),

            "strong_candidate_components": (
                strong_candidate_components
            ),

            "opposing_components": (
                opposing_components
            ),

            "meaningful_opposing_components": (
                meaningful_opposing_components
            ),

            "blockers": blockers,

            "status": status,
        }

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

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
                    "CANDIDATE_NOT_DICTIONARY"
                ],
                "warnings": [],
            }

        for field in cls.REQUIRED_FIELDS:
            if field not in candidate:
                errors.append(
                    f"MISSING_FIELD:{field}"
                )

        if candidate.get(
            "tonic"
        ) is None:
            errors.append(
                "TONIC_MISSING"
            )

        pitch_class = candidate.get(
            "tonic_pitch_class"
        )

        if pitch_class is None:
            warnings.append(
                "TONIC_PITCH_CLASS_MISSING"
            )
        else:
            normalized = cls.normalize_pitch_class(
                pitch_class
            )

            if normalized is None:
                errors.append(
                    "TONIC_PITCH_CLASS_INVALID"
                )

        readiness = cls._float(
            candidate.get(
                "readiness_score",
                0.0,
            )
        )

        if not 0.0 <= readiness <= 1.0:
            errors.append(
                "READINESS_SCORE_OUT_OF_RANGE"
            )

        support_share = cls._float(
            candidate.get(
                "support_share",
                0.0,
            )
        )

        if not 0.0 <= support_share <= 1.0:
            errors.append(
                "SUPPORT_SHARE_OUT_OF_RANGE"
            )

        support = cls._float(
            candidate.get(
                "candidate_support",
                0.0,
            )
        )

        if support < 0.0:
            errors.append(
                "CANDIDATE_SUPPORT_NEGATIVE"
            )

        if not isinstance(
            candidate.get(
                "supporting_components"
            ),
            list,
        ):
            errors.append(
                "SUPPORTING_COMPONENTS_NOT_LIST"
            )

        if not isinstance(
            candidate.get(
                "opposing_components"
            ),
            list,
        ):
            errors.append(
                "OPPOSING_COMPONENTS_NOT_LIST"
            )

        if not isinstance(
            candidate.get(
                "blockers"
            ),
            list,
        ):
            errors.append(
                "BLOCKERS_NOT_LIST"
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    # ---------------------------------------------------------
    # Contract status
    # ---------------------------------------------------------

    @classmethod
    def is_decision_eligible(
        cls,
        candidate: Dict[str, Any],
    ) -> bool:

        validation = cls.validate(
            candidate
        )

        if not validation["valid"]:
            return False

        if candidate.get(
            "status"
        ) != "READY":
            return False

        if candidate.get(
            "blockers"
        ):
            return False

        if candidate.get(
            "tonic"
        ) is None:
            return False

        if candidate.get(
            "tonic_pitch_class"
        ) is None:
            return False

        return True

    # ---------------------------------------------------------
    # Batch building
    # ---------------------------------------------------------

    @classmethod
    def build_candidates(
        cls,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        if not isinstance(
            candidates,
            list,
        ):
            raise TypeError(
                "candidates must be a list"
            )

        result = []

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):
            result.append(
                cls.build(
                    candidate,
                    rank=index,
                )
            )

        return result

    # ---------------------------------------------------------
    # Contract document
    # ---------------------------------------------------------

    @classmethod
    def build_document(
        cls,
        candidates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        normalized = cls.build_candidates(
            candidates
        )

        validations = [
            cls.validate(candidate)
            for candidate in normalized
        ]

        return {
            "version": cls.VERSION,
            "feature_version": cls.FEATURE_VERSION,
            "patch_version": cls.PATCH_VERSION,

            "contract": {
                "name": "Tonic Candidate Contract",
                "version": cls.VERSION,
                "decision_making": False,
                "source_modification": False,
                "maqam_selection": False,
                "jins_selection": False,
            },

            "candidates": normalized,

            "validation": {
                "all_valid": all(
                    item["valid"]
                    for item in validations
                ),
                "results": validations,
            },

            "protection": {
                "source_pitch_modified": False,
                "source_timing_modified": False,
                "source_performance_modified": False,
                "source_scores_modified": False,

                "tonic_decision_made": False,
                "maqam_decision_made": False,
                "jins_decision_made": False,

                "contract_selected_tonic": False,
                "source_audio_modified": False,
            },
        }


if __name__ == "__main__":
    contract = TonicCandidateContract()

    print(
        "PhoenixVoiceEngine"
    )
    print(
        "Tonic Candidate Contract V1.0"
    )
    print("=" * 60)
    print(
        "Version:",
        contract.VERSION
    )
    print(
        "Feature Version:",
        contract.FEATURE_VERSION
    )
    print(
        "Patch Version:",
        contract.PATCH_VERSION
    )
    print(
        "Decision Making:",
        False
    )
    print(
        "Source Modification:",
        False
    )