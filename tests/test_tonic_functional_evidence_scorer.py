"""
PhoenixVoiceEngine
Tonic Functional Evidence Scorer V1.0
"""

from src.maqam.tonic_functional_evidence_scorer import (
    TonicFunctionalEvidenceScorer,
)


def functional_fixture():
    return {
        "version": "1.0.0",
        "input": {"phrase_count": 10, "event_count": 100},
        "evidence": {
            "functional_roles": [
                {
                    "pitch_class": 7,
                    "pitch_class_name": "G",
                    "event_count": 20,
                    "duration": 20.0,
                    "event_recurrence": 0.20,
                    "duration_share": 0.20,
                    "phrase_initial_count": 3,
                    "phrase_initial_ratio": 0.30,
                    "phrase_final_count": 6,
                    "phrase_final_ratio": 0.60,
                },
                {
                    "pitch_class": 0,
                    "pitch_class_name": "C",
                    "event_count": 30,
                    "duration": 30.0,
                    "event_recurrence": 0.30,
                    "duration_share": 0.30,
                    "phrase_initial_count": 2,
                    "phrase_initial_ratio": 0.20,
                    "phrase_final_count": 2,
                    "phrase_final_ratio": 0.20,
                },
            ],
            "transition_evidence": [
                {
                    "source_pitch_class": 10,
                    "target_pitch_class": 7,
                    "count": 8,
                },
                {
                    "source_pitch_class": 7,
                    "target_pitch_class": 7,
                    "count": 8,
                },
                {
                    "source_pitch_class": 7,
                    "target_pitch_class": 2,
                    "count": 4,
                },
                {
                    "source_pitch_class": 0,
                    "target_pitch_class": 0,
                    "count": 3,
                },
                {
                    "source_pitch_class": 2,
                    "target_pitch_class": 0,
                    "count": 4,
                },
            ],
        },
    }


def stable_fixture():
    return {
        "evidence": {
            "stable_pitch_centers": [
                {
                    "pitch_class": 7,
                    "region_count": 80,
                    "total_duration": 30.0,
                    "mean_stability_score": 0.75,
                },
                {
                    "pitch_class": 0,
                    "region_count": 90,
                    "total_duration": 35.0,
                    "mean_stability_score": 0.70,
                },
            ]
        }
    }


def cadence_fixture():
    return {
        "evidence": {
            "cadences": {
                "final_pitch_class_counts": {
                    "7": 6,
                    "0": 2,
                }
            }
        }
    }


def test_build():
    assert TonicFunctionalEvidenceScorer.PATCH_VERSION == "1.0.0"


def test_candidate_generation():
    r = TonicFunctionalEvidenceScorer().analyze(
        functional_fixture(),
        stable_data=stable_fixture(),
        cadence_data=cadence_fixture(),
        candidates=[7, 0],
    )
    assert len(r["ranking"]["candidates"]) == 2


def test_g_has_stronger_functional_score():
    r = TonicFunctionalEvidenceScorer().analyze(
        functional_fixture(),
        stable_data=stable_fixture(),
        cadence_data=cadence_fixture(),
        candidates=[7, 0],
    )
    top = r["ranking"]["top"]
    assert top["tonic_name"] == "G"


def test_components_present():
    r = TonicFunctionalEvidenceScorer().analyze(
        functional_fixture(),
        stable_data=stable_fixture(),
        cadence_data=cadence_fixture(),
        candidates=[7, 0],
    )
    components = r["ranking"]["top"]["components"]
    for key in (
        "cadence_evidence",
        "final_strength",
        "initial_strength",
        "local_stability",
        "approach_evidence",
        "stable_center_evidence",
    ):
        assert key in components


def test_margin():
    r = TonicFunctionalEvidenceScorer().analyze(
        functional_fixture(),
        stable_data=stable_fixture(),
        cadence_data=cadence_fixture(),
        candidates=[7, 0],
    )
    assert r["ranking"]["margin"] > 0


def test_score_range():
    r = TonicFunctionalEvidenceScorer().analyze(
        functional_fixture(),
        stable_data=stable_fixture(),
        cadence_data=cadence_fixture(),
        candidates=[7, 0],
    )
    for x in r["ranking"]["candidates"]:
        assert 0.0 <= x["score"] <= 1.0


def test_evidence_only():
    r = TonicFunctionalEvidenceScorer().analyze(
        functional_fixture(),
        stable_data=stable_fixture(),
        cadence_data=cadence_fixture(),
        candidates=[7, 0],
    )
    assert r["decision"]["status"] == "EVIDENCE_ONLY"
    assert r["decision"]["tonic_name"] is None
    assert r["decision"]["maqam"] is None


def test_protection():
    r = TonicFunctionalEvidenceScorer().analyze(
        functional_fixture(),
        stable_data=stable_fixture(),
        cadence_data=cadence_fixture(),
        candidates=[7, 0],
    )
    p = r["protection"]
    assert p["source_pitch_modified"] is False
    assert p["source_timing_modified"] is False
    assert p["tonic_decision_made"] is False
    assert p["maqam_decision_made"] is False


def run():
    print("PhoenixVoiceEngine")
    print("Tonic Functional Evidence Scorer V1.0")
    print("=" * 60)

    tests = [
        test_build,
        test_candidate_generation,
        test_g_has_stronger_functional_score,
        test_components_present,
        test_margin,
        test_score_range,
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
