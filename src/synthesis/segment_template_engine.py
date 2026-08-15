import json
from pathlib import Path

import soundfile as sf


class SegmentTemplateEngine:

    VERSION = "1.0.0"

    def build(
        self,
        audio_path,
        blueprint_path,
    ):

        data, sample_rate = sf.read(
            audio_path
        )

        blueprint = json.loads(
            Path(
                blueprint_path
            ).read_text(
                encoding="utf-8"
            )
        )

        return {
            "artist": blueprint["artist"],
            "replacement_word": blueprint[
                "replacement_word"
            ],
            "sample_rate": sample_rate,
            "samples": len(data),
            "duration": blueprint[
                "duration"
            ],
            "maqam": blueprint[
                "maqam"
            ],
            "status": "READY_FOR_GENERATION",
        }