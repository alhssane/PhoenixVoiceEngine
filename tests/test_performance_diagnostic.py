import json
import tempfile
from pathlib import Path

from src.performance.performance_diagnostic import PerformanceDiagnostic


def make_pitch():
    return {
        "version": "1.0.0",
        "pitch": {
            "frames": [
                {
                    "time": 0.00,
                    "f0_hz": 261.63,
                    "voiced": True,
                    "voiced_probability": 0.9,
                },
                {
                    "time": 0.05,
                    "f0_hz": 262.00,
                    "voiced": True,
                    "voiced_probability": 0.9,
                },
                {
                    "time": 0.10,
                    "f0_hz": 262.30,
                    "voiced": True,
                    "voiced_probability": 0.9,
                },
            ]
        },
    }


def make_event(index=1, start=0.0, end=0.10):
    return {
        "event_index": index,
        "start_time": start,
        "end_time": end,
        "duration": end - start,
        "confidence": 0.8,
        "stability": 0.8,
        "pitch": {
            "range_semitones": 0.4,
        },
        "techniques": {
            "dominant_type": "NATURAL_VARIATION",
            "source_classifier": "NATURAL_VARIATION",
        },
        "contour": [
            {"time": start, "midi": 60.0, "offset": 0.0},
            {"time": end, "midi": 60.2, "offset": 0.2},
        ],
    }


def make_performance(events):
    return {
        "version": "1.0.0",
        "feature_version": "1.0.0",
        "performance": {
            "event_count": len(events),
            "events": events,
        },
    }


def test_build():
    engine = PerformanceDiagnostic()
    assert engine.VERSION == "1.0.0"
    assert engine.FEATURE_VERSION == "1.0.0"


def test_aligned_healthy_event():
    engine = PerformanceDiagnostic()
    result = engine.analyze(
        make_pitch(),
        make_performance([make_event()]),
    )
    assert result["status"] == "PASS"
    assert result["classification_counts"]["HEALTHY"] == 1


def test_invalid_timing():
    engine = PerformanceDiagnostic()
    event = make_event()
    event["end_time"] = -1.0
    result = engine.analyze(make_pitch(), make_performance([event]))
    assert result["status"] == "FAIL"
    assert any(x["type"] == "INVALID_EVENT_TIMING" for x in result["issues"])


def test_low_confidence():
    engine = PerformanceDiagnostic()
    event = make_event()
    event["confidence"] = 0.1
    result = engine.analyze(make_pitch(), make_performance([event]))
    assert result["status"] == "WARNING"
    assert any(x["type"] == "LOW_CONFIDENCE" for x in result["issues"])


def test_low_stability():
    engine = PerformanceDiagnostic()
    event = make_event()
    event["stability"] = 0.1
    result = engine.analyze(make_pitch(), make_performance([event]))
    assert any(x["type"] == "LOW_STABILITY" for x in result["issues"])


def test_contour_gap():
    engine = PerformanceDiagnostic(max_contour_gap=0.05)
    event = make_event()
    event["contour"] = [
        {"time": 0.0, "midi": 60.0},
        {"time": 0.20, "midi": 60.1},
    ]
    result = engine.analyze(make_pitch(), make_performance([event]))
    assert any(x["type"] == "CONTOUR_GAP" for x in result["issues"])


def test_classification_conflict():
    engine = PerformanceDiagnostic()
    event = make_event()
    event["techniques"]["source_classifier"] = "PITCH_BEND"
    event["techniques"]["dominant_type"] = "NATURAL_VARIATION"
    result = engine.analyze(make_pitch(), make_performance([event]))
    assert any(
        x["type"] == "CLASSIFICATION_CONFLICT"
        for x in result["issues"]
    )


def test_event_order():
    engine = PerformanceDiagnostic()
    e1 = make_event(index=2, start=0.0, end=0.1)
    e2 = make_event(index=1, start=0.2, end=0.3)
    result = engine.analyze(
        make_pitch(),
        make_performance([e1, e2]),
    )
    assert any(x["type"] == "EVENT_ORDER" for x in result["issues"])


def test_event_overlap():
    engine = PerformanceDiagnostic()
    e1 = make_event(index=1, start=0.0, end=0.2)
    e2 = make_event(index=2, start=0.1, end=0.3)
    result = engine.analyze(
        make_pitch(),
        make_performance([e1, e2]),
    )
    assert any(x["type"] == "EVENT_OVERLAP" for x in result["issues"])


def test_no_auto_correction():
    engine = PerformanceDiagnostic()
    event = make_event()
    original = json.dumps(event, sort_keys=True)
    engine.analyze(make_pitch(), make_performance([event]))
    assert json.dumps(event, sort_keys=True) == original


def test_raw_contour_preservation():
    engine = PerformanceDiagnostic()
    event = make_event()
    original = list(event["contour"])
    engine.analyze(make_pitch(), make_performance([event]))
    assert event["contour"] == original


def test_output_file():
    engine = PerformanceDiagnostic()
    event = make_event()

    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "diagnostic.json"
        result = engine.analyze_file(
            Path(temp) / "pitch.json",
            Path(temp) / "performance.json",
            output,
        ) if False else None

        pitch_path = Path(temp) / "pitch.json"
        performance_path = Path(temp) / "performance.json"

        pitch_path.write_text(
            json.dumps(make_pitch()),
            encoding="utf-8",
        )
        performance_path.write_text(
            json.dumps(make_performance([event])),
            encoding="utf-8",
        )

        result = engine.analyze_file(
            pitch_path,
            performance_path,
            output,
        )

        assert output.exists()
        assert result["version"] == "1.0.0"


def test_configuration_protection():
    try:
        PerformanceDiagnostic(min_confidence=1.5)
        assert False
    except ValueError:
        pass

    try:
        PerformanceDiagnostic(max_contour_gap=-1)
        assert False
    except ValueError:
        pass


def test_no_hidden_correction():
    engine = PerformanceDiagnostic()
    event = make_event()
    event["confidence"] = 0.1
    event["stability"] = 0.1
    before = dict(event)
    engine.analyze(make_pitch(), make_performance([event]))
    assert event["confidence"] == before["confidence"]
    assert event["stability"] == before["stability"]


def run():
    print("PhoenixVoiceEngine")
    print("Performance Diagnostic V1.0")
    print("=" * 60)

    tests = [
        ("TEST 1: Build", test_build),
        ("TEST 2: Healthy Event", test_aligned_healthy_event),
        ("TEST 3: Invalid Timing", test_invalid_timing),
        ("TEST 4: Low Confidence", test_low_confidence),
        ("TEST 5: Low Stability", test_low_stability),
        ("TEST 6: Contour Gap", test_contour_gap),
        ("TEST 7: Classification Conflict", test_classification_conflict),
        ("TEST 8: Event Order", test_event_order),
        ("TEST 9: Event Overlap", test_event_overlap),
        ("TEST 10: No Auto Correction", test_no_auto_correction),
        ("TEST 11: Raw Contour Preservation", test_raw_contour_preservation),
        ("TEST 12: Output File", test_output_file),
        ("TEST 13: Configuration Protection", test_configuration_protection),
        ("TEST 14: Hidden Correction Protection", test_no_hidden_correction),
    ]

    for name, fn in tests:
        fn()
        print(f"{name} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()