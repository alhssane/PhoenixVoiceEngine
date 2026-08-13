from src.generator.singing_blueprint_engine import (
    SingingBlueprintEngine,
)


def build_data():

    return {
        "maqam": {"name": "rast"},
        "tonic": {"note": "C"},
        "jins": {"name": "rast"},
        "musical_identity": {
            "status": "READY"
        },
        "performance": {
            "status": "READY"
        },
        "voice_dna": {
            "average_score": 0.85
        },
        "lyrics": {
            "count": 10
        },
    }


def test_build():

    engine = (
        SingingBlueprintEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_blueprint_creation():

    engine = (
        SingingBlueprintEngine()
    )

    data = build_data()

    result = engine.build(
        data["maqam"],
        data["tonic"],
        data["jins"],
        data["musical_identity"],
        data["performance"],
        data["voice_dna"],
        data["lyrics"],
    )

    assert (
        result["status"]
        == "READY"
    )


def test_component_count():

    engine = (
        SingingBlueprintEngine()
    )

    data = build_data()

    result = engine.analyze(
        data["maqam"],
        data["tonic"],
        data["jins"],
        data["musical_identity"],
        data["performance"],
        data["voice_dna"],
        data["lyrics"],
    )

    assert (
        result["components"]
        == 7
    )


def test_analysis():

    engine = (
        SingingBlueprintEngine()
    )

    data = build_data()

    result = engine.analyze(
        data["maqam"],
        data["tonic"],
        data["jins"],
        data["musical_identity"],
        data["performance"],
        data["voice_dna"],
        data["lyrics"],
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
        "Singing Blueprint Engine V1.0"
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