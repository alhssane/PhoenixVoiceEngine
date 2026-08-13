from src.generator.singing_reconstruction_engine import (
    SingingReconstructionEngine,
)


def test_build():

    engine = (
        SingingReconstructionEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_blueprint_creation():

    engine = (
        SingingReconstructionEngine()
    )

    blueprint = (
        engine.build_blueprint(
            {"maqam": "rast"},
            {"expression": 0.9},
            {"count": 5},
            {"average_score": 0.8},
        )
    )

    assert (
        blueprint["status"]
        == "READY"
    )


def test_reconstruction():

    engine = (
        SingingReconstructionEngine()
    )

    blueprint = (
        engine.build_blueprint(
            {"maqam": "rast"},
            {"expression": 0.9},
            {"count": 5},
            {"average_score": 0.8},
        )
    )

    result = (
        engine.reconstruct(
            blueprint
        )
    )

    assert (
        result["status"]
        == "RECONSTRUCTED"
    )


def test_layer_count():

    engine = (
        SingingReconstructionEngine()
    )

    blueprint = (
        engine.build_blueprint(
            {"maqam": "rast"},
            {"expression": 0.9},
            {"count": 5},
            {"average_score": 0.8},
        )
    )

    result = (
        engine.reconstruct(
            blueprint
        )
    )

    assert (
        result["layers"]
        == 4
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
        "Singing Reconstruction Engine V1.0"
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