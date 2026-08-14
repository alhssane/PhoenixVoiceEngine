from src.maqam.quarter_tone_map_engine import (
    QuarterToneMapEngine,
)


AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        QuarterToneMapEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        QuarterToneMapEngine()
    )

    results = (
        engine.analyze(
            AUDIO_FILE
        )
    )

    print()

    print(
        "Quarter Tone Analysis"
    )

    print(
        "=" * 40
    )

    print(
        f"Detected samples: "
        f"{len(results)}"
    )

    print()

    for item in results[:20]:

        print(
            item
        )

    assert (
        isinstance(
            results,
            list,
        )
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Quarter Tone Map Engine V1.0"
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