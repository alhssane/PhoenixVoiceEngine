from src.voice.voice_dna_engine import (
    VoiceDNAEngine,
)


def build_samples():

    return [
        {
            "timbre": 0.9,
            "vibrato": 0.8,
            "expression": 0.7,
            "articulation": 0.9,
        },
        {
            "timbre": 0.8,
            "vibrato": 0.9,
            "expression": 0.8,
            "articulation": 0.8,
        },
    ]


def test_build():

    engine = VoiceDNAEngine()

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_normalization():

    engine = VoiceDNAEngine()

    assert (
        engine.normalize(
            1.5
        )
        == 1.0
    )


def test_profile_generation():

    engine = VoiceDNAEngine()

    profile = (
        engine.build_profile(
            0.9,
            0.8,
            0.7,
            0.9,
        )
    )

    assert (
        profile[
            "voice_dna_score"
        ]
        > 0
    )


def test_empty_analysis():

    engine = VoiceDNAEngine()

    result = engine.analyze(
        []
    )

    assert (
        result["status"]
        == "EMPTY"
    )


def test_analysis():

    engine = VoiceDNAEngine()

    result = engine.analyze(
        build_samples()
    )

    assert (
        result["status"]
        == "READY"
    )


def test_average_score():

    engine = VoiceDNAEngine()

    result = engine.analyze(
        build_samples()
    )

    assert (
        0.0
        <= result[
            "average_score"
        ]
        <= 1.0
    )


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith(
            "test_"
        )
    ]

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Voice DNA Engine V1.0"
    )

    print("=" * 60)

    for index, test in enumerate(
        tests,
        1,
    ):

        test()

        print(
            f"TEST {index}: "
            f"{test.__name__} - PASS"
        )

    print("=" * 60)

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()