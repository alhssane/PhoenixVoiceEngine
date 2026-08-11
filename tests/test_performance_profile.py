"""
PhoenixVoiceEngine
Performance Profile V1.0 tests
"""

from src.performance.performance_profile import PerformanceProfile


def make_data():
    contour = [
        {"time": 0.00, "midi": 60.0, "offset": 0.0},
        {"time": 0.10, "midi": 60.4, "offset": 0.4},
        {"time": 0.20, "midi": 59.8, "offset": -0.2},
    ]

    melody_event = {
        "event_index": 1,
        "start_time": 0.0,
        "end_time": 0.3,
        "duration": 0.3,
        "midi_note": 60,
        "note_name": "C4",
        "midi_mean": 60.05,
        "f0_mean_hz": 261.7,
        "confidence": 0.8,
        "stability": 0.7,
        "pitch_contour": contour,
    }

    performance_event = {
        "event_index": 1,
        "start_time": 0.0,
        "end_time": 0.3,
        "duration": 0.3,
        "confidence": 0.8,
        "stability": 0.7,
        "melody": {
            "midi_note": 60,
            "note_name": "C4",
            "midi_mean": 60.05,
            "f0_mean_hz": 261.7,
        },
        "pitch": {
            "min_midi": 59.8,
            "max_midi": 60.4,
            "range_semitones": 0.6,
            "mean_offset_semitones": 0.05,
            "max_deviation_semitones": 0.4,
            "direction": "ASCENDING",
            "slope_semitones_per_second": 0.5,
            "directional_ratio": 0.7,
        },
        "techniques": {
            "dominant_type": "VIBRATO",
            "source_classifier": "PITCH_BEND",
        },
        "contour": contour,
    }

    diagnostic_event = {
        "event_index": 1,
        "classification": "HEALTHY",
        "classifications": ["HEALTHY"],
        "issues": [],
    }

    pitch = {
        "version": "1.0.0",
        "pitch": {"frames": [
            {
                "time": p["time"],
                "f0_hz": 261.7,
                "voiced": True,
                "voiced_probability": 0.9,
            }
            for p in contour
        ]},
    }

    melody = {
        "version": "1.0.0",
        "feature_version": "1.2.1",
        "melody": {"events": [melody_event]},
    }

    performance = {
        "version": "1.0.0",
        "feature_version": "1.0.0",
        "performance": {
            "events": [performance_event],
        },
    }

    diagnostic = {
        "version": "1.0.0",
        "feature_version": "1.0.0",
        "patch_version": "1.0.1",
        "status": "WARNING",
        "issue_count": 1,
        "fail_count": 0,
        "warning_count": 1,
        "analysis": {
            "boundary_overlap_count": 0,
            "real_event_overlap_count": 0,
        },
        "events": [diagnostic_event],
    }

    return pitch, melody, performance, diagnostic


def test():
    print("PhoenixVoiceEngine")
    print("Performance Profile V1.0")
    print("=" * 60)

    tests = [
        test_build,
        test_event_count,
        test_event_order,
        test_timing_preservation,
        test_raw_contour_preservation,
        test_primary_secondary_techniques,
        test_statistics,
        test_diagnostic_passthrough,
        test_capability_protection,
    ]

    for index, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {index}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


def test_build():
    engine = PerformanceProfile()
    assert engine.VERSION == "1.0.0"
    assert engine.FEATURE_VERSION == "1.0.0"


def test_event_count():
    engine = PerformanceProfile()
    pitch, melody, performance, diagnostic = make_data()
    result = engine.analyze(
        pitch,
        melody,
        performance,
        diagnostic,
    )
    assert result["profile"]["event_count"] == 1


def test_event_order():
    engine = PerformanceProfile()
    pitch, melody, performance, diagnostic = make_data()
    result = engine.analyze(
        pitch,
        melody,
        performance,
        diagnostic,
    )
    assert result["profile"]["events"][0]["event_index"] == 1


def test_timing_preservation():
    engine = PerformanceProfile()
    pitch, melody, performance, diagnostic = make_data()
    result = engine.analyze(
        pitch,
        melody,
        performance,
        diagnostic,
    )
    event = result["profile"]["events"][0]
    assert event["timing"]["start_time"] == 0.0
    assert event["timing"]["end_time"] == 0.3
    assert event["timing"]["duration"] == 0.3


def test_raw_contour_preservation():
    engine = PerformanceProfile()
    pitch, melody, performance, diagnostic = make_data()
    result = engine.analyze(
        pitch,
        melody,
        performance,
        diagnostic,
    )
    event = result["profile"]["events"][0]
    assert event["contour"]["raw_preserved"] is True
    assert event["contour"]["point_count"] == 3
    assert event["contour"]["points"][1]["midi"] == 60.4


def test_primary_secondary_techniques():
    engine = PerformanceProfile()
    pitch, melody, performance, diagnostic = make_data()
    result = engine.analyze(
        pitch,
        melody,
        performance,
        diagnostic,
    )
    techniques = result["profile"]["events"][0]["performance"]["techniques"]
    assert techniques["primary"] == "PITCH_BEND"
    assert "VIBRATO" in techniques["secondary"]


def test_statistics():
    engine = PerformanceProfile()
    pitch, melody, performance, diagnostic = make_data()
    result = engine.analyze(
        pitch,
        melody,
        performance,
        diagnostic,
    )
    stats = result["profile"]["statistics"]
    assert stats["event_count"] == 1
    assert stats["duration"]["total"] == 0.3
    assert stats["confidence"]["mean"] == 0.8
    assert stats["stability"]["mean"] == 0.7


def test_diagnostic_passthrough():
    engine = PerformanceProfile()
    pitch, melody, performance, diagnostic = make_data()
    result = engine.analyze(
        pitch,
        melody,
        performance,
        diagnostic,
    )
    diag = result["profile"]["diagnostic"]
    assert diag["status"] == "WARNING"
    assert diag["issue_count"] == 1


def test_capability_protection():
    engine = PerformanceProfile()
    pitch, melody, performance, diagnostic = make_data()
    result = engine.analyze(
        pitch,
        melody,
        performance,
        diagnostic,
    )
    capabilities = result["profile"]["capabilities"]

    assert capabilities["raw_contour_preserved"] is True
    assert capabilities["timing_preserved"] is True
    assert capabilities["no_auto_correction"] is True

    assert capabilities["maqam_analyzed"] is False
    assert capabilities["arab_analyzed"] is False
    assert capabilities["phrase_analyzed"] is False
    assert capabilities["generation_ready"] is False


if __name__ == "__main__":
    test()