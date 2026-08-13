from src.performance.expression_transfer_engine import (
    ExpressionTransferEngine,
)


def build_sample():

    engine = (
        ExpressionTransferEngine()
    )

    return [
        engine.build_expression(
            "emotional",
            0.0,
            0.5,
            0.9,
        ),
        engine.build_expression(
            "powerful",
            0.5,
            1.0,
            0.8,
        ),
    ]


def test_build():

    engine = (
        ExpressionTransferEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_supported_types():

    engine = (
        ExpressionTransferEngine()
    )

    assert (
        "emotional"
        in engine.SUPPORTED_EXPRESSIONS
    )


def test_expression_creation():

    engine = (
        ExpressionTransferEngine()
    )

    expression = (
        engine.build_expression(
            "soft",
            1.0,
            2.0,
            0.7,
        )
    )

    assert (
        expression["duration"]
        == 1.0
    )


def test_transfer():

    engine = (
        ExpressionTransferEngine()
    )

    result = engine.transfer(
        build_sample(),
        [
            "يا",
            "روحي",
        ],
    )

    assert len(result) == 2


def test_expression_preserved():

    engine = (
        ExpressionTransferEngine()
    )

    result = engine.transfer(
        build_sample(),
        [
            "يا",
            "روحي",
        ],
    )

    assert (
        result[0]["expression"]
        == "emotional"
    )


def test_analysis():

    engine = (
        ExpressionTransferEngine()
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
        "Expression Transfer Engine V1.0"
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