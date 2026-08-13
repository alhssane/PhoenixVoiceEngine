from src.performance.performance_timeline_engine import (
    PerformanceTimelineEngine,
)


def build_profile(
    start_time,
    end_time,
    dynamics,
    energy,
    expression,
):

    average = (
        dynamics
        + energy
        + expression
    ) / 3

    return {
        "start_time": start_time,
        "end_time": end_time,
        "dynamics": dynamics,
        "energy": energy,
        "expression": expression,
        "average_score": average,
    }


def test_build():

    engine = PerformanceTimelineEngine()

    assert engine.VERSION == "1.0.0"


def test_empty_timeline():

    engine = PerformanceTimelineEngine()

    result = engine.build_timeline([])

    assert result["status"] == "EMPTY"


def test_sorting():

    engine = PerformanceTimelineEngine()

    profiles = [
        build_profile(
            5.0,
            10.0,
            0.9,
            0.8,
            0.7,
        ),
        build_profile(
            0.0,
            5.0,
            0.7,
            0.6,
            0.5,
        ),
    ]

    ordered = engine.sort_segments(
        profiles,
    )

    assert (
        ordered[0]["start_time"]
        == 0.0
    )


def test_segment_generation():

    engine = PerformanceTimelineEngine()

    profiles = [
        build_profile(
            0.0,
            5.0,
            0.9,
            0.8,
            0.7,
        )
    ]

    result = engine.build_timeline(
        profiles,
    )

    assert result["count"] == 1


def test_duration():

    engine = PerformanceTimelineEngine()

    profiles = [
        build_profile(
            2.0,
            7.0,
            0.9,
            0.8,
            0.7,
        )
    ]

    result = engine.build_timeline(
        profiles,
    )

    assert (
        result["segments"][0]["duration"]
        == 5.0
    )


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith("test_")
    ]

    print("PhoenixVoiceEngine")
    print("Performance Timeline Engine V1.0")
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
    print("STATUS: PASS")


if __name__ == "__main__":

    run()