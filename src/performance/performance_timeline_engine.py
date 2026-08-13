from typing import Any, Dict, List


class PerformanceTimelineEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    def sort_segments(
        self,
        segments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        return sorted(
            segments,
            key=lambda x: x["start_time"],
        )

    def build_timeline(
        self,
        profiles: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if not profiles:

            return {
                "status": "EMPTY",
                "count": 0,
                "segments": [],
            }

        ordered = self.sort_segments(
            profiles,
        )

        segments = []

        for index, profile in enumerate(
            ordered,
            start=1,
        ):

            segment = {
                "id": index,
                "start_time": profile["start_time"],
                "end_time": profile["end_time"],
                "duration": (
                    profile["end_time"]
                    - profile["start_time"]
                ),
                "dynamics": profile["dynamics"],
                "energy": profile["energy"],
                "expression": profile["expression"],
                "average_score": profile["average_score"],
            }

            segments.append(segment)

        return {
            "status": "READY",
            "count": len(segments),
            "segments": segments,
        }