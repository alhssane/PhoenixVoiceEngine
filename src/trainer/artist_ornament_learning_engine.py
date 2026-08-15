import json


class ArtistOrnamentLearningEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        profile_file,
    ):

        with open(
            profile_file,
            "r",
            encoding="utf-8",
        ) as file:

            profile = json.load(
                file
            )

        syllables = profile[
            "syllable_count"
        ]

        words = profile[
            "word_count"
        ]

        density = round(
            syllables
            / words,
            2,
        )

        return {
            "ornament_density": density
        }