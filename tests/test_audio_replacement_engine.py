from src.replacement.audio_replacement_engine import (
    AudioReplacementEngine,
)

WORDS = (
    r"D:\PhoenixVoiceEngine"
    r"\outputs\lyrics"
    r"\fareed_words.json"
)


def run():

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Audio Replacement Engine V1.0"
    )

    print(
        "=" * 60
    )

    result = (
        AudioReplacementEngine()
        .replace(
            WORDS,
            "سعادة",
            "فرح",
        )
    )

    print()

    print(
        "Replacement:"
    )

    print()

    print(
        result["text"]
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()