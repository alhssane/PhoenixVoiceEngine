import librosa

from src.maqam.arabic_maqam_detector import (
    ArabicMaqamDetector,
)


class MaqamTimelineEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        file_path,
        segment_duration=5,
    ):

        audio, sample_rate = librosa.load(
            file_path,
            sr=None,
            mono=True,
        )

        duration = (
            len(audio)
            / sample_rate
        )

        segments = []

        detector = (
            ArabicMaqamDetector()
        )

        start = 0

        while start < duration:

            end = min(
                start
                + segment_duration,
                duration,
            )

            result = detector.detect(
                file_path
            )

            segments.append(
                {
                    "start": round(
                        start,
                        2,
                    ),
                    "end": round(
                        end,
                        2,
                    ),
                    "maqam": result[
                        "detected_maqam"
                    ],
                    "confidence": result[
                        "confidence"
                    ],
                }
            )

            start += (
                segment_duration
            )

        return segments