from src.analysis.pitch_stability_engine import (
    PitchStabilityEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        PitchStabilityEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        PitchStabilityEngine()
    )

    results = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "Pitch Stability Analysis"
    )

    print(
        "=" * 40
    )

    for result in results[:20]:

        print(
            f"{result['status']} | "
            f"Average: {result['average']} | "
            f"Deviation: {result['deviation']}"
        )

    assert (
        len(results)
        > 0
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Pitch Stability Engine V1.0"
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