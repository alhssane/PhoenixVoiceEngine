from src.maqam.segment_jins_detector import (
    SegmentJinsDetector,
)

SEGMENTS_DIRECTORY = (
    r"D:\PhoenixVoiceEngine\segments"
)


def test_build():

    detector = (
        SegmentJinsDetector()
    )

    assert (
        detector.VERSION
        == "1.0.0"
    )


def test_detection():

    detector = (
        SegmentJinsDetector()
    )

    results = detector.analyze(
        SEGMENTS_DIRECTORY
    )

    print()

    print(
        "Segment Jins Analysis"
    )

    print(
        "=" * 40
    )

    for result in results:

        print(
            f"{result['segment']} | "
            f"{result['jins']} | "
            f"{result['average_pitch']} Hz"
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
        "Segment Jins Detector V1.0"
    )

    print(
        "=" * 60
    )

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_detection()

    print(
        "TEST 2: test_detection - PASS"
    )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()