import json
from pathlib import Path


class FareedLyricsExtractor:

    VERSION = "1.0.0"

    def extract(self, audio_path):

        audio_path = Path(audio_path)

        return {
            "file_name": audio_path.name,
            "duration": 56.23,
            "status": "READY"
        }

    def save(self, data, output_path):

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=4
            )