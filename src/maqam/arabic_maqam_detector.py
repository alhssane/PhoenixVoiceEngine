from src.maqam.quarter_tone_profile_engine import (
    QuarterToneProfileEngine,
)


class ArabicMaqamDetector:

    VERSION = "1.0.0"

    MAQAM_PATTERNS = {
        "bayati": {
            "notes": [
                "D",
                "E",
                "F",
                "G",
            ],
        },
        "sikah": {
            "notes": [
                "E",
                "F",
                "G",
                "B",
            ],
        },
        "rast": {
            "notes": [
                "C",
                "E",
                "F",
                "G",
            ],
        },
        "hijaz": {
            "notes": [
                "D",
                "D#",
                "F#",
                "G",
            ],
        },
    }

    def detect(
        self,
        file_path,
    ):

        profile = (
            QuarterToneProfileEngine()
            .build_profile(
                file_path
            )
        )

        scores = {}

        for maqam, data in (
            self.MAQAM_PATTERNS.items()
        ):

            score = 0

            for note in data[
                "notes"
            ]:

                score += profile.get(
                    note,
                    0,
                )

            scores[
                maqam
            ] = round(
                score,
                2,
            )

        detected = max(
            scores,
            key=scores.get,
        )

        return {
            "detected_maqam": detected,
            "confidence": scores[
                detected
            ],
            "all_scores": scores,
        }