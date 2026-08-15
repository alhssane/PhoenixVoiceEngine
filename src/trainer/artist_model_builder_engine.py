import json


class ArtistModelBuilderEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        profile_file,
        embedding_file,
        pronunciation_model,
        melody_model,
        ornament_model,
    ):

        with open(
            profile_file,
            "r",
            encoding="utf-8",
        ) as file:

            profile = json.load(
                file
            )

        with open(
            embedding_file,
            "r",
            encoding="utf-8",
        ) as file:

            embedding = json.load(
                file
            )

        return {
            "artist": profile[
                "artist"
            ],
            "duration": profile[
                "duration"
            ],
            "word_count": profile[
                "word_count"
            ],
            "syllable_count": profile[
                "syllable_count"
            ],
            "maqam": profile[
                "maqam"
            ],
            "voice_embedding": embedding,
            "pronunciation_model": pronunciation_model,
            "melody_model": melody_model,
            "ornament_model": ornament_model,
            "status": "TRAINED",
        }