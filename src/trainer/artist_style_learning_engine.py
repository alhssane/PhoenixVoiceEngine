import json
from pathlib import Path


class ArtistStyleLearningEngine:

    VERSION = "1.0.0"

    def analyze(
        self,
        profile_path,
        embedding_path,
    ):

        profile = json.loads(
            Path(
                profile_path
            ).read_text(
                encoding="utf-8",
            )
        )

        embedding = json.loads(
            Path(
                embedding_path
            ).read_text(
                encoding="utf-8",
            )
        )

        word_count = profile.get(
            "word_count",
            0,
        )

        syllable_count = profile.get(
            "syllable_count",
            0,
        )

        style = {
            "artist": profile.get(
                "artist",
                "unknown",
            ),
            "maqam": profile.get(
                "maqam",
                "unknown",
            ),
            "duration": profile.get(
                "duration",
                0,
            ),
            "word_count": word_count,
            "syllable_count": syllable_count,
            "timbre_centroid": embedding.get(
                "timbre_centroid",
                0,
            ),
            "timbre_bandwidth": embedding.get(
                "timbre_bandwidth",
                0,
            ),
            "energy": embedding.get(
                "energy",
                0,
            ),
            "voice_activity": embedding.get(
                "voice_activity",
                0,
            ),
            "ornament_density": round(
                syllable_count
                / max(
                    word_count,
                    1,
                ),
                2,
            ),
            "style_status": "LEARNED",
        }

        return style

    def save(
        self,
        style,
        output_path,
    ):

        Path(
            output_path
        ).write_text(
            json.dumps(
                style,
                ensure_ascii=False,
                indent=4,
            ),
            encoding="utf-8",
        )