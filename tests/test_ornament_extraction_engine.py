from src.performance.ornament_extraction_engine import (
    OrnamentExtractionEngine,
)


def test_build():

    engine = OrnamentExtractionEngine()

    assert engine.VERSION == "1.0.0"


def test_supported_types():

    engine = OrnamentExtractionEngine()

    assert "VIBRATO" in engine.ORNAMENT_TYPES
    assert "PORTAMENTO" in engine.ORNAMENT_TYPES
    assert "MELISMA" in engine.ORNAMENT_TYPES


def test_build_vibrato():

    engine = OrnamentExtractionEngine()

    result = engine.build_ornament(
        "vibrato",
        1.0,
        2.0,
        0.95,
    )

    assert result["type"] == "VIBRATO"


def test_duration():

    engine = OrnamentExtractionEngine()

    result = engine.build_ornament(
        "pitch_bend",
        2.0,
        3.5,
        0.80,
    )

    assert result["duration"] == 1.5


def test_empty_analysis():

    engine = OrnamentExtractionEngine()

    result = engine.analyze([])

    assert result["status"] == "NO_ORNAMENTS"


def test_ornament_detection():

    engine = OrnamentExtractionEngine()

    ornament = engine.build_ornament(
        "melisma",
        0.0,
        1.0,
        0.90,
    )

    result = engine.analyze([ornament])

    assert (
        result["status"]
        == "ORNAMENTS_DETECTED"
    )


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith("test_")
    ]

    print("PhoenixVoiceEngine")
    print("Ornament Extraction Engine V1.0")
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