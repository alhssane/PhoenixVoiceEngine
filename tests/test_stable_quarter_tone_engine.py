from src.analysis.stable_quarter_tone_engine import (
    StableQuarterToneEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        StableQuarterToneEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        StableQuarterToneEngine()
    )

    results = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "Stable Quarter-Tone Analysis"
    )

    print(
        "=" * 40
    )

    for result in results:

        print(
            f"{result['note']} | "
            f"{result['occurrences']} occurrences | "
            f"{result['duration']}s | "
            f"{result['average_cents']} cents"
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
        "Stable Quarter-Tone Engine V1.0"
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