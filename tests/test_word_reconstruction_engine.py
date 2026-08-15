from src.synthesis.word_reconstruction_engine import (
    WordReconstructionEngine,
)


def run():

    result = (
        WordReconstructionEngine()
        .analyze(
            r"D:\PhoenixVoiceEngine\workspace\phoneme_segments",
            "فرح",
            0.96,
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Word Reconstruction Engine V1.0"
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