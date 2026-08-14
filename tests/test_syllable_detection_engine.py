from src.analysis.syllable_detection_engine import (
    SyllableDetectionEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        SyllableDetectionEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    results = (
        SyllableDetectionEngine()
        .analyze(
            AUDIO_FILE
        )
    )

    print()

    print(
        "Syllable Analysis"
    )

    print(
        "=" * 40
    )

    print(
        f"Detected syllables: {len(results)}"
    )

    print()

    for syllable in results[:20]:

        print(
            f"{syllable['start']}s -> "
            f"{syllable['end']}s | "
            f"{syllable['duration']}s"
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
        "Syllable Detection Engine V1.0"
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