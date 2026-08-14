from statistics import mean

from src.analysis.phoneme_mapping_engine import (
    PhonemeMappingEngine,
)

from src.analysis.pitch_validation_engine import (
    PitchValidationEngine,
)


class CleanVocalSignatureEngine:

    VERSION = "2.0.0"

    def analyze(
        self,
        file_path,
    ):

        segments = (
            PhonemeMappingEngine()
            .analyze(file_path)
        )

        pitch_data = (
            PitchValidationEngine()
            .analyze(file_path)
        )

        frames = (
            pitch_data[
                "valid_data"
            ]
        )

        results = []

        for segment in segments:

            matched_frames = []

            for frame in frames:

                if (
                    segment["start"]
                    <= frame["time"]
                    <= segment["end"]
                ):

                    matched_frames.append(
                        frame
                    )

            frequencies = [
                frame["frequency"]
                for frame in matched_frames
            ]

            average_pitch = 0

            if frequencies:

                average_pitch = round(
                    mean(
                        frequencies
                    ),
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
                    "note_count": len(
                        segment["notes"]
                    ),
                }
            )

        return results