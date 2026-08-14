from src.analysis.pyin_quarter_tone_detector import (
    PyinQuarterToneDetector,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    detector = (
        PyinQuarterToneDetector()
    )

    assert (
        detector.VERSION
        == "1.0.0"
    )


def test_analysis():

    detector = (
        PyinQuarterToneDetector()
    )

    results = detector.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "PYIN Quarter-Tone Analysis"
    )

    print(
        "=" * 40
    )

    print(
        f"Detected samples: {len(results)}"
    )

    print()

    for item in results[:30]:

        print(
            f"{item['note']} | "
            f"{item['frequency']} Hz | "
            f"{item['cents']} cents"
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
        "PYIN Quarter-Tone Detector V1.0"
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