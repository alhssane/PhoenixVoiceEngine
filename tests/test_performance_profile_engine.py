from src.performance.performance_profile_engine import (
    PerformanceProfileEngine,
)


def build_sample():

    engine = PerformanceProfileEngine()

    return engine.build_profile(
        dynamics=0.90,
        energy=0.85,
        breath=0.80,
        sustain=0.95,
        attack=0.75,
        release=0.82,
        expression=0.91,
    )


def test_build():

    engine = PerformanceProfileEngine()

    assert engine.VERSION == "1.0.0"


def test_normalization():

    engine = PerformanceProfileEngine()

    assert engine.normalize(1.5) == 1.0
    assert engine.normalize(-1.0) == 0.0


def test_profile_generation():

    profile = build_sample()

    assert "average_score" in profile


def test_average_range():

    profile = build_sample()

    assert 0.0 <= profile["average_score"] <= 1.0


def test_empty_analysis():

    engine = PerformanceProfileEngine()

    result = engine.analyze([])

    assert result["status"] == "NO_PROFILE"


def test_profile_analysis():

    engine = PerformanceProfileEngine()

    result = engine.analyze(
        [build_sample()]
    )

    assert result["status"] == "PROFILE_READY"


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith("test_")
    ]

    print("PhoenixVoiceEngine")
    print("Performance Profile Engine V1.0")
    print("=" * 60)

    for index, test in enumerate(tests, 1):

        test()

        print(
            f"TEST {index}: "
            f"{test.__name__} - PASS"
        )

    print("=" * 60)

    print("STATUS: PASS")


if __name__ == "__main__":

    run()