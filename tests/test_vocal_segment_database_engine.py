from pathlib import Path

from src.synthesis.vocal_segment_database_engine import (
    VocalSegmentDatabaseEngine,
)


AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)

WORDS_FILE = (
    r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_words.json"
)

OUTPUT_DIRECTORY = (
    r"D:\PhoenixVoiceEngine\workspace\vocal_segments"
)


def run():

    segments = (
        VocalSegmentDatabaseEngine()
        .analyze(
            AUDIO_FILE,
            WORDS_FILE,
            OUTPUT_DIRECTORY,
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Vocal Segment Database V1.0"
    )

    print(
        "=" * 60
    )

    print()

    print(
        f"Segments: {len(segments)}"
    )

    print()

    print(
        segments[:10]
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()