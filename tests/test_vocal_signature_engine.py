from src.analysis.vocal_signature_engine import (
    VocalSignatureEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        VocalSignatureEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    results = (
        VocalSignatureEngine()
        .analyze(
            AUDIO_FILE
        )
    )

    print()

    print(
        "Vocal Signature Analysis"
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
            f"Maqam: "
            f"{item['maqam']}"
        )

        print(
            f"Ornament: "
            f"{item['ornament']}"
        )

        print(
            f"Average Pitch: "
            f"{item['average_pitch']} Hz"
        )

        print(
            f"Quarter Tone: "
            f"{item['average_cents']} cents"
        )

        print(
            f"Notes: "
            f"{item['notes']}"
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
        "Vocal Signature Engine V1.0"
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