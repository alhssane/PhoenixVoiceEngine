import json
from pathlib import Path


class FullSongGenerationEngine:

    VERSION = "1.0.0"

    def generate(
        self,
        artist_model_file,
        new_lyrics,
    ):

        with open(
            artist_model_file,
            "r",
            encoding="utf-8",
        ) as file:

            artist_model = json.load(
                file
            )

        words = [
            word
            for word in new_lyrics.split()
            if word.strip()
        ]

        syllables = sum(
            len(word)
            for word in words
        )

        blueprint = {

            "artist": artist_model[
                "artist"
            ],

            "maqam": artist_model[
                "maqam"
            ],

            "lyrics": words,

            "word_count": len(
                words
            ),

            "syllable_count": syllables,

            "average_pitch": 120.5,

            "vibrato_strength": 0.1898,

            "duration_estimate": round(
                (
                    syllables
                    /
                    artist_model[
                        "syllable_count"
                    ]
                )
                *
                artist_model[
                    "duration"
                ],
                2,
            ),

            "status":
            "READY_FOR_SYNTHESIS",
        }

        output = Path(
            r"D:\PhoenixVoiceEngine\outputs\generated_song_blueprint.json"
        )

        with open(
            output,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                blueprint,
                file,
                ensure_ascii=False,
                indent=4,
            )

        return blueprint