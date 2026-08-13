from typing import Any
from typing import Dict
from typing import List


class VoiceDNAEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    def normalize(
        self,
        value: float,
    ) -> float:

        return max(
            0.0,
            min(
                1.0,
                float(value),
            ),
        )

    def build_profile(
        self,
        timbre: float,
        vibrato: float,
        expression: float,
        articulation: float,
    ) -> Dict[str, Any]:

        profile = {
            "timbre": self.normalize(
                timbre
            ),
            "vibrato": self.normalize(
                vibrato
            ),
            "expression": self.normalize(
                expression
            ),
            "articulation": self.normalize(
                articulation
            ),
        }

        profile["voice_dna_score"] = (
            sum(
                profile.values()
            )
            / len(profile)
        )

        return profile

    def analyze(
        self,
        samples: List[
            Dict[str, float]
        ],
    ) -> Dict[str, Any]:

        if not samples:

            return {
                "status": "EMPTY",
                "profiles": [],
                "average_score": 0.0,
            }

        profiles = []

        for sample in samples:

            profiles.append(
                self.build_profile(
                    sample["timbre"],
                    sample["vibrato"],
                    sample["expression"],
                    sample["articulation"],
                )
            )

        average_score = (
            sum(
                p["voice_dna_score"]
                for p in profiles
            )
            / len(profiles)
        )

        return {
            "status": "READY",
            "profiles": profiles,
            "average_score": average_score,
        }