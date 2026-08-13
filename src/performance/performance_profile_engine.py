from typing import Any, Dict, List


class PerformanceProfileEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    def normalize(self, value: float) -> float:

        return max(0.0, min(1.0, float(value)))

    def build_profile(
        self,
        dynamics: float,
        energy: float,
        breath: float,
        sustain: float,
        attack: float,
        release: float,
        expression: float,
    ) -> Dict[str, Any]:

        profile = {
            "dynamics": self.normalize(dynamics),
            "energy": self.normalize(energy),
            "breath": self.normalize(breath),
            "sustain": self.normalize(sustain),
            "attack": self.normalize(attack),
            "release": self.normalize(release),
            "expression": self.normalize(expression),
        }

        profile["average_score"] = round(
            sum(profile.values()) / len(profile),
            6,
        )

        return profile

    def analyze(
        self,
        profiles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if not profiles:

            return {
                "status": "NO_PROFILE",
                "profile_count": 0,
                "profiles": [],
            }

        average = sum(
            profile["average_score"]
            for profile in profiles
        ) / len(profiles)

        return {
            "status": "PROFILE_READY",
            "profile_count": len(profiles),
            "overall_score": round(
                average,
                6,
            ),
            "profiles": profiles,
        }