from src.analysis.lyric_alignment_engine import (
    LyricAlignmentEngine,
)

from src.analysis.ornament_classification_engine import (
    OrnamentClassificationEngine,
)


class PhonemeMappingEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        file_path,
    ):

        aligned = (
            LyricAlignmentEngine()
            .analyze(file_path)
        )

        ornament_engine = (
            OrnamentClassificationEngine()
        )

        results = []

        for item in aligned:

            notes = item["notes"]

            unique_notes = []

            for note in notes:

                if note not in unique_notes:

                    unique_notes.append(note)

            if len(unique_notes) >= 3:

                ornament = (
                    ornament_engine.classify(
                        unique_notes
                    )
                )

            else:

                ornament = (
                    "NONE"
                )

            results.append(
                {
                    "start": item["start"],
                    "end": item["end"],
                    "duration": item["duration"],
                    "maqam": item["maqam"],
                    "notes": unique_notes,
                    "ornament": ornament,
                }
            )

        return results