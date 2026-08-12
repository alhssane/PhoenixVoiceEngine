from typing import Any, Dict, List


class OrnamentExtractionEngine:

    VERSION = "1.0.0"
    FEATURE_VERSION = "1.0.0"
    PATCH_VERSION = "1.0.0"

    ORNAMENT_TYPES = (
        "VIBRATO",
        "PORTAMENTO",
        "MELISMA",
        "GRACE_NOTE",
        "PITCH_BEND",
    )

    def build_ornament(
        self,
        ornament_type: str,
        start_time: float,
        end_time: float,
        confidence: float,
    ) -> Dict[str, Any]:

        ornament_type = str(ornament_type).upper()

        if ornament_type not in self.ORNAMENT_TYPES:
            raise ValueError("Unsupported ornament type.")

        confidence = max(0.0, min(1.0, float(confidence)))

        return {
            "type": ornament_type,
            "start_time": float(start_time),
            "end_time": float(end_time),
            "duration": float(end_time) - float(start_time),
            "confidence": confidence,
        }

    def analyze(
        self,
        ornaments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        total = len(ornaments)

        if total == 0:
            return {
                "status": "NO_ORNAMENTS",
                "count": 0,
                "ornaments": [],
            }

        average_confidence = (
            sum(item["confidence"] for item in ornaments) / total
        )

        return {
            "status": "ORNAMENTS_DETECTED",
            "count": total,
            "average_confidence": round(
                average_confidence,
                6,
            ),
            "ornaments": ornaments,
        }