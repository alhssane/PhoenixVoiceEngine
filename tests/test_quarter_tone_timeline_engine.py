from src.analysis.quarter_tone_timeline_engine import (
    QuarterToneTimelineEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        QuarterToneTimelineEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        QuarterToneTimelineEngine()
    )

    results = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "Quarter-Tone Timeline"
    )

    print(
        "=" * 40
    )

    for result in results[
        :30
    ]:

        print(
            f"{result['time']}s | "
            f"{result['note']} | "
            f"{result['cents']} cents"
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
        "Quarter-Tone Timeline Engine V1.0"
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