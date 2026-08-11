from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.pitch.lyric_melody_alignment import (
    LyricMelodyAlignment,
)


def make_word(
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
        "duration": end - start,
        "confidence": 0.9,
    }


def make_event(
    index=1,
    start=0.0,
    end=1.0,
    note="A3",
    midi=57,
    f0=220.0,
):
    return {
        "event_index": index,
        "start_time": start,
        "end_time": end,
        "duration": end - start,
        "f0_mean_hz": f0,
        "midi_mean": float(midi),
        "midi_note": midi,
        "note_name": note,
        "confidence": 0.9,
        "frame_count": 10,
    }


def make_lyrics(words):
    return {
        "version": "1.0.0",
        "word_count": len(words),
        "words": words,
    }


def make_melody(events):
    return {
        "version": "1.0.0",
        "melody": {
            "event_count": len(events),
            "events": events,
        },
    }


def test_build():

    engine = LyricMelodyAlignment()

    assert engine.VERSION == "1.0.0"

    print(
        "TEST 1: Build - PASS"
    )


def test_exact_alignment():

    engine = LyricMelodyAlignment()

    words = [
        make_word(
            index=1,
            start=0.0,
            end=1.0,
        )
    ]

    events = [
        make_event(
            index=1,
            start=0.0,
            end=1.0,
        )
    ]

    result = engine.align(
        make_lyrics(words),
        make_melody(events),
    )

    assert result[
        "aligned_word_count"
    ] == 1

    assert (
        result["words"][0][
            "alignment_status"
        ]
        == "ALIGNED"
    )

    assert (
        result["words"][0][
            "melody_event_count"
        ]
        == 1
    )

    print(
        "TEST 2: Exact Alignment - PASS"
    )


def test_partial_alignment():

    engine = LyricMelodyAlignment()

    words = [
        make_word(
            index=1,
            start=0.5,
            end=1.5,
        )
    ]

    events = [
        make_event(
            index=1,
            start=0.0,
            end=1.0,
        )
    ]

    result = engine.align(
        make_lyrics(words),
        make_melody(events),
    )

    item = result[
        "words"
    ][0]

    assert (
        item["alignment_status"]
        == "ALIGNED"
    )

    assert (
        item["melody_event_count"]
        == 1
    )

    assert (
        item["melody_events"][0][
            "overlap"
        ]
        == 0.5
    )

    print(
        "TEST 3: Partial Alignment - PASS"
    )


def test_multiple_melody_events():

    engine = LyricMelodyAlignment()

    words = [
        make_word(
            index=1,
            start=0.0,
            end=2.0,
        )
    ]

    events = [
        make_event(
            index=1,
            start=0.0,
            end=1.0,
            note="A3",
            midi=57,
        ),
        make_event(
            index=2,
            start=1.0,
            end=2.0,
            note="B3",
            midi=59,
        ),
    ]

    result = engine.align(
        make_lyrics(words),
        make_melody(events),
    )

    item = result[
        "words"
    ][0]

    assert (
        item["melody_event_count"]
        == 2
    )

    assert item[
        "notes"
    ] == [
        "A3",
        "B3",
    ]

    assert item[
        "midi_notes"
    ] == [
        57,
        59,
    ]

    print(
        "TEST 4: Multiple Melody Events - PASS"
    )


def test_no_overlap():

    engine = LyricMelodyAlignment()

    words = [
        make_word(
            index=1,
            start=0.0,
            end=0.5,
        )
    ]

    events = [
        make_event(
            index=1,
            start=1.0,
            end=2.0,
        )
    ]

    result = engine.align(
        make_lyrics(words),
        make_melody(events),
    )

    item = result[
        "words"
    ][0]

    assert (
        item["alignment_status"]
        == "NO_MELODY_OVERLAP"
    )

    assert (
        item["melody_event_count"]
        == 0
    )

    print(
        "TEST 5: No Overlap Protection - PASS"
    )


def test_timing_preservation():

    engine = LyricMelodyAlignment()

    word = make_word(
        index=10,
        text="كلمة",
        start=12.34,
        end=13.21,
    )

    event = make_event(
        index=5,
        start=12.0,
        end=13.5,
    )

    result = engine.align(
        make_lyrics([word]),
        make_melody([event]),
    )

    item = result[
        "words"
    ][0]

    assert (
        item["start_time"]
        == 12.34
    )

    assert (
        item["end_time"]
        == 13.21
    )

    print(
        "TEST 6: Timing Preservation - PASS"
    )


