from src.maqam.maqam_timeline_engine import (
    MaqamTimelineEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        MaqamTimelineEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_timeline():

    engine = (
        MaqamTimelineEngine()
    )

    timeline = (
        engine.analyze(
            AUDIO_FILE
        )
    )

    print()

    print(
        "Maqam Timeline"
    )

    print(
        "=" * 40
    )

    for item in timeline:

        print(
            f"{item['start']}s"
            f" -> "
            f"{item['end']}s"
            f" | "
            f"{item['maqam']}"
            f" | "
            f"{item['confidence']}%"
        )

    assert (
        len(timeline)
        > 0
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Maqam Timeline Engine V1.0"
    )

    print(
        "=" * 60
    )

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_timeline()

    print(
        "TEST 2: test_timeline - PASS"
    )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()