"""
PhoenixVoiceEngine
Maqam Evidence Analyzer V1.0.1
"""

from src.maqam.maqam_evidence_analyzer import MaqamEvidenceAnalyzer


def event(
    index,
    start,
    end,
    midi,
    pitch_range=0.1,
    max_deviation=0.1,
    technique="NATURAL_VARIATION",
):
    return {
        "event_index": index,
        "start_time": start,
        "end_time": end,
        "duration": end - start,
        "melody": {"midi_note": midi},
        "pitch": {
            "range_semitones": pitch_range,
            "max_deviation_semitones": max_deviation,
        },
        "techniques": {
            "dominant_type": technique,
        },
    }


def phrase(index, events):
    return {
        "phrase_index": index,
        "start_time": events[0]["start_time"],
        "end_time": events[-1]["end_time"],
        "duration": events[-1]["end_time"] - events[0]["start_time"],
        "events": events,
    }


def data(phrases):
    return {
        "version": "1.0.0",
        "feature_version": "1.0.0",
        "patch_version": "1.0.1",
        "phrases": {"phrases": phrases},
    }


def test_build():
    e = MaqamEvidenceAnalyzer()
    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.1"


def test_real_performance_stability_source():
    e = MaqamEvidenceAnalyzer()
    r = e.analyze(data([
        phrase(1, [
            event(1, 0.0, 1.0, 60),
            event(2, 1.0, 2.0, 62, 0.2, 0.2),
        ])
    ]))
    stable = r["evidence"]["stable_note_evidence"]
    assert stable["stable_event_count"] == 2
    assert stable["ranked_pitch_classes"][0]["pitch_class"] in [0, 2]


def test_movement_technique_not_stable():
    e = MaqamEvidenceAnalyzer()
    r = e.analyze(data([
        phrase(1, [
            event(
                1, 0.0, 1.0, 60,
                pitch_range=0.1,
                max_deviation=0.1,
                technique="VIBRATO",
            ),
        ])
    ]))
    assert r["analysis"]["stable_event_count"] == 0


def test_pitch_class_distribution():
    e = MaqamEvidenceAnalyzer()
    r = e.analyze(data([
        phrase(1, [
            event(1, 0.0, 2.0, 60),
            event(2, 2.0, 3.0, 62),
        ])
    ]))
    d = r["evidence"]["pitch_class_distribution"]
    assert d["duration_by_pitch_class"]["0"] == 2.0
    assert d["duration_by_pitch_class"]["2"] == 1.0


def test_phrase_endings():
    e = MaqamEvidenceAnalyzer()
    r = e.analyze(data([
        phrase(1, [
            event(1, 0.0, 1.0, 60),
            event(2, 1.0, 2.0, 62),
            event(3, 2.0, 3.0, 60),
        ])
    ]))
    endings = r["evidence"]["phrase_endings"]
    assert endings[0]["final_event"]["pitch_class"] == 0


def test_intervals():
    e = MaqamEvidenceAnalyzer()
    r = e.analyze(data([
        phrase(1, [
            event(1, 0.0, 1.0, 60),
            event(2, 1.0, 2.0, 64),
            event(3, 2.0, 3.0, 62),
        ])
    ]))
    assert r["evidence"]["interval_evidence"]["semitone_deltas"] == [
        4.0, -2.0
    ]


def test_timing_unchanged():
    e = MaqamEvidenceAnalyzer()
    r = e.analyze(data([
        phrase(1, [
            event(1, 0.0, 0.79, 60),
            event(2, 0.78, 1.20, 62),
        ])
    ]))
    x = r["evidence"]["event_evidence"]
    assert x[0]["end_time"] == 0.79
    assert x[1]["start_time"] == 0.78


def test_evidence_only():
    e = MaqamEvidenceAnalyzer()
    r = e.analyze(data([]))
    assert r["decision"]["status"] == "EVIDENCE_ONLY"
    assert r["decision"]["maqam"] is None
    assert r["decision"]["jins"] is None
    assert r["decision"]["confidence"] is None


def test_protection_flags():
    e = MaqamEvidenceAnalyzer()
    r = e.analyze(data([]))
    a = r["analysis"]
    assert a["raw_pitch_preserved"] is True
    assert a["timing_preserved"] is True
    assert a["no_pitch_correction"] is True
    assert a["no_microtonal_quantization"] is True
    assert a["no_maqam_decision"] is True
    assert a["no_jins_decision"] is True
    assert a["no_sayr_decision"] is True


def run():
    print("PhoenixVoiceEngine")
    print("Maqam Evidence Analyzer V1.0.1")
    print("=" * 60)

    tests = [
        test_build,
        test_real_performance_stability_source,
        test_movement_technique_not_stable,
        test_pitch_class_distribution,
        test_phrase_endings,
        test_intervals,
        test_timing_unchanged,
        test_evidence_only,
        test_protection_flags,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()