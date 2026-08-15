from __future__ import annotations

import json
from pathlib import Path


class AudioReplacementEngine:

    VERSION = "1.0.0"

    def replace(
        self,
        words_path,
        original_word,
        replacement_word,
    ):

        words = json.loads(
            Path(
                words_path
            ).read_text(
                encoding="utf-8"
            )
        )

        replaced = False

        for item in words:

            if (
                item["word"]
                == original_word
                and not replaced
            ):

                item["replacement"] = (
                    replacement_word
                )

                replaced = True

            else:

                item["replacement"] = (
                    item["word"]
                )

        final_text = " ".join(
            item["replacement"]
            for item in words
        )

        return {
            "replaced": replaced,
            "text": final_text,
            "words": words,
        }