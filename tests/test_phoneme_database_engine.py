from src.synthesis.phoneme_database_engine import (
    PhonemeDatabaseEngine,
)


def run():

    database = (
        PhonemeDatabaseEngine()
        .analyze(
            r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav",
            r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_words.json",
            r"D:\PhoenixVoiceEngine\workspace\phoneme_segments",
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Phoneme Database Engine V1.0"
    )

    print(
        "=" * 60
    )

    print()

    print(
        f"Phonemes extracted: {len(database)}"
    )

    print()

    for item in database[:20]:

        print(
            item
        )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()