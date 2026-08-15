import json
from pathlib import Path


class ReplacementBlueprintEngine:

    VERSION = "1.0.0"

    def build(
        self,
        artist_profile_path,
        original_word,
        replacement_word,
        start_time,
        end_time,
    ):

        profile = json.loads(
            Path(
                artist_profile_path
            ).read_text(
                encoding="utf-8"
            )
        )

        blueprint = {
            "artist": profile["artist"],
            "maqam": profile["maqam"],
            "original_word": original_word,
            "replacement_word": replacement_word,
            "start_time": start_time,
            "end_time": end_time,
            "duration": round(
                end_time - start_time,
                2,
            ),
            "voice_profile": {
                "timbre": 0.9,
                "vibrato": 0.85,
                "expression": 0.95,
                "articulation": 0.92,
            },
            "status": "READY",
        }

        return blueprint