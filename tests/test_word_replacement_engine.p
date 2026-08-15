from src.replacement.word_replacement_engine import (
    WordReplacementEngine,
)


def run():

    result = (

        WordReplacementEngine()

        .replace(

            "سعادة",

            "فرح",

        )

    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Word Replacement Engine V1.0"
    )

    print(
        "=" * 60
    )

    print()

    print(
        result
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()