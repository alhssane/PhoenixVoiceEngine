from pathlib import Path

from src.trainer.artist_training_engine import (
    ArtistTrainingEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)

WORDS_FILE = (
    r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_words.json"
)

OUTPUT_FILE = (
    r"D:\PhoenixVoiceEngine\workspace\artist_profiles\fareed_profile.json"
)


def run():

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Artist Training Engine V1.0"
    )

    print(
        "=" * 60
    )

    result = (
        ArtistTrainingEngine()
        .train(
            AUDIO_FILE,
            WORDS_FILE,
            OUTPUT_FILE,
        )
    )

    print()

    print(
        f"Artist: "
        f"{result['artist']}"
    )

    print(
        f"Duration: "
        f"{result['duration']} seconds"
    )

    print(
        f"Words: "
        f"{result['word_count']}"
    )

    print(
        f"Syllables: "
        f"{result['syllable_count']}"
    )

    print(
        f"Maqam: "
        f"{result['maqam']}"
    )

    print()

    print(
        f"Saved: "
        f"{OUTPUT_FILE}"
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()