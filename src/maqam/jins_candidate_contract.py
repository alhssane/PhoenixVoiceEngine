from typing import Any, Dict, List, Optional


class JinsCandidateContract:

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

    READY = "READY"
    NOT_READY = "NOT_READY"

    DECIDED = "DECIDED"
    ABSTAIN = "ABSTAIN"

    REQUIRED_FIELDS = [
        "tonic_pitch_class",
        "tonic_status",
        "maqam_name",
        "maqam_status",
        "jins_name",
        "jins_support",
        "support_share",
        "support_margin",
        "readiness_score",
        "status",
        "blockers",
    ]

    def _normalize_pitch_class(self, pitch_class: Optional[int]):

        if pitch_class is None:
            return None

        return int(pitch_class) % 12

    def _pitch_name(self, pitch_class):

        if pitch_class is None:
            return None

        return self.PITCH_CLASS_NAMES.get(pitch_class)

    def _normalize_status(self, status):

        if not status:
            return self.NOT_READY

        return str(status).upper()

    def build_candidate(
        self,
        tonic_pitch_class: Optional[int],
        tonic_status: str,
        maqam_name: str,
        maqam_status: str,
        jins_name: str,
        jins_support: float,
        support_share: float,
        support_margin: float,
        readiness_score: float,
        status: str = "READY",
        blockers: Optional[List[str]] = None,
    ):

        blockers = blockers or []

        pc = self._normalize_pitch_class(tonic_pitch_class)

        candidate = {
            "tonic_pitch_class": pc,
            "tonic_name": self._pitch_name(pc),
            "tonic_status": self._normalize_status(tonic_status),
            "maqam_name": maqam_name,
            "maqam_status": self._normalize_status(maqam_status),
            "jins_name": jins_name,
            "jins_support": float(jins_support),
            "support_share": float(support_share),
            "support_margin": float(support_margin),
            "readiness_score": float(readiness_score),
            "status": self._normalize_status(status),
            "eligible": False,
            "blockers": blockers,
            "decision": {
                "status": "EVIDENCE_ONLY",
                "jins": None,
            },
            "protection": {
                "tonic_modified": False,
                "maqam_modified": False,
                "jins_decision_made": False,
                "source_audio_modified": False,
                "scores_modified": False,
            },
        }

        candidate["eligible"] = self.is_eligible(candidate)

        return candidate

    def validate(self, candidate: Dict[str, Any]):

        missing = []

        for field in self.REQUIRED_FIELDS:

            if field not in candidate:
                missing.append(field)

        valid = len(missing) == 0

        return {
            "valid": valid,
            "missing_fields": missing,
        }

    def is_eligible(self, candidate):

        if candidate["tonic_status"] != self.DECIDED:
            return False

        if candidate["maqam_status"] != self.DECIDED:
            return False

        if candidate["status"] != self.READY:
            return False

        if candidate["jins_support"] <= 0:
            return False

        if candidate["blockers"]:
            return False

        return True