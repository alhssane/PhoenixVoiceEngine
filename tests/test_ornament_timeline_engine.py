from src.performance.ornament_extraction_engine import (
    OrnamentExtractionEngine,
)

from src.performance.ornament_timeline_engine import (
    OrnamentTimelineEngine,
)


def build_ornament(
    ornament_type,
    start_time,
    end_time,
):

    extractor = OrnamentExtractionEngine()

    return extractor.build_ornament(
        ornament_type,
        start_time,
        end_time,
        0.9,
    )


def test_build():

    engine = OrnamentTimelineEngine()

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_empty_timeline():

    engine = OrnamentTimelineEngine()

    result = engine.build_timeline(
        [],
    )

    assert (
        result["status"]
        == "EMPTY"
    )


def test_sorting():

    engine = OrnamentTimelineEngine()

    ornaments = [
        build_ornament(
            "vibrato",
            2.0,
            3.0,
        ),
        build_ornament(
            "melisma",
            1.0,
            2.0,
        ),
    ]

    ordered = engine.sort_ornaments(
        ornaments,
    )

    assert (
        ordered[0]["start_time"]
        == 1.0
    )


def test_event_generation():

    engine = OrnamentTimelineEngine()

    ornaments = [
        build_ornament(
            "vibrato",
            0.5,
            1.0,
        )
    ]

    result = engine.build_timeline(
        ornaments,
    )

    assert (
        result["count"]
        == 1
    )


def test_event_identifier():

    engine = OrnamentTimelineEngine()

    ornaments = [
        build_ornament(
            "melisma",
            0.5,
            1.0,
        )
    ]

    result = engine.build_timeline(
        ornaments,
    )

    assert (
        result["events"][0]["id"]
        == 1
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
        "Ornament Timeline Engine V1.0"
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