from src.analysis.frame_tracking_engine import (
    FrameTrackingEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        FrameTrackingEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        FrameTrackingEngine()
    )

    results = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "Frame Tracking"
    )

    print(
        "=" * 40
    )

    print(
        f"Total frames: {len(results)}"
    )

    print()

    for item in results[:25]:

        print(
            f"{item['time']}s | "
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
        "Frame Tracking Engine V1.0"
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