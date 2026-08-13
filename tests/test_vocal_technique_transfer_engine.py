from src.performance.vocal_technique_transfer_engine import (
    VocalTechniqueTransferEngine,
)


def build_sample():

    engine = (
        VocalTechniqueTransferEngine()
    )

    return [
        engine.build_technique(
            "vibrato",
            0.0,
            0.5,
            0.9,
        ),
        engine.build_technique(
            "run",
            0.5,
            1.0,
            0.8,
        ),
    ]


def test_build():

    engine = (
        VocalTechniqueTransferEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_supported_types():

    engine = (
        VocalTechniqueTransferEngine()
    )

    assert (
        "vibrato"
        in engine.SUPPORTED_TECHNIQUES
    )


def test_technique_creation():

    engine = (
        VocalTechniqueTransferEngine()
    )

    technique = (
        engine.build_technique(
            "trill",
            1.0,
            2.0,
            0.7,
        )
    )

    assert (
        technique["duration"]
        == 1.0
    )


def test_transfer():

    engine = (
        VocalTechniqueTransferEngine()
    )

    result = engine.transfer(
        build_sample(),
        [
            "يا",
            "روحي",
        ],
    )

    assert len(result) == 2


def test_technique_preserved():

    engine = (
        VocalTechniqueTransferEngine()
    )

    result = engine.transfer(
        build_sample(),
        [
            "يا",
            "روحي",
        ],
    )

    assert (
        result[0]["technique"]
        == "vibrato"
    )


def test_analysis():

    engine = (
        VocalTechniqueTransferEngine()
    )

    result = engine.analyze(
        build_sample(),
        [
            "يا",
            "روحي",
        ],
    )

    assert (
        result["status"]
        == "READY"
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
        "Vocal Technique Transfer Engine V1.0"
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