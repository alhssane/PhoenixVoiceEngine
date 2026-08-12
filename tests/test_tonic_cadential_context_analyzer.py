"""
PhoenixVoiceEngine
Tonic Cadential Context Analyzer V1.0
"""

from src.maqam.tonic_cadential_context_analyzer import (
    TonicCadentialContextAnalyzer,
)


def fixture():
    return {
        "phrases": {
            "phrases": [
                {
                    "phrase_index": 1,
                    "events": [
                        {"melody": {"midi_note": 60}},
                        {"melody": {"midi_note": 58}},
                        {"melody": {"midi_note": 55}},
                    ],
                },
                {
                    "phrase_index": 2,
                    "events": [
                        {"melody": {"midi_note": 62}},
                        {"melody": {"midi_note": 58}},
                        {"melody": {"midi_note": 55}},
                    ],
                },
                {
                    "phrase_index": 3,
                    "events": [
                        {"melody": {"midi_note": 60}},
                        {"melody": {"midi_note": 55}},
                    ],
                },
                {
                    "phrase_index": 4,
                    "events": [
                        {"melody": {"midi_note": 60}},
                        {"melody": {"midi_note": 62}},
                    ],
                },
            ]
        }
    }


def test_build():
    assert TonicCadentialContextAnalyzer.PATCH_VERSION == "1.0.0"


def test_candidate_generation():
    r = TonicCadentialContextAnalyzer().analyze(
        fixture(),
        candidates=[7, 0],
    )
    assert len(r["ranking"]["candidates"]) == 2


def test_g_endings_detected():
    r = TonicCadentialContextAnalyzer().analyze(
        fixture(),
        candidates=[7, 0],
    )
    g = next(
        x for x in r["ranking"]["candidates"]
        if x["tonic_name"] == "G"
    )
    assert g["ending_phrase_count"] == 3


def test_c_endings_detected():
    r = TonicCadentialContextAnalyzer().analyze(
        fixture(),
        candidates=[7, 0],
    )
    c = next(
        x for x in r["ranking"]["candidates"]
        if x["tonic_name"] == "C"
    )
    assert c["ending_phrase_count"] == 0


def test_recurring_context():
    r = TonicCadentialContextAnalyzer().analyze(
        fixture(),
        candidates=[7],
    )
    g = r["ranking"]["top"]
    assert len(g["recurring_contexts"]) >= 1
    assert g["recurring_contexts"][0]["count"] >= 2


def test_penultimate():
    r = TonicCadentialContextAnalyzer().analyze(
        fixture(),
        candidates=[7],
    )
    g = r["ranking"]["top"]
    # A# is the penultimate note in two of the G-ending phrases.
    assert g["penultimate_pitch_class_names"].get("A#", 0) == 2


def test_context_widths():
    r = TonicCadentialContextAnalyzer().analyze(
        fixture(),
        candidates=[7],
        context_widths=(2, 3, 4),
    )
    contexts = r["evidence"]["phrase_contexts_by_candidate"]["7"]
    assert contexts
    assert "2" in contexts[0]["windows"]
    assert "3" in contexts[0]["windows"]


def test_evidence_only():
    r = TonicCadentialContextAnalyzer().analyze(
        fixture(),
        candidates=[7, 0],
    )
    assert r["decision"]["status"] == "EVIDENCE_ONLY"
    assert r["decision"]["tonic_name"] is None
    assert r["decision"]["maqam"] is None


def test_protection():
    r = TonicCadentialContextAnalyzer().analyze(
        fixture(),
        candidates=[7, 0],
    )
    p = r["protection"]
    assert p["source_pitch_modified"] is False
    assert p["source_timing_modified"] is False
    assert p["tonic_decision_made"] is False
    assert p["maqam_decision_made"] is False


def run():
    print("PhoenixVoiceEngine")
    print("Tonic Cadential Context Analyzer V1.0")
    print("=" * 60)

    tests = [
        test_build,
        test_candidate_generation,
        test_g_endings_detected,
        test_c_endings_detected,
        test_recurring_context,
        test_penultimate,
        test_context_widths,
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
