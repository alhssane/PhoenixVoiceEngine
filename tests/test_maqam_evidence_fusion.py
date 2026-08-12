"""
PhoenixVoiceEngine
Maqam Evidence Fusion V1.0.2
"""

from src.maqam.maqam_evidence_fusion import MaqamEvidenceFusion


def make_candidates():
    return {
        "candidates": [
            {
                "maqam": "BAYATI",
                "tonic_pitch_class": 7,
                "tonic_name": "G",
                "score": 0.613085,
                "confidence": 0.521122,
            },
            {
                "maqam": "KURD",
                "tonic_pitch_class": 7,
                "tonic_name": "G",
                "score": 0.613085,
                "confidence": 0.521122,
            },
            {
                "maqam": "NAHAWAND",
                "tonic_pitch_class": 7,
                "tonic_name": "G",
                "score": 0.588589,
                "confidence": 0.500301,
            },
        ],
        "decision": {
            "status": "AMBIGUOUS",
            "maqam": None,
            "tonic_name": None,
            "confidence": 0.521122,
        },
    }


def make_evidence():
    return {
        "decision": {"status": "EVIDENCE_ONLY"},
        "evidence": {
            "cadences": {
                "cadences": [
                    {
                        "final_pitch_class": 7,
                        "window_pitch_classes": [10, 7, 7],
                    },
                    {
                        "final_pitch_class": 7,
                        "window_pitch_classes": [2, 10, 7],
                    },
                    {
                        "final_pitch_class": 0,
                        "window_pitch_classes": [10, 0, 0],
                    },
                    {
                        "final_pitch_class": 2,
                        "window_pitch_classes": [7, 2, 2],
                    },
                ],
                "final_pitch_class_counts": {
                    "7": 2,
                    "0": 1,
                    "2": 1,
                },
            },
            "stable_transitions": {
                "ranked_pairs": [
                    {
                        "source_pitch_class": 10,
                        "target_pitch_class": 7,
                        "count": 23,
                    },
                    {
                        "source_pitch_class": 0,
                        "target_pitch_class": 10,
                        "count": 20,
                    },
                    {
                        "source_pitch_class": 2,
                        "target_pitch_class": 10,
                        "count": 18,
                    },
                    {
                        "source_pitch_class": 7,
                        "target_pitch_class": 2,
                        "count": 9,
                    },
                ],
            },
        },
    }


def test_build():
    assert MaqamEvidenceFusion.PATCH_VERSION == "1.0.2"


def test_fusion_builds():
    result = MaqamEvidenceFusion().fuse(
        make_candidates(),
        make_evidence(),
    )
    assert len(result["ranking"]["candidates"]) == 3
    assert "fused_score" in result["ranking"]["candidates"][0]


def test_original_score_preserved():
    result = MaqamEvidenceFusion().fuse(
        make_candidates(),
        make_evidence(),
    )
    top = result["ranking"]["candidates"][0]
    assert top["original_candidate_score"] == 0.613085
    assert 0 <= top["fused_score"] <= 1


def test_cadence_evidence_present():
    result = MaqamEvidenceFusion().fuse(
        make_candidates(),
        make_evidence(),
    )
    top = result["ranking"]["candidates"][0]
    assert "cadence" in top["new_evidence"]
    assert top["new_evidence"]["cadence"]["cadence_count"] == 4


def test_bayati_kurd_coarse_limit():
    result = MaqamEvidenceFusion().fuse(
        make_candidates(),
        make_evidence(),
    )
    ranked = result["ranking"]["candidates"]
    bayati = next(x for x in ranked if x["maqam"] == "BAYATI")
    kurd = next(x for x in ranked if x["maqam"] == "KURD")

    # Same tonic + same coarse 12-TET scale representation means this layer
    # must not pretend to distinguish them by scale compatibility.
    assert (
        bayati["new_evidence"]["transition"]["score"]
        == kurd["new_evidence"]["transition"]["score"]
    )


def test_protection():
    result = MaqamEvidenceFusion().fuse(
        make_candidates(),
        make_evidence(),
    )
    protection = result["protection"]
    assert protection["source_pitch_modified"] is False
    assert protection["source_timing_modified"] is False
    assert protection["source_performance_modified"] is False
    assert protection["original_candidate_decision_overridden"] is False
    assert protection["microtonal_claim_from_12tet"] is False


def test_original_ambiguity_is_protected():
    result = MaqamEvidenceFusion(
        ambiguity_margin=0.0
    ).fuse(
        make_candidates(),
        make_evidence(),
    )
    # With equal original Bayati/Kurd scores and equal coarse evidence,
    # the system must not invent a winner.
    assert result["decision"]["status"] in {
        "AMBIGUOUS",
        "LEADING_CANDIDATE_NOT_CONFIRMED",
    }


def run():
    print("PhoenixVoiceEngine")
    print("Maqam Evidence Fusion V1.0.2")
    print("=" * 60)

    tests = [
        test_build,
        test_fusion_builds,
        test_original_score_preserved,
        test_cadence_evidence_present,
        test_bayati_kurd_coarse_limit,
        test_protection,
        test_original_ambiguity_is_protected,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()
