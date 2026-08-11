from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.pitch.lyric_melody_alignment_diagnostic import (
    LyricMelodyAlignmentDiagnostic,
)


def word(
    index=1,
    text="يا",
    start=0.0,
    end=1.0,
):
    return {
        "index": index,
        "text": text,
        "original_text": text,
        "final_text": text,
        "start_time": start,
        "end_time": end,
    }


def event(
    index=1,
    start=0.0,
    end=1.0,
):
    return {
        "event_index": index,
        "start_time": start,
        "end_time": end,
        "duration": end - start,
        "note_name": "A3",
        "midi_note": 57,
        "f0_mean_hz": 220.0,
        "confidence": 0.9,
    }


def pitch_frame(
    time=0.5,
    voiced=True,
    f0=220.0,
):
    return {
        "time": time,
        "voiced": voiced,
        "f0_hz": f0,
    }


def lyrics(words):
    return {
        "words": words,
    }


def melody(events):
    return {
        "melody": {
            "events": events,
        }
    }


def pitch(frames):
    return {
        "pitch": {
            "frames": frames,
        }
    }


def test_build():

    engine = LyricMelodyAlignmentDiagnostic()

    assert engine.VERSION == "1.0.0"

    print("TEST 1: Build - PASS")


def test_aligned_word():

    engine = LyricMelodyAlignmentDiagnostic()

    result = engine.diagnose(
        lyrics([
            word(
                start=0.0,
                end=1.0,
            )
        ]),
        melody([
            event(
                start=0.0,
                end=1.0,
            )
        ]),
        pitch([
            pitch_frame()
        ]),
    )

    item = result["words"][0]

    assert (
        item["classification"]
        == "ALIGNED"
    )

    print("TEST 2: Aligned Word - PASS")


def test_true_no_melody():

    engine = LyricMelodyAlignmentDiagnostic()

    result = engine.diagnose(
        lyrics([
            word(
                start=0.0,
                end=1.0,
            )
        ]),
        melody([
            event(
                start=2.0,
                end=3.0,
            )
        ]),
        pitch([]),
    )

    item = result["words"][0]

    assert (
        item["classification"]
        == "TRUE_NO_MELODY"
    )

    print("TEST 3: True No Melody - PASS")


def test_boundary_mismatch():

    engine = LyricMelodyAlignmentDiagnostic(
        nearby_threshold=0.25
    )

    result = engine.diagnose(
        lyrics([
            word(
                start=1.0,
                end=2.0,
            )
        ]),
        melody([
            event(
                start=0.0,
                end=0.9,
            )
        ]),
        pitch([]),
    )

    item = result["words"][0]

    assert (
        item["classification"]
        == "POSSIBLE_BOUNDARY_MISMATCH"
    )

    print(
        "TEST 4: Boundary Mismatch - PASS"
    )


def test_pitch_gap():

    engine = LyricMelodyAlignmentDiagnostic()

    result = engine.diagnose(
        lyrics([
            word(
                start=1.0,
                end=2.0,
            )
        ]),
        melody([
            event(
                start=0.0,
                end=0.5,
            ),
            event(
                start=2.5,
                end=3.0,
            ),
        ]),
        pitch([
            pitch_frame(
                time=1.2,
                voiced=True,
            ),
            pitch_frame(
                time=1.5,
                voiced=True,
            ),
            pitch_frame(
                time=1.8,
                voiced=True,
            ),
        ]),
    )

    item = result["words"][0]

    assert (
        item["classification"]
        == "POSSIBLE_PITCH_GAP"
    )

    print(
        "TEST 5: Possible Pitch Gap - PASS"
    )


def test_no_auto_correction():

    engine = LyricMelodyAlignmentDiagnostic()

    original = word(
        text="الأصل",
        start=1.0,
        end=2.0,
    )

    result = engine.diagnose(
        lyrics([original]),
        melody([]),
        pitch([]),
    )

    assert (
        result["no_auto_correction"]
        is True
    )

    assert (
        result["words"][0]["text"]
        == "الأصل"
    )

    print(
        "TEST 6: No Auto Correction - PASS"
    )


