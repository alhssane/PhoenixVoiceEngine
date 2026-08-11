"""
PhoenixVoiceEngine
Musical Phrase Analyzer V1.0.1 tests
"""

from src.phrase.musical_phrase_analyzer import MusicalPhraseAnalyzer


def make_event(index, start, end, midi, direction="ASCENDING"):
    return {
        "event_index": index,
        "melody": {
            "midi_note": midi,
            "note_name": "C4",
        },
        "timing": {
            "start_time": start,
            "end_time": end,
            "duration": end - start,
        },
        "pitch": {
            "direction": direction,
            "range_semitones": 1.0,
        },
        "performance": {
            "techniques": {
                "primary": "PITCH_BEND",
                "secondary": [],
            },
        },
        "contour": {
            "raw_preserved": True,
            "points": [
                {"time": start, "midi": float(midi)},
                {"time": end, "midi": float(midi)},
            ],
        },
    }


def make_profile(events):
    return {
        "version": "1.0.0",
        "feature_version": "1.0.0",
        "profile": {
            "event_count": len(events),
            "events": events,
        },
    }


def test_build():
    engine = MusicalPhraseAnalyzer()
    assert engine.VERSION == "1.0.0"
    assert engine.FEATURE_VERSION == "1.0.0"
    assert engine.PATCH_VERSION == "1.0.1"


def test_single_phrase():
    engine = MusicalPhraseAnalyzer()
    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.3, 60),
            make_event(2, 0.31, 0.7, 62),
            make_event(3, 0.71, 1.1, 64),
        ])
    )
    assert result["phrases"]["phrase_count"] == 1


def test_long_silence_split():
    engine = MusicalPhraseAnalyzer()
    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.3, 60),
            make_event(2, 0.4, 0.8, 62),
            make_event(3, 1.7, 2.0, 64),
        ])
    )
    assert result["phrases"]["phrase_count"] == 2


def test_event_gap_split():
    engine = MusicalPhraseAnalyzer(max_event_gap=0.45)
    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.3, 60),
            make_event(2, 0.9, 1.2, 62),
        ])
    )
    assert result["phrases"]["phrase_count"] == 2


def test_max_duration_split():
    engine = MusicalPhraseAnalyzer(max_phrase_duration=1.0)
    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.4, 60),
            make_event(2, 0.4, 0.8, 62),
            make_event(3, 0.8, 1.2, 64),
        ])
    )
    assert result["phrases"]["phrase_count"] == 2


def test_overlap_protection_at_duration_boundary():
    # V1.0.0 could split at the 8-second duration threshold even when
    # the next source event starts before the previous event ends.
    # V1.0.1 must keep the overlapping events in the same phrase.
    engine = MusicalPhraseAnalyzer(
        max_phrase_duration=1.0
    )

    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.8, 60),
            make_event(2, 0.79, 1.2, 62),
            make_event(3, 1.21, 1.5, 64),
        ])
    )

    phrases = result["phrases"]["phrases"]

    assert len(phrases) == 2
    assert [
        event["event_index"]
        for event in phrases[0]["events"]
    ] == [1, 2]


def test_overlap_is_not_corrected():
    engine = MusicalPhraseAnalyzer(
        max_phrase_duration=1.0
    )

    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.8, 60),
            make_event(2, 0.79, 1.2, 62),
        ])
    )

    events = result["phrases"]["phrases"][0]["events"]

    assert events[0]["timing"]["end_time"] == 0.8
    assert events[1]["timing"]["start_time"] == 0.79
    assert events[1]["timing"]["start_time"] < events[0]["timing"]["end_time"]


def test_event_order():
    engine = MusicalPhraseAnalyzer()
    result = engine.analyze(
        make_profile([
            make_event(2, 0.5, 0.8, 62),
            make_event(1, 0.0, 0.3, 60),
        ])
    )
    events = result["phrases"]["phrases"][0]["events"]
    assert [x["event_index"] for x in events] == [1, 2]


def test_timing_preservation():
    engine = MusicalPhraseAnalyzer()
    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.3, 60),
            make_event(2, 0.31, 0.7, 62),
        ])
    )
    events = result["phrases"]["phrases"][0]["events"]
    assert events[0]["timing"]["start_time"] == 0.0
    assert events[0]["timing"]["end_time"] == 0.3
    assert events[1]["timing"]["start_time"] == 0.31


def test_raw_contour_preservation():
    engine = MusicalPhraseAnalyzer()
    profile = make_profile([
        make_event(1, 0.0, 0.3, 60),
    ])
    original = profile["profile"]["events"][0]["contour"]["points"][1]["midi"]

    result = engine.analyze(profile)

    stored = (
        result["phrases"]["phrases"][0]
        ["events"][0]
        ["contour"]["points"][1]["midi"]
    )
    assert stored == original


def test_pitch_jump_not_automatic_split():
    engine = MusicalPhraseAnalyzer(
        max_pitch_jump=2.0
    )
    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.3, 60),
            make_event(2, 0.31, 0.6, 67),
        ])
    )
    assert result["phrases"]["phrase_count"] == 1


def test_no_auto_correction():
    engine = MusicalPhraseAnalyzer()
    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.3, 60),
            make_event(2, 0.31, 0.6, 62),
        ])
    )
    analysis = result["analysis"]
    assert analysis["timing_preserved"] is True
    assert analysis["source_events_preserved"] is True
    assert analysis["raw_contour_preserved"] is True
    assert analysis["no_auto_correction"] is True
    assert analysis["boundary_overlap_protection"] is True


def test_future_analysis_protection():
    engine = MusicalPhraseAnalyzer()
    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.3, 60),
        ])
    )
    assert result["analysis"]["maqam_analysis"] is False
    assert result["analysis"]["arab_analysis"] is False
    assert result["analysis"]["ornament_semantics_analysis"] is False


def test_phrase_structure():
    engine = MusicalPhraseAnalyzer()
    result = engine.analyze(
        make_profile([
            make_event(1, 0.0, 0.3, 60),
            make_event(2, 0.31, 0.7, 62),
        ])
    )
    phrase = result["phrases"]["phrases"][0]
    assert phrase["start_time"] == 0.0
    assert phrase["end_time"] == 0.7
    assert phrase["duration"] == 0.7
    assert phrase["structure"]["midi_min"] == 60
    assert phrase["structure"]["midi_max"] == 62


def run():
    print("PhoenixVoiceEngine")
    print("Musical Phrase Analyzer V1.0.1")
    print("=" * 60)

    tests = [
        test_build,
        test_single_phrase,
        test_long_silence_split,
        test_event_gap_split,
        test_max_duration_split,
        test_overlap_protection_at_duration_boundary,
        test_overlap_is_not_corrected,
        test_event_order,
        test_timing_preservation,
        test_raw_contour_preservation,
        test_pitch_jump_not_automatic_split,
        test_no_auto_correction,
        test_future_analysis_protection,
        test_phrase_structure,
    ]

    for index, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {index}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()