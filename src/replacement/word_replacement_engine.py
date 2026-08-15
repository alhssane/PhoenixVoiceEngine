import json
from pathlib import Path


class WordReplacementEngine:

    VERSION = "1.0.0"

    def replace(
        self,
        original_word,
        replacement_word,
    ):

        timeline_path = Path(
            r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_words.json"
        )

        with open(
            timeline_path,
            "r",
            encoding="utf-8",
        ) as file:

            words = json.load(
                file
            )

        matches = [

            item

            for item in words

            if item["word"]
            == original_word

        ]

        if not matches:

            return {

                "status": "WORD_NOT_FOUND"

            }

        target = matches[0]

        return {

            "original_word":
            original_word,

            "replacement_word":
            replacement_word,

            "start":
            target["start"],

            "end":
            target["end"],

            "duration":
            target["duration"],

            "status":
            "READY",

        }