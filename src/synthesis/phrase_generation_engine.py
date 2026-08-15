from pathlib import Path
import json


class PhraseGenerationEngine:

    VERSION = "1.0.0"

    def load_blueprint(
        self,
        blueprint_path,
    ):

        with open(
            blueprint_path,
            encoding="utf-8",
        ) as file:

            return json.load(
                file
            )

    def split_into_phonetic_units(
        self,
        text,
    ):

        units = []

        for character in text:

            if character.strip():

                units.append(
                    character
                )

        return units

    def build(
        self,
        blueprint_path,
    ):

        blueprint = (
            self.load_blueprint(
                blueprint_path
            )
        )

        replacement = (
            blueprint[
                "replacement_word"
            ]
        )

        phonetic_units = (
            self.split_into_phonetic_units(
                replacement
            )
        )

        return {
            "artist": blueprint[
                "artist"
            ],
            "word": replacement,
            "phonemes": phonetic_units,
            "duration": blueprint[
                "duration"
            ],
            "maqam": blueprint[
                "maqam"
            ],
            "voice_profile": blueprint[
                "voice_profile"
            ],
            "status": (
                "PHONEMES_GENERATED"
            ),
        }