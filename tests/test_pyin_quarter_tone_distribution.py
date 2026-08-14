from src.analysis.pyin_quarter_tone_distribution import (
    PyinQuarterToneDistribution,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        PyinQuarterToneDistribution()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        PyinQuarterToneDistribution()
    )

    results = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "PYIN Quarter-Tone Distribution"
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
        "PYIN Quarter-Tone Distribution V1.0"
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