from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.pitch.melody_quality_assurance import (
    MelodyQualityAssurance,
)


def make_event(
    index=1,
    start=0.0,
    end=1.0,
    duration=1.0,
    f0=220.0,
    midi=57,
    note="A3",
    confidence=0.9,
):
    return {
        "event_index": index,
        "start_time": start,
        "end_time": end,
        "duration": duration,
        "f0_mean_hz": f0,
        "midi_mean": float(midi),
        "midi_note": midi,
        "note_name": note,
        "confidence": confidence,
        "frame_count": 10,
    }


def make_data(events):
    return {
        "version": "1.0.0",
        "analysis": {},
        "melody": {
            "source_frame_count": 100,
            "usable_frame_count": 80,
            "event_count": len(events),
            "events": events,
        },
    }


def test_build():

    engine = MelodyQualityAssurance()

    assert engine.VERSION == "1.0.0"

    print(
        "TEST 1: Build - PASS"
    )


def test_clean_melody():

    engine = MelodyQualityAssurance()

    events = [
        make_event(
            index=1,
            start=0.0,
            end=1.0,
            duration=1.0,
        ),
        make_event(
            index=2,
            start=1.1,
            end=2.0,
            duration=0.9,
            f0=261.63,
            midi=60,
            note="C4",
        ),
    ]

    result = engine.analyze(
        make_data(events)
    )

    assert result["status"] == "PASS"
    assert result["event_count"] == 2
    assert result["fail_count"] == 0

    print(
        "TEST 2: Clean Melody - PASS"
    )


def test_empty_melody():

    engine = MelodyQualityAssurance()

    result = engine.analyze(
        make_data([])
    )

    assert result["status"] == "FAIL"

    assert any(
        x["type"] == "EMPTY_MELODY"
        for x in result["issues"]
    )

    print(
        "TEST 3: Empty Melody Detection - PASS"
    )


def test_invalid_duration():

    engine = MelodyQualityAssurance()

    event = make_event(
        start=2.0,
        end=1.0,
        duration=-1.0,
    )

    result = engine.analyze(
        make_data([event])
    )

    assert result["status"] == "FAIL"

    assert any(
        x["type"] == "INVALID_DURATION"
        for x in result["issues"]
    )

    print(
        "TEST 4: Invalid Duration - PASS"
    )


def test_timing_overlap():

    engine = MelodyQualityAssurance()

    events = [
        make_event(
            index=1,
            start=0.0,
            end=1.0,
            duration=1.0,
        ),
        make_event(
            index=2,
            start=0.8,
            end=1.8,
            duration=1.0,
        ),
    ]

    result = engine.analyze(
        make_data(events)
    )

    assert any(
        x["type"] == "TIMING_OVERLAP"
        for x in result["issues"]
    )

    print(
        "TEST 5: Timing Overlap - PASS"
    )


def test_duplicate_index():

    engine = MelodyQualityAssurance()

    events = [
        make_event(
            index=1
        ),
        make_event(
            index=1,
            start=1.1,
            end=2.0,
            duration=0.9,
        ),
    ]

    result = engine.analyze(
        make_data(events)
    )

    assert any(
        x["type"]
        == "DUPLICATE_EVENT_INDEX"
        for x in result["issues"]
    )

    print(
        "TEST 6: Duplicate Event Detection - PASS"
    )


def test_invalid_f0():

    engine = MelodyQualityAssurance()

    event = make_event(
        f0=-10.0
    )

    result = engine.analyze(
        make_data([event])
    )

    assert any(
        x["type"] == "INVALID_F0"
        for x in result["issues"]
    )

    print(
        "TEST 7: Invalid F0 Protection - PASS"
    )


def test_invalid_midi():

    engine = MelodyQualityAssurance()

    event = make_event(
        midi=200
    )

    result = engine.analyze(
        make_data([event])
    )

    assert any(
        x["type"] == "INVALID_MIDI"
        for x in result["issues"]
    )

    print(
        "TEST 8: Invalid MIDI Protection - PASS"
    )


def test_confidence_validation():

    engine = MelodyQualityAssurance()

    event = make_event(
        confidence=1.5
    )

    result = engine.analyze(
        make_data([event])
    )

    assert any(
        x["type"]
        == "INVALID_CONFIDENCE"
        for x in result["issues"]
    )

    print(
        "TEST 9: Confidence Validation - PASS"
    )


def test_short_event_warning():

    engine = MelodyQualityAssurance(
        min_duration=0.10
    )

    event = make_event(
        start=0.0,
        end=0.05,
        duration=0.05,
    )

    result = engine.analyze(
        make_data([event])
    )

    assert any(
        x["type"]
        == "VERY_SHORT_EVENT"
        for x in result["issues"]
    )

    print(
        "TEST 10: Short Event Warning - PASS"
    )


def test_note_validation():

    engine = MelodyQualityAssurance()

    event = make_event(
        note="INVALID"
    )

    result = engine.analyze(
        make_data([event])
    )

    assert any(
        x["type"]
        == "INVALID_NOTE_NAME"
        for x in result["issues"]
    )

    print(
        "TEST 11: Note Validation - PASS"
    )


def test_no_auto_correction():

    engine = MelodyQualityAssurance()

    event = make_event(
        f0=-50.0
    )

    result = engine.analyze(
        make_data([event])
    )

    assert result[
        "no_auto_correction"
    ] is True

    assert event[
        "f0_mean_hz"
    ] == -50.0

    print(
        "TEST 12: No Auto Correction - PASS"
    )


def test_output_file():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        melody_path = (
            root
            / "melody.json"
        )

        qa_path = (
            root
            / "qa.json"
        )

        data = make_data(
            [
                make_event()
            ]
        )

        melody_path.write_text(
            json.dumps(
                data,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        engine = MelodyQualityAssurance()

        result = engine.analyze_file(
            melody_path,
            qa_path,
        )

        assert qa_path.exists()

        saved = json.loads(
            qa_path.read_text(
                encoding="utf-8"
            )
        )

        assert (
            saved["version"]
            == "1.0.0"
        )

        assert (
            saved["event_count"]
            == 1
        )

        assert (
            result["status"]
            == "PASS"
        )

    print(
        "TEST 13: Output File - PASS"
    )


if __name__ == "__main__":

    print("=" * 60)
    print("PhoenixVoiceEngine")
    print("Melody Quality Assurance V1.0")
    print("=" * 60)

    test_build()
    test_clean_melody()
    test_empty_melody()
    test_invalid_duration()
    test_timing_overlap()
    test_duplicate_index()
    test_invalid_f0()
    test_invalid_midi()
    test_confidence_validation()
    test_short_event_warning()
    test_note_validation()
    test_no_auto_correction()
    test_output_file()

    print("=" * 60)
    print("STATUS: PASS")
    print("=" * 60)