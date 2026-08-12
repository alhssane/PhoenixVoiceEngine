"""
PhoenixVoiceEngine
Jins & Cadence Evidence Analyzer V1.0.2
"""

from src.maqam.jins_cadence_evidence_analyzer import JinsCadenceEvidenceAnalyzer


def make_phrase_data():
    events = [
        {
            "event_index": 1,
            "melody": {"midi_note": 55, "midi_mean": 55.0},
            "timing": {"start_time": 0.0, "end_time": 1.0},
        },
        {
            "event_index": 2,
            "melody": {"midi_note": 57, "midi_mean": 57.0},
            "timing": {"start_time": 1.0, "end_time": 2.0},
        },
        {
            "event_index": 3,
            "melody": {"midi_note": 59, "midi_mean": 59.0},
            "timing": {"start_time": 2.0, "end_time": 3.0},
        },
        {
            "event_index": 4,
            "melody": {"midi_note": 62, "midi_mean": 62.0},
            "timing": {"start_time": 3.0, "end_time": 4.0},
        },
        {
            "event_index": 5,
            "melody": {"midi_note": 60, "midi_mean": 60.0},
            "timing": {"start_time": 4.0, "end_time": 5.0},
        },
    ]

    return {
        "phrases": {
            "event_count": 5,
            "phrase_count": 1,
            "duration": 5.0,
            "phrases": [{
                "phrase_index": 1,
                "start_time": 0.0,
                "end_time": 5.0,
                "duration": 5.0,
                "events": events,
            }],
        }
    }


def test_build():
    assert JinsCadenceEvidenceAnalyzer().VERSION == "1.0.0"


def test_real_schema_midi_note():
    r = JinsCadenceEvidenceAnalyzer().analyze(make_phrase_data())
    assert r["input"]["event_count"] == 5


def test_intervals():
    r = JinsCadenceEvidenceAnalyzer().analyze(make_phrase_data())
    intervals = r["evidence"]["intervals"]
    assert intervals["transition_count"] == 4
    assert intervals["interval_counts"]["2"] == 3
    assert intervals["interval_counts"]["3"] == 1


def test_directions():
    r = JinsCadenceEvidenceAnalyzer().analyze(make_phrase_data())
    directed = r["evidence"]["intervals"]["directed_interval_counts"]
    assert directed["ASCENDING:2"] == 2
    assert directed["ASCENDING:3"] == 1
    assert directed["DESCENDING:2"] == 1


def test_cadence_window():
    r = JinsCadenceEvidenceAnalyzer(cadence_window=3).analyze(make_phrase_data())
    c = r["evidence"]["cadences"]["cadences"][0]
    assert c["window_pitch_classes"] == [11, 2, 0]
    assert c["final_pitch_class"] == 0


def test_transition_pairs():
    r = JinsCadenceEvidenceAnalyzer().analyze(make_phrase_data())
    pairs = r["evidence"]["stable_transitions"]["ranked_pairs"]
    assert pairs[0]["count"] >= 1


def test_evidence_only():
    r = JinsCadenceEvidenceAnalyzer().analyze(make_phrase_data())
    assert r["decision"]["status"] == "EVIDENCE_ONLY"
    assert r["decision"]["maqam"] is None
    assert r["decision"]["jins"] is None
    assert r["decision"]["confidence"] is None


def test_protection():
    r = JinsCadenceEvidenceAnalyzer().analyze(make_phrase_data())
    assert r["analysis"]["source_timing_preserved"] is True
    assert r["analysis"]["source_pitch_preserved"] is True
    assert r["analysis"]["no_auto_correction"] is True
    assert r["analysis"]["no_maqam_decision"] is True


def run():
    print("PhoenixVoiceEngine")
    print("Jins & Cadence Evidence Analyzer V1.0.2")
    print("=" * 60)

    tests = [
        test_build,
        test_real_schema_midi_note,
        test_intervals,
        test_directions,
        test_cadence_window,
        test_transition_pairs,
        test_evidence_only,
        test_protection,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()
