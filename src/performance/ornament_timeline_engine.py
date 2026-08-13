from typing import Any
from typing import Dict
from typing import List


class OrnamentTimelineEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    def sort_ornaments(
        self,
        ornaments: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        return sorted(
            ornaments,
            key=lambda x: x["start_time"],
        )

    def build_timeline(
        self,
        ornaments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if not ornaments:

            return {
                "status": "EMPTY",
                "events": [],
                "count": 0,
            }

        ordered = self.sort_ornaments(
            ornaments,
        )

        events = []

        for index, ornament in enumerate(
            ordered,
            start=1,
        ):

            events.append(
                {
                    "id": index,
                    "type": ornament["type"],
                    "start_time": ornament["start_time"],
                    "end_time": ornament["end_time"],
                    "duration": ornament["duration"],
                    "confidence": ornament["confidence"],
                }
            )

        return {
            "status": "READY",
            "count": len(events),
            "events": events,
        }