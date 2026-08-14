from src.analysis.melisma_detection_engine import (
    MelismaDetectionEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        MelismaDetectionEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        MelismaDetectionEngine()
    )

    results = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "Melisma Analysis"
    )

    print(
        "=" * 40
    )

    print(
        f"Detected melismas: {len(results)}"
    )

    print()

    for index, melisma in enumerate(
        results[:10]
    ):

        start = round(
            melisma[0]["time"],
            2,
        )

        end = round(
            melisma[-1]["time"],
            2,
        )

        notes = [
            item["note"]
            for item in melisma
        ]

        print(
            f"{index+1}. "
            f"{start}s -> "
            f"{end}s | "
            f"{notes}"
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
        "Melisma Detection Engine V1.0"
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