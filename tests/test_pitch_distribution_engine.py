from src.analysis.pitch_distribution_engine import (
    PitchDistributionEngine,
)


AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        PitchDistributionEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_distribution():

    engine = (
        PitchDistributionEngine()
    )

    distribution = (
        engine.analyze(
            AUDIO_FILE
        )
    )

    print()

    print(
        "Pitch Distribution"
    )

    print(
        "=" * 40
    )

    for note, value in sorted(
        distribution.items()
    ):

        print(
            f"{note}: "
            f"{value}%"
        )

    assert (
        len(
            distribution
        )
        == 12
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Pitch Distribution Engine V1.0"
    )

    print(
        "=" * 60
    )

    test_build()

    print(
        "TEST 1: "
        "test_build - PASS"
    )

    test_distribution()

    print()

    print(
        "TEST 2: "
        "test_distribution - PASS"
    )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()