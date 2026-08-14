from src.maqam.cent_analyzer_engine import (
    CentAnalyzerEngine,
)


def test_build():

    engine = (
        CentAnalyzerEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_hz_to_midi():

    engine = (
        CentAnalyzerEngine()
    )

    midi = engine.hz_to_midi(
        440
    )

    assert (
        round(
            midi
        )
        == 69
    )


def test_cent_analysis():

    engine = (
        CentAnalyzerEngine()
    )

    result = engine.analyze(
        440
    )

    print()

    print(
        "Cent Analysis"
    )

    print(
        result
    )

    assert (
        "cents"
        in result
    )


def run():

    tests = [
        obj
        for name, obj
        in globals().items()
        if name.startswith(
            "test_"
        )
    ]

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Cent Analyzer Engine V1.0"
    )

    print(
        "=" * 60
    )

    for index, test in enumerate(
        tests,
        1,
    ):

        test()

        print(
            f"TEST {index}: "
            f"{test.__name__} - PASS"
        )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()