from src.maqam.quarter_tone_profile_engine import (
    QuarterToneProfileEngine,
)


AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        QuarterToneProfileEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_profile():

    engine = (
        QuarterToneProfileEngine()
    )

    profile = (
        engine.build_profile(
            AUDIO_FILE
        )
    )

    print()

    print(
        "Quarter-Tone Profile"
    )

    print(
        "=" * 40
    )

    for note, value in profile.items():

        print(
            f"{note}: {value}%"
        )

    assert (
        len(profile)
        > 0
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Quarter Tone Profile Engine V1.0"
    )

    print(
        "=" * 60
    )

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_profile()

    print(
        "TEST 2: test_profile - PASS"
    )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()