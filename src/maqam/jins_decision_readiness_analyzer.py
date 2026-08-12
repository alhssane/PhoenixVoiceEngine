from typing import Dict, List, Optional, Any


class JinsDecisionReadinessAnalyzer:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    MIN_READINESS_SCORE = 0.70
    MIN_SUPPORT = 0.10
    MIN_SUPPORT_MARGIN = 0.05

    READY = "READY"
    NOT_READY = "NOT_READY"

    DECIDED = "DECIDED"
    ABSTAIN = "ABSTAIN"

    def _normalize_status(self, value):

        if not value:
            return self.NOT_READY

        return str(value).upper()

    def analyze(
        self,
        candidates: Optional[List[Dict[str, Any]]] = None
    ):

        candidates = candidates or []

        ranked = []

        for candidate in candidates:

            blockers = []

            if candidate.get("tonic_status") != self.DECIDED:
                blockers.append("TONIC_NOT_DECIDED")

            if candidate.get("maqam_status") != self.DECIDED:
                blockers.append("MAQAM_NOT_DECIDED")

            if candidate.get(
                "jins_support",
                0.0
            ) < self.MIN_SUPPORT:
                blockers.append("LOW_JINS_SUPPORT")

            if candidate.get(
                "support_margin",
                0.0
            ) < self.MIN_SUPPORT_MARGIN:
                blockers.append("LOW_SUPPORT_MARGIN")

            readiness_score = float(
                candidate.get(
                    "readiness_score",
                    0.0
                )
            )

            status = self.READY

            if (
                readiness_score < self.MIN_READINESS_SCORE
                or blockers
            ):
                status = self.NOT_READY

            ranked.append(
                {
                    **candidate,
                    "status": status,
                    "blockers": blockers,
                }
            )

        ranked.sort(
            key=lambda x: x.get(
                "readiness_score",
                0.0
            ),
            reverse=True
        )

        global_status = self.NOT_READY

        if ranked and ranked[0]["status"] == self.READY:
            global_status = self.READY

        return {
            "version": self.VERSION,
            "feature_version": self.FEATURE_VERSION,
            "patch_version": self.PATCH_VERSION,
            "readiness": {
                "status": global_status,
                "candidates": ranked,
            },
            "decision": {
                "status": "EVIDENCE_ONLY",
                "jins": None,
            },
            "protection": {
                "tonic_modified": False,
                "maqam_modified": False,
                "jins_decision_made": False,
                "scores_modified": False,
                "source_audio_modified": False,
            },
        }