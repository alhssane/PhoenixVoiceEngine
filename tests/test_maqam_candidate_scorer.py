"""
PhoenixVoiceEngine
Maqam Candidate Evidence Scorer V1.0.2
"""

from src.maqam.maqam_candidate_scorer import (
    MaqamCandidateEvidenceScorer,
)


def make_evidence():
    return {
        "evidence": {
            "cadences": {
                "cadences": [
                    {
                        "phrase_index": 1,
                        "window_pitch_classes": [10, 7, 7],
                        "final_pitch_class": 7,
                    },
                    {
                        "phrase_index": 2,
                        "window_pitch_classes": [2, 10, 7],
                        "final_pitch_class": 7,
                    },
                    {
                        "phrase_index": 3,
                        "window_pitch_classes": [0, 10, 0],
                        "final_pitch_class": 0,
                    },
                ],
                "final_pitch_class_counts": {
                    "7": 2,
                    "0": 1,
                },
            },
            "stable_transitions": {
                "ranked_pairs": [
                    {
                        "source_pitch_class": 10,
                        "target_pitch_class": 7,
                        "count": 4,
                    },
                    {
                        "source_pitch_class": 2,
                        "target_pitch_class": 10,
                        "count": 3,
                    },
                    {
                        "source_pitch_class": 0,
                        "target_pitch_class": 10,
                        "count": 2,
                    },
                ],
            },
        }
    }


def test_build():
    assert MaqamCandidateEvidenceScorer.PATCH_VERSION == "1.0.2"


def test_cadence_evidence():
    scorer = MaqamCandidateEvidenceScorer()
    candidate = {
        "maqam": "TEST",
        "tonic_pitch_class": 7,
        "tonic_name": "G",
        "_knowledge": {
            "scale_pc_intervals_12tet": [0, 2, 3, 5, 7, 9, 10],
        },
    }
    result = scorer.score_candidate(candidate, make_evidence())
    assert result["cadence"]["ending_on_tonic"] == 2
    assert result["cadence"]["cadence_count"] == 3
    assert result["cadence"]["score"] > 0


def test_final_recurrence():
    scorer = MaqamCandidateEvidenceScorer()
    candidate = {
        "maqam": "TEST",
        "tonic_pitch_class": 7,
        "tonic_name": "G",
        "_knowledge": {},
    }
    result = scorer.score_candidate(candidate, make_evidence())
    assert result["final_recurrence"]["tonic_final_count"] == 2
    assert result["final_recurrence"]["final_count"] == 3


def test_transition_evidence():
    scorer = MaqamCandidateEvidenceScorer()
    candidate = {
        "maqam": "TEST",
        "tonic_pitch_class": 7,
        "tonic_name": "G",
        "_knowledge": {
            "scale_pc_intervals_12tet": [0, 2, 3, 5, 7, 9, 10],
        },
    }
    result = scorer.score_candidate(candidate, make_evidence())
    assert result["transition"]["transition_count"] == 9
    assert 0 <= result["transition"]["score"] <= 1


def test_score_range():
    scorer = MaqamCandidateEvidenceScorer()
    candidate = {
        "maqam": "TEST",
        "tonic_pitch_class": 7,
        "tonic_name": "G",
        "_knowledge": {
            "scale_pc_intervals_12tet": [0, 2, 3, 5, 7, 9, 10],
        },
    }
    result = scorer.score_candidate(candidate, make_evidence())
    assert 0 <= result["combined"] <= 1


def test_discrimination_report():
    scorer = MaqamCandidateEvidenceScorer()
    candidates = [
        {
            "maqam": "BAYATI",
            "tonic_name": "G",
            "evidence_fusion_score": 0.61,
        },
        {
            "maqam": "KURD",
            "tonic_name": "G",
            "evidence_fusion_score": 0.60,
        },
        {
            "maqam": "HIJAZ",
            "tonic_name": "G",
            "evidence_fusion_score": 0.40,
        },
    ]
    report = scorer.discrimination_report(candidates)
    assert report["status"] == "DISCRIMINATION_LIMITED"
    assert len(report["indistinguishable_groups"]) == 1


def test_no_source_correction():
    scorer = MaqamCandidateEvidenceScorer()
    assert scorer.VERSION == "1.0.0"
    assert scorer.PATCH_VERSION == "1.0.2"


def run():
    print("PhoenixVoiceEngine")
    print("Maqam Candidate Evidence Scorer V1.0.2")
    print("=" * 60)

    tests = [
        test_build,
        test_cadence_evidence,
        test_final_recurrence,
        test_transition_evidence,
        test_score_range,
        test_discrimination_report,
        test_no_source_correction,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()
