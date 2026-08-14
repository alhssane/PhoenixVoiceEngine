from src.analysis.pyin_pitch_engine import (
    PyinPitchEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        PyinPitchEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    engine = (
        PyinPitchEngine()
    )

    result = engine.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "PYIN Analysis"
    )

    print(
        "=" * 40
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )

    assert (
        result["status"]
        == "SUCCESS"
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "PYIN Pitch Engine V1.0"
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