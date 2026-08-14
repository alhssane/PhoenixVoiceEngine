from pathlib import Path

from src.maqam.arabic_maqam_detector import (
    ArabicMaqamDetector,
)


class SegmentMaqamDetector:

    VERSION = "1.0.0"

    def analyze(
        self,
        segments_directory,
    ):

        detector = (
            ArabicMaqamDetector()
        )

        results = []

        directory = Path(
            segments_directory
        )

        for segment in sorted(
            directory.glob(
                "*.wav"
            )
        ):

            result = detector.detect(
                str(segment)
            )

            results.append(
                {
                    "segment": segment.name,
                    "maqam": result[
                        "detected_maqam"
                    ],
                    "confidence": result[
                        "confidence"
                    ],
                }
            )

        return results