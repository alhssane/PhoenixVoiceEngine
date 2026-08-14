from src.maqam.segmented_pyin_maqam_detector import (
    SegmentedPyinMaqamDetector,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    detector = (
        SegmentedPyinMaqamDetector()
    )

    assert (
        detector.VERSION
        == "3.0.0"
    )


def test_analysis():

    detector = (
        SegmentedPyinMaqamDetector()
    )

    results = detector.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "Segmented PYIN Maqam Timeline"
    )

    print(
        "=" * 40
    )

    for item in results:

        print(
            f"{item['start']}s -> "
            f"{item['end']}s | "
            f"{item['maqam']} | "
            f"{item['confidence']}%"
        )

    assert len(results) > 0


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Segmented PYIN Maqam Detector V3.0"
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