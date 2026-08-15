import json
from pathlib import Path


class NeuralSingingSynthesisEngine:

    VERSION = "1.0.0"

    def generate(
        self,
        lyrics,
        artist,
    ):

        words = lyrics.split()

        song = {

            "artist": artist,

            "words": words,

            "segments_found": 0,

            "segments_missing": 0,

            "status": "BLUEPRINT_CREATED",
        }

        database = Path(
            r"D:\PhoenixVoiceEngine\workspace\vocal_segments"
        )

        existing_words = []

        for file in database.glob("*.wav"):

            existing_words.append(
                file.stem.split(
                    "_",
                    1,
                )[1]
            )

        for word in words:

            if word in existing_words:

                song["segments_found"] += 1

            else:

                song["segments_missing"] += 1

        output = Path(
            r"D:\PhoenixVoiceEngine\workspace\generated_songs\generated_song.json"
        )

        with open(
            output,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                song,
                file,
                ensure_ascii=False,
                indent=4,
            )

        return song