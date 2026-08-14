from src.maqam.pyin_maqam_detector_v2 import (
    PyinMaqamDetector,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    detector = (
        PyinMaqamDetector()
    )

    assert (
        detector.VERSION
        == "2.0.0"
    )


def test_analysis():

    detector = (
        PyinMaqamDetector()
    )

    results = detector.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "PYIN Arabic Maqam Analysis"
    )

    print(
        "=" * 40
    )

    for maqam, score in sorted(
        results.items(),
        key=lambda x: x[1],
        reverse=True,
    ):

        print(
            f"{maqam}: {score}%"
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
        "PYIN Arabic Maqam Detector V2.0"
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