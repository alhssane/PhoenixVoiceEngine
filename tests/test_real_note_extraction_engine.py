from src.analysis.real_note_extraction_engine import (
    RealNoteExtractionEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        RealNoteExtractionEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        RealNoteExtractionEngine()
    )

    result = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "Real Note Distribution"
    )

    print(
        "=" * 40
    )

    for note, percentage in (
        result.items()
    ):

        print(
            f"{note}: {percentage}%"
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
        "Real Note Extraction Engine V1.0"
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