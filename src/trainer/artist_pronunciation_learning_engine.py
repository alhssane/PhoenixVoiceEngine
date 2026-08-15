import json
from pathlib import Path


class ArtistPronunciationLearningEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        words_file,
    ):

        with open(
            words_file,
            "r",
            encoding="utf-8",
        ) as file:

            words = json.load(
                file
            )

        phonemes = {}

        for item in words:

            word = item["word"]

            duration = item[
                "duration"
            ]

            letters = list(
                word
            )

            if not letters:

                continue

            letter_duration = round(
                duration
                / len(
                    letters
                ),
                3,
            )

            for letter in letters:

                if (
                    letter
                    not in phonemes
                ):

                    phonemes[
                        letter
                    ] = []

                phonemes[
                    letter
                ].append(
                    letter_duration
                )

        model = {}

        for letter, values in (
            phonemes.items()
        ):

            model[
                letter
            ] = round(
                sum(values)
                / len(values),
                3,
            )

        return model