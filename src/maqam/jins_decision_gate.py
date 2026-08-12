from typing import Any, Dict, List


class JinsDecisionGate:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    MIN_READINESS_SCORE = 0.70
    MIN_SUPPORT_SHARE = 0.50
    MIN_SUPPORT_MARGIN = 0.05

    READY = "READY"
    NOT_READY = "NOT_READY"

    def analyze(self, readiness: Dict[str, Any]):

        candidates = readiness.get(
            "readiness",
            {}
        ).get(
            "candidates",
            []
        )

        candidate_gates = []

        for candidate in candidates:

            blockers = []

            if candidate.get("status") != self.READY:
                blockers.append(
                    "READINESS_NOT_READY"
                )

            if (
                candidate.get(
                    "readiness_score",
                    0.0
                )
                < self.MIN_READINESS_SCORE
            ):
                blockers.append(
                    "READINESS_SCORE_TOO_LOW"
                )

            if (
                candidate.get(
                    "support_share",
                    0.0
                )
                < self.MIN_SUPPORT_SHARE
            ):
                blockers.append(
                    "SUPPORT_SHARE_TOO_LOW"
                )

            if (
                candidate.get(
                    "support_margin",
                    0.0
                )
                < self.MIN_SUPPORT_MARGIN
            ):
                blockers.append(
                    "SUPPORT_MARGIN_TOO_LOW"
                )

            candidate_gate = {
                "jins": candidate.get(
                    "jins_name"
                ),
                "status": (
                    "OPEN"
                    if not blockers
                    else "CLOSED"
                ),
                "decision_allowed": (
                    len(blockers) == 0
                ),
                "blockers": blockers,
            }

            candidate_gates.append(
                candidate_gate
            )

        gate_open = any(
            c["decision_allowed"]
            for c in candidate_gates
        )

        return {
            "version": self.VERSION,
            "feature_version":
                self.FEATURE_VERSION,
            "patch_version":
                self.PATCH_VERSION,
            "gate": {
                "status": (
                    "OPEN"
                    if gate_open
                    else "CLOSED"
                ),
                "decision_allowed":
                    gate_open,
                "abstention_required":
                    not gate_open,
            },
            "candidate_gates":
                candidate_gates,
            "decision": {
                "status":
                    "EVIDENCE_ONLY",
                "jins": None,
            },
            "protection": {
                "tonic_modified":
                    False,
                "maqam_modified":
                    False,
                "jins_decision_made":
                    False,
                "source_audio_modified":
                    False,
            },
        }