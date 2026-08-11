from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.pitch.melody_analyzer import MelodyAnalyzer


def make_pitch_data(
    frames,
):
    return {
        "version": "1.0.0",
        "source": "test.wav",
        "pitch": {
            "frame_count": len(frames),
            "frames": frames,
        },
    }


def make_frame(
    index,
    time,
    f0,
    voiced=True,
    probability=0.95,
):
    return {
        "frame_index": index,
        "time": time,
        "f0_hz": f0,
        "voiced": voiced,
        "voiced_probability": probability,
    }


def test_build():

    engine = MelodyAnalyzer()

    assert engine.VERSION == "1.0.0"

    print(
        "TEST 1: Build - PASS"
    )


def test_midi_conversion():

    engine = MelodyAnalyzer()

    midi = engine.hz_to_midi(
        440.0
    )

    assert midi is not None
    assert abs(
        midi - 69.0
    ) < 0.001

    hz = engine.midi_to_hz(
        69.0
    )

    assert abs(
        hz - 440.0
    ) < 0.001

    print(
        "TEST 2: MIDI Conversion - PASS"
    )


def test_note_name_conversion():

    engine = MelodyAnalyzer()

    assert (
        engine.midi_to_note_name(
            69
        )
        == "A4"
    )

    assert (
        engine.midi_to_note_name(
            60
        )
        == "C4"
    )

    print(
        "TEST 3: Note Name Conversion - PASS"
    )


def test_unvoiced_protection():

    engine = MelodyAnalyzer()

    frames = [
        make_frame(
            0,
            0.00,
            220.0,
        ),
        make_frame(
            1,
            0.01,
            None,
            voiced=False,
            probability=0.0,
        ),
        make_frame(
            2,
            0.02,
            220.0,
        ),
    ]

    usable = engine._usable_frames(
        frames
    )

    assert len(
        usable
    ) == 2

    print(
        "TEST 4: Unvoiced Protection - PASS"
    )


def test_stable_event_detection():

    engine = MelodyAnalyzer(
        min_event_duration=0.02,
        max_gap=0.02,
    )

    frames = [
        make_frame(
            0,
            0.00,
            220.0,
        ),
        make_frame(
            1,
            0.01,
            220.5,
        ),
        make_frame(
            2,
            0.02,
            219.8,
        ),
        make_frame(
            3,
            0.03,
            220.2,
        ),
    ]

    result = engine.extract_melody(
        frames
    )

    assert (
        result["event_count"]
        == 1
    )

    event = result[
        "events"
    ][0]

    assert (
        event["f0_mean_hz"]
        > 200
    )

    assert (
        event["frame_count"]
        == 4
    )

    print(
        "TEST 5: Stable Event Detection - PASS"
    )


def test_note_change_detection():

    engine = MelodyAnalyzer(
        min_event_duration=0.02,
        max_gap=0.02,
        note_change_semitones=0.5,
    )

    frames = [
        make_frame(
            0,
            0.00,
            220.0,
        ),
        make_frame(
            1,
            0.01,
            220.0,
        ),
        make_frame(
            2,
            0.02,
            261.63,
        ),
        make_frame(
            3,
            0.03,
            261.63,
        ),
    ]

    result = engine.extract_melody(
        frames
    )

    assert (
        result["event_count"]
        == 2
    )

    assert (
        result["events"][0][
            "start_time"
        ]
        < result["events"][1][
            "start_time"
        ]
    )

    print(
        "TEST 6: Note Change Detection - PASS"
    )


def test_short_segment_protection():

    engine = MelodyAnalyzer(
        min_event_duration=0.08,
        max_gap=0.02,
    )

    frames = [
        make_frame(
            0,
            0.00,
            220.0,
        ),
        make_frame(
            1,
            0.01,
            220.0,
        ),
    ]

    result = engine.extract_melody(
        frames
    )

    assert (
        result["event_count"]
        == 0
    )

    print(
        "TEST 7: Short Segment Protection - PASS"
    )


def test_order_preservation():

    engine = MelodyAnalyzer(
        min_event_duration=0.02,
        max_gap=0.02,
    )

    frames = [
        make_frame(
            0,
            0.00,
            220.0,
        ),
        make_frame(
            1,
            0.01,
            220.0,
        ),
        make_frame(
            2,
            0.02,
            261.63,
        ),
        make_frame(
            3,
            0.03,
            261.63,
        ),
    ]

    result = engine.extract_melody(
        frames
    )

    events = result[
        "events"
    ]

    for i in range(
        1,
        len(events),
    ):

        assert (
            events[i][
                "start_time"
            ]
            >= events[i - 1][
                "start_time"
            ]
        )

    print(
        "TEST 8: Melody Ordering - PASS"
    )


def test_timing_preservation():

    engine = MelodyAnalyzer(
        min_event_duration=0.02,
        max_gap=0.02,
    )

    frames = [
        make_frame(
            0,
            1.00,
            220.0,
        ),
        make_frame(
            1,
            1.01,
            220.0,
        ),
        make_frame(
            2,
            1.02,
            220.0,
        ),
    ]

    result = engine.extract_melody(
        frames
    )

    assert (
        result["events"][0][
            "start_time"
        ]
        == 1.0
    )

    assert (
        result["events"][0][
            "end_time"
        ]
        > 1.0
    )

    print(
        "TEST 9: Timing Preservation - PASS"
    )


def test_output_structure():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        pitch_path = (
            root
            / "pitch.json"
        )

        output_path = (
            root
            / "melody.json"
        )

        frames = [
            make_frame(
                0,
                0.00,
                220.0,
            ),
            make_frame(
                1,
                0.01,
                220.0,
            ),
            make_frame(
                2,
                0.02,
                220.0,
            ),
            make_frame(
                3,
                0.03,
                220.0,
            ),
        ]

        pitch_path.write_text(
            json.dumps(
                make_pitch_data(
                    frames
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        engine = MelodyAnalyzer(
            min_event_duration=0.02,
            max_gap=0.02,
        )

        result = engine.analyze_file(
            pitch_path,
            output_path,
        )

        assert output_path.exists()

        assert (
            result["version"]
            == "1.0.0"
        )

        assert (
            "melody"
            in result
        )

        assert (
            "events"
            in result["melody"]
        )

        saved = json.loads(
            output_path.read_text(
                encoding="utf-8"
            )
        )

        assert (
            saved["melody"][
                "event_count"
            ]
            >= 0
        )

    print(
        "TEST 10: Output Structure - PASS"
    )


def test_no_auto_correction():

    engine = MelodyAnalyzer()

    frames = [
        make_frame(
            0,
            0.00,
            220.0,
        ),
        make_frame(
            1,
            0.01,
            220.0,
        ),
        make_frame(
            2,
            0.02,
            220.0,
        ),
    ]

    result = engine.extract_melody(
        frames
    )

    assert (
        "corrected"
        not in result
    )

    assert (
        "correction"
        not in result
    )

    print(
        "TEST 11: No Auto Correction - PASS"
    )


if __name__ == "__main__":

    print("=" * 60)
    print("PhoenixVoiceEngine")
    print("Melody Analyzer V1.0")
    print("=" * 60)

    test_build()
    test_midi_conversion()
    test_note_name_conversion()
    test_unvoiced_protection()
    test_stable_event_detection()
    test_note_change_detection()
    test_short_segment_protection()
    test_order_preservation()
    test_timing_preservation()
    test_output_structure()
    test_no_auto_correction()

    print("=" * 60)
    print("STATUS: PASS")
    print("=" * 60)