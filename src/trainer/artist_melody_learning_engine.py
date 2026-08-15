import json


class ArtistMelodyLearningEngine:

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

        return {
            "maqam": profile[
                "maqam"
            ],
            "notes": profile[
                "note_distribution"
            ],
        }