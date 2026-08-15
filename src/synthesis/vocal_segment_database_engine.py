import json
from pathlib import Path

import librosa
import soundfile as sf


class VocalSegmentDatabaseEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        audio_file,
        words_file,
        output_directory,
    ):

        audio, sample_rate = librosa.load(
            audio_file,
            sr=None,
        )

        with open(
            words_file,
            "r",
            encoding="utf-8",
        ) as file:

            words = json.load(
                file
            )

        output_path = Path(
            output_directory
        )

        output_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        database = []

        for index, item in enumerate(
            words
        ):

            start_sample = int(
                item["start"]
                * sample_rate
            )

            end_sample = int(
                item["end"]
                * sample_rate
            )

            segment = audio[
                start_sample:end_sample
            ]

            filename = (
                f"{index:03d}_"
                f"{item['word']}.wav"
            )

            segment_path = (
                output_path
                / filename
            )

            sf.write(
                segment_path,
                segment,
                sample_rate,
            )

            database.append(
                {
                    "word": item["word"],
                    "start": item["start"],
                    "end": item["end"],
                    "file": str(
                        segment_path
                    ),
                }
            )

        return database