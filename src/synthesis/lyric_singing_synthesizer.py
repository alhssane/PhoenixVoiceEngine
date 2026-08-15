from __future__ import annotations

import json
from pathlib import Path


class LyricSingingSynthesizer:

    VERSION = "1.0.0"

    def synthesize(
        self,
        profile_path,
        original_word,
        replacement_word,
        duration,
    ):

        profile = json.loads(
            Path(
                profile_path
            ).read_text(
                encoding="utf-8"
            )
        )

        result = {
            "artist": profile[
                "artist"
            ],
            "maqam": profile[
                "maqam"
            ],
            "original_word": (
                original_word
            ),
            "replacement_word": (
                replacement_word
            ),
            "duration": duration,
            "voice_profile": profile[
                "voice_profile"
            ],
            "status": (
                "READY_FOR_SYNTHESIS"
            ),
        }

        return result