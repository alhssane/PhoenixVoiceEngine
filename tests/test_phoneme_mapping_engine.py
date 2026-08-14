from src.analysis.phoneme_mapping_engine import (
    PhonemeMappingEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        PhonemeMappingEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    results = (
        PhonemeMappingEngine()
        .analyze(
            AUDIO_FILE
        )
    )

    print()

    print(
        "Phoneme Mapping"
    )

    print(
        "=" * 40
    )

    for item in results[:20]:

        print(
            f"{item['start']}s -> "
            f"{item['end']}s | "
            f"{item['maqam']} | "
            f"{item['ornament']} | "
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
        "Phoneme Mapping Engine V1.0"
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