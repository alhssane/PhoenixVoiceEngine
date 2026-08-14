from src.analysis.pitch_validation_engine import (
    PitchValidationEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        PitchValidationEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    results = (
        PitchValidationEngine()
        .analyze(
            AUDIO_FILE
        )
    )

    print()

    print(
        "Pitch Validation"
    )

    print(
        "=" * 40
    )

    print(
        f"Total frames: "
        f"{results['total_frames']}"
    )

    print(
        f"Valid frames: "
        f"{results['valid_frames']}"
    )

    print(
        f"Rejected frames: "
        f"{results['rejected_frames']}"
    )

    print(
        f"Average frequency: "
        f"{results['average_frequency']} Hz"
    )

    assert (
        results[
            "valid_frames"
        ]
        > 0
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Pitch Validation Engine V1.0"
    )

    print(
        "=" * 60
    )

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_analysis()

    print(
        "TEST 2: test_analysis - PASS"
    )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()