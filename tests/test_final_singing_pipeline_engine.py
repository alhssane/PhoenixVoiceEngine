from src.generator.final_singing_pipeline_engine import (
    FinalSingingPipelineEngine,
)


def build_data():

    return {
        "blueprint": {
            "status": "READY",
            "components": 7,
        },
        "reconstruction": {
            "status": "RECONSTRUCTED",
            "layers": 4,
        },
    }


def test_build():

    engine = (
        FinalSingingPipelineEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_pipeline_creation():

    engine = (
        FinalSingingPipelineEngine()
    )

    data = build_data()

    pipeline = (
        engine.build_pipeline(
            data["blueprint"],
            data["reconstruction"],
        )
    )

    assert (
        pipeline[
            "pipeline_status"
        ]
        == "READY"
    )


def test_execution():

    engine = (
        FinalSingingPipelineEngine()
    )

    data = build_data()

    pipeline = (
        engine.build_pipeline(
            data["blueprint"],
            data["reconstruction"],
        )
    )

    result = (
        engine.execute(
            pipeline
        )
    )

    assert (
        result["status"]
        == "COMPLETED"
    )


def test_stage_count():

    engine = (
        FinalSingingPipelineEngine()
    )

    data = build_data()

    result = engine.analyze(
        data["blueprint"],
        data["reconstruction"],
    )

    assert (
        result["stages"]
        == 2
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
        "Final Singing Pipeline Engine V1.0"
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