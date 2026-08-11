from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.performance.performance_analyzer import PerformanceAnalyzer


def make_contour(start=0.0, step=0.05, values=None):
    values = values or [60.0, 60.0, 60.0, 60.0]
    return [
        {
            "time": start + i * step,
            "midi": value,
            "f0_hz": 440.0 * (2.0 ** ((value - 69.0) / 12.0)),
            "offset": value - 60.0,
        }
        for i, value in enumerate(values)
    ]


def make_event(values, start=0.0, step=0.05):
    contour = make_contour(start, step, values)
    end = contour[-1]["time"] + step
    return {
        "event_index": 1,
        "start_time": start,
        "end_time": end,
        "duration": end - start,
        "midi_note": 60,
        "note_name": "C4",
        "midi_mean": sum(values) / len(values),
        "f0_mean_hz": 261.6256,
        "confidence": 0.9,
        "stability": 0.9,
        "frame_count": len(values),
        "pitch_contour": contour,
    }


def make_data(event):
    frames = [
        {
            "time": p["time"],
            "f0_hz": p["f0_hz"],
            "voiced": True,
            "voiced_probability": 0.95,
        }
        for p in event["pitch_contour"]
    ]
    return (
        {"version": "1.0.0", "pitch": {"frames": frames}},
        {
            "version": "1.0.0",
            "feature_version": "1.2.1",
            "melody": {"events": [event]},
        },
    )


def test_build():
    engine = PerformanceAnalyzer()
    assert engine.VERSION == "1.0.0"
    assert engine.FEATURE_VERSION == "1.0.0"


def test_stable_note_extraction():
    engine = PerformanceAnalyzer()
    event = make_event([60, 60.05, 59.95, 60.0])
    pitch, melody = make_data(event)
    result = engine.analyze(pitch, melody)
    item = result["performance"]["events"][0]
    assert item["melody"]["midi_note"] == 60
    assert item["contour"]


def test_pitch_deviation():
    engine = PerformanceAnalyzer()
    event = make_event([60, 60.5, 60.2, 59.8])
    pitch, melody = make_data(event)
    item = engine.analyze(pitch, melody)["performance"]["events"][0]
    assert item["pitch"]["range_semitones"] > 0
    assert item["pitch"]["max_deviation_semitones"] > 0


def test_ascending_detection():
    engine = PerformanceAnalyzer()
    event = make_event([60, 60.5, 61.0, 61.5])
    pitch, melody = make_data(event)
    item = engine.analyze(pitch, melody)["performance"]["events"][0]
    assert item["pitch"]["direction"] == "ASCENDING"


def test_descending_detection():
    engine = PerformanceAnalyzer()
    event = make_event([61.5, 61.0, 60.5, 60.0])
    pitch, melody = make_data(event)
    item = engine.analyze(pitch, melody)["performance"]["events"][0]
    assert item["pitch"]["direction"] == "DESCENDING"


def test_vibrato_detection():
    engine = PerformanceAnalyzer()
    event = make_event(
        [60, 60.35, 59.7, 60.4, 59.65, 60.3, 59.75, 60.25,
         59.7, 60.35, 59.8, 60.2],
        step=0.08,
    )
    pitch, melody = make_data(event)
    item = engine.analyze(pitch, melody)["performance"]["events"][0]
    assert item["techniques"]["vibrato"]["detected"] is True


def test_slide_detection():
    engine = PerformanceAnalyzer()
    event = make_event([60, 60.5, 61.0, 61.5, 62.0], step=0.10)
    pitch, melody = make_data(event)
    item = engine.analyze(pitch, melody)["performance"]["events"][0]
    assert item["techniques"]["slide"]["detected"] is True


def test_ornament_candidate():
    engine = PerformanceAnalyzer()
    event = make_event([60, 61.0, 60.2, 59.95, 60.0], step=0.05)
    pitch, melody = make_data(event)
    item = engine.analyze(pitch, melody)["performance"]["events"][0]
    assert item["techniques"]["ornament"]["detected"] is True


