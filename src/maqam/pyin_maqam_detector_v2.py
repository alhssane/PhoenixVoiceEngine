from src.analysis.pyin_note_extractor import (
    PyinNoteExtractor,
)

from src.analysis.pyin_quarter_tone_distribution import (
    PyinQuarterToneDistribution,
)


class PyinMaqamDetector:

    VERSION = "2.0.0"

    MAQAMS = {
        "rast": [
            "C",
            "E(+50)",
            "G",
        ],
        "bayati": [
            "D(-50)",
            "G",
            "A",
        ],
        "bayati_husayni": [
            "D(-50)",
            "A(-50)",
            "G",
        ],
        "sikah": [
            "E(-50)",
            "B(-50)",
        ],
        "sikah_hazzam": [
            "E(-50)",
            "B(-50)",
            "F",
        ],
        "hijaz": [
            "D",
            "D#",
            "G",
        ],
        "hijaz_husayni": [
            "D",
            "A(-50)",
            "G",
        ],
    }

    def analyze(
        self,
        file_path,
    ):

        notes = (
            PyinNoteExtractor()
            .analyze(
                file_path
            )
        )

        quarter_tones = (
            PyinQuarterToneDistribution()
            .analyze(
                file_path
            )
        )

        scores = {}

        for maqam, pattern in (
            self.MAQAMS.items()
        ):

            score = 0

            for note in pattern:

                if note in notes:

                    score += notes[
                        note
                    ]

                if note in quarter_tones:

                    score += (
                        quarter_tones[
                            note
                        ]
                    )

            scores[
                maqam
            ] = round(
                score,
                2,
            )

        total = sum(
            scores.values()
        )

        if total == 0:

            return scores

        normalized = {}

        for maqam, score in (
            scores.items()
        ):

            normalized[
                maqam
            ] = round(
                (
                    score
                    / total
                )
                * 100,
                2,
            )

        return normalized