from src.maqam.arabic_maqam_detector import (
    ArabicMaqamDetector,
)


AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    detector = (
        ArabicMaqamDetector()
    )

    assert (
        detector.VERSION
        == "1.0.0"
    )


def test_detection():

    detector = (
        ArabicMaqamDetector()
    )

    result = detector.detect(
        AUDIO_FILE
    )

    print()

    print(
        "Arabic Maqam Analysis"
    )

    print(
        "=" * 40
    )

    print(
        f"Detected: "
        f"{result['detected_maqam']}"
    )

    print(
        f"Confidence: "
        f"{result['confidence']}%"
    )

    print()

    for maqam, score in (
        result[
            "all_scores"
        ].items()
    ):

        print(
            f"{maqam}: "
            f"{score}%"
        )

    assert (
        "detected_maqam"
        in result
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Arabic Maqam Detector V1.0"
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