def test_event_order():

    engine = LyricMelodyAlignment()

    word = make_word(
        index=1,
        start=0.0,
        end=3.0,
    )

    events = [
        make_event(
            index=1,
            start=2.0,
            end=3.0,
            note="C4",
            midi=60,
        ),
        make_event(
            index=2,
            start=0.0,
            end=1.0,
            note="A3",
            midi=57,
        ),
        make_event(
            index=3,
            start=1.0,
            end=2.0,
            note="B3",
            midi=59,
        ),
    ]

    result = engine.align(
        make_lyrics([word]),
        make_melody(events),
    )

    assert result[
        "words"
    ][0]["midi_notes"] == [
        57,
        59,
        60,
    ]

    print(
        "TEST 7: Melody Order Preservation - PASS"
    )


def test_multiple_words():

    engine = LyricMelodyAlignment()

    words = [
        make_word(
            index=1,
            text="يا",
            start=0.0,
            end=1.0,
        ),
        make_word(
            index=2,
            text="حبيبي",
            start=1.0,
            end=2.0,
        ),
    ]

    events = [
        make_event(
            index=1,
            start=0.0,
            end=1.0,
            note="A3",
            midi=57,
        ),
        make_event(
            index=2,
            start=1.0,
            end=2.0,
            note="C4",
            midi=60,
        ),
    ]

    result = engine.align(
        make_lyrics(words),
        make_melody(events),
    )

    assert (
        result["lyric_word_count"]
        == 2
    )

    assert (
        result["aligned_word_count"]
        == 2
    )

    assert (
        result["alignment_coverage"]
        == 1.0
    )

    print(
        "TEST 8: Multiple Word Alignment - PASS"
    )


def test_no_auto_correction():

    engine = LyricMelodyAlignment()

    words = [
        make_word(
            index=1,
            text="الأصل",
            start=0.0,
            end=1.0,
        )
    ]

    events = [
        make_event(
            index=1,
            start=0.0,
            end=1.0,
        )
    ]

    result = engine.align(
        make_lyrics(words),
        make_melody(events),
    )

    assert (
        result["no_auto_correction"]
        is True
    )

    assert (
        result["words"][0][
            "text"
        ]
        == "الأصل"
    )

    print(
        "TEST 9: No Auto Correction - PASS"
    )


def test_output_file():

    with tempfile.TemporaryDirectory() as tmp:

        root = Path(tmp)

        lyrics_path = (
            root
            / "lyrics.json"
        )

        melody_path = (
            root
            / "melody.json"
        )

        output_path = (
            root
            / "alignment.json"
        )

        lyrics_path.write_text(
            json.dumps(
                make_lyrics(
                    [
                        make_word()
                    ]
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        melody_path.write_text(
            json.dumps(
                make_melody(
                    [
                        make_event()
                    ]
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        engine = LyricMelodyAlignment()

        result = engine.analyze_file(
            lyrics_path,
            melody_path,
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
            saved["lyric_word_count"]
            == 1
        )

        assert (
            result[
                "aligned_word_count"
            ]
            == 1
        )

    print(
        "TEST 10: Output File - PASS"
    )


def test_invalid_lyrics_timing():

    engine = LyricMelodyAlignment()

    words = [
        make_word(
            start=2.0,
            end=1.0,
        )
    ]

    events = [
        make_event()
    ]

    try:

        engine.align(
            make_lyrics(words),
            make_melody(events),
        )

    except ValueError as exc:

        assert (
            "end_time"
            in str(exc)
        )

    else:

        raise AssertionError(
            "Invalid lyric timing was not rejected."
        )

    print(
        "TEST 11: Invalid Lyric Timing Protection - PASS"
    )


def test_invalid_melody_timing():

    engine = LyricMelodyAlignment()

    words = [
        make_word()
    ]

    events = [
        make_event(
            start=2.0,
            end=1.0,
        )
    ]

    try:

        engine.align(
            make_lyrics(words),
            make_melody(events),
        )

    except ValueError as exc:

        assert (
            "end_time"
            in str(exc)
        )

    else:

        raise AssertionError(
            "Invalid melody timing was not rejected."
        )

    print(
        "TEST 12: Invalid Melody Timing Protection - PASS"
    )


if __name__ == "__main__":

    print("=" * 60)
    print("PhoenixVoiceEngine")
    print("Lyric–Melody Alignment V1.0")
    print("=" * 60)

    test_build()
    test_exact_alignment()
    test_partial_alignment()
    test_multiple_melody_events()
    test_no_overlap()
    test_timing_preservation()
    test_event_order()
    test_multiple_words()
    test_no_auto_correction()
    test_output_file()
    test_invalid_lyrics_timing()
    test_invalid_melody_timing()

    print("=" * 60)
    print("STATUS: PASS")
    print("=" * 60)