from src.analysis.clean_vocal_signature_engine import (
    CleanVocalSignatureEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        CleanVocalSignatureEngine()
    )

    assert (
        engine.VERSION
        == "2.0.0"
    )


def test_analysis():

    results = (
        CleanVocalSignatureEngine()
        .analyze(
            AUDIO_FILE
        )
    )

    print()

    print(
        "Clean Vocal Signature"
    )

    print(
        "=" * 40
    )

    for item in results[:15]:

        print()

        print(
            f"{item['start']}s -> "
            f"{item['end']}s"
        )

        print(
            f"Maqam: {item['maqam']}"
        )

        print(
            f"Pitch: "
            f"{item['average_pitch']} Hz"
        )

        print(
            f"Ornament: "
            f"{item['ornament']}"
        )

        print(
            f"Notes: "
            f"{item['note_count']}"
        )

    assert len(results) > 0


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Clean Vocal Signature Engine V2.0"
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