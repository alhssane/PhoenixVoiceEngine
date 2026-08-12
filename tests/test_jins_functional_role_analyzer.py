"""
PhoenixVoiceEngine
Jins Functional Role Analyzer V1.0
"""

from src.maqam.jins_functional_role_analyzer import (
    JinsFunctionalRoleAnalyzer,
)


def fixture():
    return {
        "phrases": {
            "phrases": [
                {
                    "phrase_index": 1,
                    "events": [
                        {"midi": 55, "start_time": 0.0, "end_time": 0.5},
                        {"midi": 58, "start_time": 0.5, "end_time": 1.0},
                        {"midi": 55, "start_time": 1.0, "end_time": 1.8},
                    ],
                },
                {
                    "phrase_index": 2,
                    "events": [
                        {"midi": 60, "start_time": 2.0, "end_time": 2.4},
                        {"midi": 55, "start_time": 2.4, "end_time": 3.2},
                    ],
                },
            ]
        }
    }


def test_build():
    assert JinsFunctionalRoleAnalyzer.PATCH_VERSION == "1.0.1"


def test_roles_detected():
    r = JinsFunctionalRoleAnalyzer().analyze(
        fixture(),
        tonic_candidates=[7, 0],
    )
    roles = r["evidence"]["functional_roles"]
    names = {x["pitch_class_name"] for x in roles}
    assert "G" in names
    assert "A#" in names
    assert "C" in names


def test_duration_role():
    r = JinsFunctionalRoleAnalyzer().analyze(fixture())
    g = next(
        x for x in r["evidence"]["functional_roles"]
        if x["pitch_class_name"] == "G"
    )
    assert g["duration"] > 1.0
    assert g["phrase_final_count"] == 2


def test_initial_and_final_roles():
    r = JinsFunctionalRoleAnalyzer().analyze(fixture())
    g = next(
        x for x in r["evidence"]["functional_roles"]
        if x["pitch_class_name"] == "G"
    )
    assert g["phrase_initial_count"] == 1
    assert g["phrase_final_count"] == 2


def test_transitions():
    r = JinsFunctionalRoleAnalyzer().analyze(fixture())
    transitions = r["evidence"]["transition_evidence"]
    pair = next(
        x for x in transitions
        if x["source_pitch_class_name"] == "G"
        and x["target_pitch_class_name"] == "A#"
    )
    assert pair["count"] == 1


def test_tonic_comparison():
    r = JinsFunctionalRoleAnalyzer().analyze(
        fixture(),
        tonic_candidates=[7, 0],
    )
    comparison = r["evidence"]["tonic_role_comparison"]
    assert len(comparison) == 2
    assert comparison[0]["evidence_only"] is True


def test_real_schema_nested_event():
    data = {
        "phrases": {
            "phrases": [{
                "phrase_index": 1,
                "events": [{
                    "event_index": 1,
                    "melody": {
                        "midi_note": 61,
                        "start_time": 0.06,
                        "end_time": 1.54,
                        "duration": 1.48,
                    },
                    "timing": {
                        "start_time": 0.06,
                        "end_time": 1.54,
                        "duration": 1.48,
                    },
                }, {
                    "event_index": 2,
                    "melody": {
                        "midi_note": 55,
                        "start_time": 1.54,
                        "end_time": 2.20,
                        "duration": 0.66,
                    },
                    "timing": {
                        "start_time": 1.54,
                        "end_time": 2.20,
                        "duration": 0.66,
                    },
                }],
            }]
        }
    }
    r = JinsFunctionalRoleAnalyzer().analyze(data, tonic_candidates=[7, 0])
    assert r["input"]["event_count"] == 2
    roles = r["evidence"]["functional_roles"]
    names = {x["pitch_class_name"] for x in roles}
    assert "C#" in names
    assert "G" in names


def test_protection():
    r = JinsFunctionalRoleAnalyzer().analyze(fixture())
    assert r["analysis"]["source_pitch_modified"] is False
    assert r["analysis"]["source_timing_modified"] is False
    assert r["analysis"]["maqam_decision_made"] is False


def test_no_decision():
    r = JinsFunctionalRoleAnalyzer().analyze(fixture())
    assert r["decision"]["status"] == "EVIDENCE_ONLY"
    assert r["decision"]["maqam"] is None
    assert r["decision"]["jins"] is None


def run():
    print("PhoenixVoiceEngine")
    print("Jins Functional Role Analyzer V1.0")
    print("=" * 60)

    tests = [
        test_build,
        test_roles_detected,
        test_duration_role,
        test_initial_and_final_roles,
        test_transitions,
        test_tonic_comparison,
        test_real_schema_nested_event,
        test_protection,
        test_no_decision,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()
