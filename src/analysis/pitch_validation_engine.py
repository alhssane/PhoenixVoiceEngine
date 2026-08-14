from statistics import mean

from src.analysis.frame_tracking_engine import (
    FrameTrackingEngine,
)


class PitchValidationEngine:

    VERSION = "1.0.0"

    MIN_HZ = 65.0

    MAX_HZ = 1000.0

    def analyze(
        self,
        file_path,
    ):

        frames = (
            FrameTrackingEngine()
            .analyze(file_path)
        )

        valid_frames = []

        rejected_frames = []

        for frame in frames:

            frequency = frame[
                "frequency"
            ]

            if (
                self.MIN_HZ
                <= frequency
                <= self.MAX_HZ
            ):

                valid_frames.append(
                    frame
                )

            else:

                rejected_frames.append(
                    frame
                )

        frequencies = [
            frame["frequency"]
            for frame in valid_frames
        ]

        average_frequency = 0

        if frequencies:

            average_frequency = round(
                mean(frequencies),
                2,
            )

        return {
            "total_frames": len(
                frames
            ),
            "valid_frames": len(
                valid_frames
            ),
            "rejected_frames": len(
                rejected_frames
            ),
            "average_frequency": (
                average_frequency
            ),
            "valid_data": (
                valid_frames
            ),
        }