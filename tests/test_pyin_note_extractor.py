from src.analysis.pyin_note_extractor import (
    PyinNoteExtractor,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        PyinNoteExtractor()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        PyinNoteExtractor()
    )

    results = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "PYIN Note Distribution"
    )

    print(
        "=" * 40
    )

    for note, value in sorted(
        results.items(),
        key=lambda x: x[1],
        reverse=True,
    ):

        print(
            f"{note}: {value}%"
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
        "PYIN Note Extractor V1.0"
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