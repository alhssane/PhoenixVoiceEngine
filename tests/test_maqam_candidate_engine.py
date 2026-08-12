"""
PhoenixVoiceEngine
Maqam Candidate Engine V1.0.1
"""

from src.maqam.maqam_candidate_engine import MaqamCandidateEngine


def evidence(distribution, endings, stable_items, stable_count=None):
    if stable_count is None:
        stable_count = len(stable_items)

    return {
        "version": "1.0.0",
        "feature_version": "1.0.0",
        "patch_version": "1.0.1",
        "analysis": {
            "stable_event_count": stable_count,
        },
        "evidence": {
            "pitch_class_distribution": {
                "normalized_duration_distribution": {
                    str(k): v for k, v in distribution.items()
                }
            },
            "stable_note_evidence": {
                "ranked_pitch_classes": [
                    {
                        "pitch_class": pc,
                        "duration": duration,
                    }
                    for pc, duration in stable_items
                ]
            },
            "phrase_endings": [
                {
                    "final_event": {
                        "pitch_class": pc,
                    }
                }
                for pc in endings
            ],
            "phrase_summaries": [
                {"final_pitch_class": pc}
                for pc in endings
            ],
        },
    }


def test_build():
    e = MaqamCandidateEngine()
    assert e.VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.1"


def test_tonic_comes_from_tonic_evidence():
    e = MaqamCandidateEngine()
    r = e.analyze(evidence(
        {0: .20, 2: .10, 4: .10, 5: .10, 7: .35, 9: .05, 11: .10},
        [7, 7, 0, 7],
        [(7, 2.0)],
        12,
    ))
    top = r["ranking"]["top"]
    assert top is not None
    assert top["tonic_name"] == "G"


def test_no_arbitrary_c_tonic():
    e = MaqamCandidateEngine()
    r = e.analyze(evidence(
        {0: .20, 2: .10, 4: .10, 5: .10, 7: .35, 9: .05, 11: .10},
        [7, 7, 0, 7],
        [(7, 2.0)],
        7,
    ))
    for candidate in r["candidates"]:
        assert candidate["tonic_name"] == "G"


def test_weak_tonic_is_uncertain():
    e = MaqamCandidateEngine()
    r = e.analyze(evidence(
        {0: .20, 1: .10, 2: .10, 3: .10, 4: .10, 5: .10, 6: .10, 7: .10, 8: .10},
        [1, 2, 3, 4, 5],
        [(7, .1)],
        1,
    ))
    assert r["decision"]["status"] in {"UNCERTAIN", "AMBIGUOUS"}
    assert r["decision"]["maqam"] is None


def test_low_stable_confidence_cap():
    e = MaqamCandidateEngine()
    r = e.analyze(evidence(
        {7: .70, 9: .10, 11: .10, 0: .10},
        [7, 7, 7, 7],
        [(7, .5)],
        2,
    ))
    top = r["ranking"]["top"]
    assert top is not None
    assert top["confidence"] <= 0.65


def test_ambiguity_is_explicit():
    e = MaqamCandidateEngine()
    r = e.analyze(evidence(
        {0: .20, 1: .15, 3: .15, 5: .15, 7: .15, 8: .10, 10: .10},
        [0, 0, 7, 0],
        [(0, 1.0)],
        20,
    ))
    assert "ambiguous" in r["ranking"]


def test_protection():
    e = MaqamCandidateEngine()
    r = e.analyze(evidence({0: 1.0}, [0], [(0, 1.0)], 1))
    assert r["analysis"]["no_source_correction"] is True
    assert r["analysis"]["no_microtonal_reconstruction"] is True


def run():
    print("PhoenixVoiceEngine")
    print("Maqam Candidate Engine V1.0.1")
    print("=" * 60)

    tests = [
        test_build,
        test_tonic_comes_from_tonic_evidence,
        test_no_arbitrary_c_tonic,
        test_weak_tonic_is_uncertain,
        test_low_stable_confidence_cap,
        test_ambiguity_is_explicit,
        test_protection,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()