from src.analysis.twenty_four_tone_extraction_engine import (
    TwentyFourToneExtractionEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        TwentyFourToneExtractionEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        TwentyFourToneExtractionEngine()
    )

    result = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "24-Tone Distribution"
    )

    print(
        "=" * 40
    )

    for note, value in (
        result.items()
    ):

        print(
            f"{note}: {value}%"
        )

    assert (
        len(result)
        > 0
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "24-Tone Extraction Engine V1.0"
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