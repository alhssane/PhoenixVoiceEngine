from statistics import mean

from src.analysis.phoneme_mapping_engine import (
    PhonemeMappingEngine,
)

from src.analysis.frame_tracking_engine import (
    FrameTrackingEngine,
)


class VocalSignatureEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        file_path,
    ):

        segments = (
            PhonemeMappingEngine()
            .analyze(file_path)
        )

        frames = (
            FrameTrackingEngine()
            .analyze(file_path)
        )

        results = []

        for segment in segments:

            segment_frames = []

            for frame in frames:

                if (
                    segment["start"]
                    <= frame["time"]
                    <= segment["end"]
                ):

                    segment_frames.append(
                        frame
                    )

            pitches = []

            cents = []

            for frame in segment_frames:

                pitches.append(
                    frame["frequency"]
                )

                cents.append(
                    frame["cents"]
                )

            average_pitch = 0

            average_cents = 0

            if pitches:

                average_pitch = round(
                    mean(pitches),
                    2,
                )

            if cents:

                average_cents = round(
                    mean(cents),
                    2,
                )

            results.append(
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "duration": segment["duration"],
                    "maqam": segment["maqam"],
                    "ornament": segment["ornament"],
                    "notes": segment["notes"],
                    "average_pitch": average_pitch,
                    "average_cents": average_cents,
                }
            )

        return results