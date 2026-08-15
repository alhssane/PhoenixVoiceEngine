import json
from pathlib import Path

import librosa
import soundfile as sf


class PhonemeDatabaseEngine:

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

        phoneme_database = []

        counter = 0

        for item in words:

            word = item["word"]

            letters = [
                letter
                for letter in word
                if letter.strip()
            ]

            if not letters:

                continue

            duration = (
                item["end"]
                - item["start"]
            )

            part_duration = (
                duration
                / len(
                    letters
                )
            )

            for index, letter in enumerate(
                letters
            ):

                start = (
                    item["start"]
                    + (
                        index
                        * part_duration
                    )
                )

                end = (
                    start
                    + part_duration
                )

                start_sample = int(
                    start
                    * sample_rate
                )

                end_sample = int(
                    end
                    * sample_rate
                )

                segment = audio[
                    start_sample:end_sample
                ]

                filename = (
                    f"{counter:04d}_"
                    f"{letter}.wav"
                )

                file_path = (
                    output_path
                    / filename
                )

                sf.write(
                    file_path,
                    segment,
                    sample_rate,
                )

                phoneme_database.append(
                    {
                        "phoneme": letter,
                        "file": str(
                            file_path
                        ),
                    }
                )

                counter += 1

        return phoneme_database