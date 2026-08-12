from typing import Any, Dict, List


class JinsDecisionEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    MIN_READINESS_SCORE = 0.70
    MIN_SUPPORT_SHARE = 0.50
    MIN_SUPPORT_MARGIN = 0.05

    def _extract_gate(self, gate_data):

        return gate_data.get("gate", {})

    def _extract_candidates(self, readiness_data):

        return (
            readiness_data
            .get("readiness", {})
            .get("candidates", [])
        )

    def _valid_candidates(self, candidates):

        valid = []

        for candidate in candidates:

            if candidate.get("status") != "READY":
                continue

            if (
                candidate.get(
                    "readiness_score",
                    0.0
                )
                < self.MIN_READINESS_SCORE
            ):
                continue

            if (
                candidate.get(
                    "support_share",
                    0.0
                )
                < self.MIN_SUPPORT_SHARE
            ):
                continue

            if (
                candidate.get(
                    "support_margin",
                    0.0
                )
                < self.MIN_SUPPORT_MARGIN
            ):
                continue

            if candidate.get("blockers"):
                continue

            valid.append(candidate)

        return valid

    def analyze(
        self,
        gate_data: Dict[str, Any],
        readiness_data: Dict[str, Any]
    ):

        gate = self._extract_gate(
            gate_data
        )

        candidates = (
            self._extract_candidates(
                readiness_data
            )
        )

        ranking = sorted(
            candidates,
            key=lambda x: x.get(
                "readiness_score",
                0.0
            ),
            reverse=True
        )

        if not gate.get(
            "decision_allowed",
            False
        ):

            return {
                "version": self.VERSION,
                "feature_version":
                    self.FEATURE_VERSION,
                "patch_version":
                    self.PATCH_VERSION,
                "decision": {
                    "status":
                        "ABSTAIN",
                    "jins":
                        None,
                    "reason": [
                        "GATE_CLOSED"
                    ],
                },
                "ranking": {
                    "candidates":
                        ranking
                },
                "protection": {
                    "tonic_modified":
                        False,
                    "maqam_modified":
                        False,
                    "jins_decision_made":
                        False,
                    "gate_bypassed":
                        False,
                },
            }

        valid = self._valid_candidates(
            ranking
        )

        if not valid:

            return {
                "version": self.VERSION,
                "feature_version":
                    self.FEATURE_VERSION,
                "patch_version":
                    self.PATCH_VERSION,
                "decision": {
                    "status":
                        "ABSTAIN",
                    "jins":
                        None,
                    "reason": [
                        "NO_VALID_CANDIDATE"
                    ],
                },
                "ranking": {
                    "candidates":
                        ranking
                },
                "protection": {
                    "tonic_modified":
                        False,
                    "maqam_modified":
                        False,
                    "jins_decision_made":
                        False,
                    "gate_bypassed":
                        False,
                },
            }

        selected = valid[0]

        return {
            "version": self.VERSION,
            "feature_version":
                self.FEATURE_VERSION,
            "patch_version":
                self.PATCH_VERSION,
            "decision": {
                "status":
                    "DECIDED",
                "jins":
                    selected.get(
                        "jins_name"
                    ),
                "confidence":
                    selected.get(
                        "readiness_score"
                    ),
            },
            "ranking": {
                "candidates":
                    ranking
            },
            "protection": {
                "tonic_modified":
                    False,
                "maqam_modified":
                    False,
                "jins_decision_made":
                    True,
                "gate_bypassed":
                    False,
            },
        }