def test_pitch_bend():
    engine = PerformanceAnalyzer()
    event = make_event([60, 60.9, 60.3, 60.8], step=0.12)
    pitch, melody = make_data(event)
    item = engine.analyze(pitch, melody)["performance"]["events"][0]
    assert item["techniques"]["pitch_bend"]["detected"] is True


def test_timing_preservation():
    engine = PerformanceAnalyzer()
    event = make_event([60, 60.1, 60.0])
    pitch, melody = make_data(event)
    item = engine.analyze(pitch, melody)["performance"]["events"][0]
    assert item["start_time"] == event["start_time"]
    assert item["end_time"] == event["end_time"]
    assert item["duration"] == event["duration"]


def test_raw_contour_preservation():
    engine = PerformanceAnalyzer()
    event = make_event([60, 60.25, 59.8, 60.1])
    pitch, melody = make_data(event)
    item = engine.analyze(pitch, melody)["performance"]["events"][0]
    assert len(item["contour"]) == len(event["pitch_contour"])
    assert item["contour"][1]["midi"] == event["pitch_contour"][1]["midi"]


def test_event_order():
    engine = PerformanceAnalyzer()
    e1 = make_event([60, 60], start=0.0)
    e2 = make_event([62, 62], start=1.0)
    pitch = {
        "version": "1.0.0",
        "pitch": {"frames": [
            *[{
                "time": p["time"], "f0_hz": p["f0_hz"],
                "voiced": True, "voiced_probability": 0.9
            } for p in e1["pitch_contour"]],
            *[{
                "time": p["time"], "f0_hz": p["f0_hz"],
                "voiced": True, "voiced_probability": 0.9
            } for p in e2["pitch_contour"]],
        ]},
    }
    melody = {
        "version": "1.0.0",
        "melody": {"events": [e1, e2]},
    }
    result = engine.analyze(pitch, melody)
    indices = [
        x["event_index"] for x in result["performance"]["events"]
    ]
    assert indices == [1, 2]


def test_no_auto_correction():
    engine = PerformanceAnalyzer()
    event = make_event([60, 60.4, 59.7, 60.2])
    pitch, melody = make_data(event)
    result = engine.analyze(pitch, melody)
    assert result["analysis"]["no_auto_correction"] is True
    assert result["analysis"]["raw_contour_preserved"] is True


def test_output_file():
    engine = PerformanceAnalyzer()
    event = make_event([60, 60.1, 60.0])
    pitch, melody = make_data(event)

    with tempfile.TemporaryDirectory() as temp:
        p = Path(temp)
        pitch_file = p / "pitch.json"
        melody_file = p / "melody.json"
        output_file = p / "performance.json"

        pitch_file.write_text(json.dumps(pitch), encoding="utf-8")
        melody_file.write_text(json.dumps(melody), encoding="utf-8")

        result = engine.analyze_file(
            pitch_file,
            melody_file,
            output_file,
        )

        assert output_file.exists()
        saved = json.loads(output_file.read_text(encoding="utf-8"))
        assert saved["performance"]["event_count"] == 1
        assert result["feature_version"] == "1.0.0"


if __name__ == "__main__":
    print("=" * 60)
    print("PhoenixVoiceEngine")
    print("Performance Analysis V1.0")
    print("=" * 60)

    tests = [
        test_build,
        test_stable_note_extraction,
        test_pitch_deviation,
        test_ascending_detection,
        test_descending_detection,
        test_vibrato_detection,
        test_slide_detection,
        test_ornament_candidate,
        test_pitch_bend,
        test_timing_preservation,
        test_raw_contour_preservation,
        test_event_order,
        test_no_auto_correction,
        test_output_file,
    ]

    for index, test in enumerate(tests, 1):
        test()
        print(f"TEST {index}: {test.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")