def test_previous_and_next():

    engine = LyricMelodyAlignmentDiagnostic()

    result = engine.diagnose(
        lyrics([
            word(
                start=1.0,
                end=2.0,
            )
        ]),
        melody([
            event(
                index=1,
                start=0.5,
                end=0.9,
            ),
            event(
                index=2,
                start=2.1,
                end=2.5,
            ),
        ]),
        pitch([]),
    )

    item = result["words"][0]

    assert (
        item["previous_event"]
        is not None
    )

    assert (
        item["next_event"]
        is not None
    )

    assert (
        item["previous_event"][
            "event_index"
        ]
        == 1
    )

    assert (
        item["next_event"][
            "event_index"
        ]
        == 2
    )

    print(
        "TEST 7: Previous/Next Detection - PASS"
    )


def test_pitch_frame_count():

    engine = LyricMelodyAlignmentDiagnostic()

    result = engine.diagnose(
        lyrics([
            word(
                start=0.0,
                end=1.0,
            )
        ]),
        melody([]),
        pitch([
            pitch_frame(
                time=0.1,
                voiced=True,
            ),
            pitch_frame(
                time=0.5,
                voiced=False,
            ),
            pitch_frame(
                time=0.8,
                voiced=True,
            ),
        ]),
    )

    pitch_result = result[
        "words"
    ][0]["pitch"]

    assert (
        pitch_result["frame_count"]
        == 3
    )

    assert (
        pitch_result[
            "voiced_frame_count"
        ]
        == 2
    )

    print(
        "TEST 8: Pitch Frame Analysis - PASS"
    )


def test_classification_counts():

    engine = LyricMelodyAlignmentDiagnostic()

    result = engine.diagnose(
        lyrics([
            word(
                index=1,
                start=0.0,
                end=1.0,
            ),
            word(
                index=2,
                start=2.0,
                end=3.0,
            ),
        ]),
        melody([
            event(
                index=1,
                start=0.0,
                end=1.0,
            )
        ]),
        pitch([]),
    )

    counts = result[
        "classification_counts"
    ]

    assert counts[
        "ALIGNED"
    ] == 1

    assert counts[
        "TRUE_NO_MELODY"
    ] == 1

    print(
        "TEST 9: Classification Counts - PASS"
    )


def test_output_file():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        lyrics_path = (
            root / "lyrics.json"
        )

        melody_path = (
            root / "melody.json"
        )

        pitch_path = (
            root / "pitch.json"
        )

        output_path = (
            root / "diagnostic.json"
        )

        lyrics_path.write_text(
            json.dumps(
                lyrics([
                    word()
                ]),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        melody_path.write_text(
            json.dumps(
                melody([
                    event()
                ]),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        pitch_path.write_text(
            json.dumps(
                pitch([
                    pitch_frame()
                ]),
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        engine = (
            LyricMelodyAlignmentDiagnostic()
        )

        result = engine.analyze_file(
            lyrics_path,
            melody_path,
            pitch_path,
            output_path,
        )

        assert output_path.exists()

        saved = json.loads(
            output_path.read_text(
                encoding="utf-8"
            )
        )

        assert (
            saved["version"]
            == "1.0.0"
        )

        assert (
            saved[
                "diagnostic_count"
            ]
            == 1
        )

        assert (
            result[
                "classification_counts"
            ]["ALIGNED"]
            == 1
        )

    print(
        "TEST 10: Output File - PASS"
    )


def test_invalid_configuration():

    try:

        LyricMelodyAlignmentDiagnostic(
            nearby_threshold=-1
        )

    except ValueError:
        pass

    else:

        raise AssertionError(
            "Negative nearby threshold was accepted."
        )

    print(
        "TEST 11: Configuration Protection - PASS"
    )


if __name__ == "__main__":

    print("=" * 60)
    print("PhoenixVoiceEngine")
    print(
        "Lyric–Melody Alignment Diagnostic V1.0"
    )
    print("=" * 60)

    test_build()
    test_aligned_word()
    test_true_no_melody()
    test_boundary_mismatch()
    test_pitch_gap()
    test_no_auto_correction()
    test_previous_and_next()
    test_pitch_frame_count()
    test_classification_counts()
    test_output_file()
    test_invalid_configuration()

    print("=" * 60)
    print("STATUS: PASS")
    print("=" * 60)