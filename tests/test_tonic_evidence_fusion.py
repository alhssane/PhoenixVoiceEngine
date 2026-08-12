from src.maqam.tonic_evidence_fusion import TonicEvidenceFusion


def run():
    print("PhoenixVoiceEngine")
    print("Tonic Evidence Fusion V1.0")
    print("=" * 60)

    tests = [
        test_build,
        test_fusion_builds,
        test_original_scores_preserved_as_inputs,
        test_cadential_evidence_present,
        test_stable_center_evidence_present,
        test_score_range,
        test_evidence_only,
        test_protection,
    ]

    for i, fn in enumerate(tests, 1):
        fn()
        print(f"TEST {i}: {fn.__name__} - PASS")

    print("=" * 60)
    print("STATUS: PASS")


def make_analyzer():
    return TonicEvidenceFusion()


def make_functional():
    return {
        "ranking": {
            "candidates": [
                {
                    "tonic_pitch_class": 7,
                    "score": 0.40,
                },
                {
                    "tonic_pitch_class": 0,
                    "score": 0.37,
                },
            ]
        }
    }


def make_cadential():
    return {
        "ranking": {
            "candidates": [
                {
                    "tonic_pitch_class": 7,
                    "cadential_context_score": 0.59,
                },
                {
                    "tonic_pitch_class": 0,
                    "cadential_context_score": 0.54,
                },
            ]
        }
    }


def make_stable():
    return {
        "evidence": {
            "stable_pitch_centers": [
                {
                    "pitch_class": 7,
                    "total_duration": 31.25,
                    "mean_stability_score": 0.73,
                },
                {
                    "pitch_class": 0,
                    "total_duration": 45.96,
                    "mean_stability_score": 0.91,
                },
            ]
        }
    }


def make_raw():
    return {
        "evidence": {
            "microtonal": {
                "available": True,
                "nontrivial_cents_ratio": 0.885,
            },
            "tonic_relative": {
                "available": True,
                "bins_25_cents": {
                    "0.00": 0.025,
                    "0.25": 0.015,
                    "0.50": 0.023,
                    "11.75": 0.049,
                },
            },
        }
    }


def test_build():
    assert TonicEvidenceFusion.VERSION == "1.0.0"
    assert TonicEvidenceFusion.FEATURE_VERSION == "1.0.0"
    assert TonicEvidenceFusion.PATCH_VERSION == "1.0.0"


def test_fusion_builds():
    e = make_analyzer()

    r = e.analyze(
        make_functional(),
        make_cadential(),
        make_stable(),
        make_raw(),
        candidates=[7, 0],
    )

    assert len(r["ranking"]["candidates"]) == 2
    assert r["ranking"]["top"] is not None


def test_original_scores_preserved_as_inputs():
    e = make_analyzer()

    r = e.analyze(
        make_functional(),
        make_cadential(),
        make_stable(),
        make_raw(),
        candidates=[7, 0],
    )

    g = r["ranking"]["candidates"][0]

    assert "functional" in g["components"]
    assert "cadential" in g["components"]


def test_cadential_evidence_present():
    e = make_analyzer()

    r = e.analyze(
        make_functional(),
        make_cadential(),
        make_stable(),
        make_raw(),
        candidates=[7, 0],
    )

    for x in r["ranking"]["candidates"]:
        assert "cadential" in x["components"]


def test_stable_center_evidence_present():
    e = make_analyzer()

    r = e.analyze(
        make_functional(),
        make_cadential(),
        make_stable(),
        make_raw(),
        candidates=[7, 0],
    )

    for x in r["ranking"]["candidates"]:
        assert "stable_center" in x["components"]


def test_score_range():
    e = make_analyzer()

    r = e.analyze(
        make_functional(),
        make_cadential(),
        make_stable(),
        make_raw(),
        candidates=[7, 0],
    )

    for x in r["ranking"]["candidates"]:
        assert 0.0 <= x["fused_score"] <= 1.0


def test_evidence_only():
    e = make_analyzer()

    r = e.analyze(
        make_functional(),
        make_cadential(),
        make_stable(),
        make_raw(),
        candidates=[7, 0],
    )

    assert r["decision"]["status"] == "EVIDENCE_ONLY"
    assert r["decision"]["tonic_pitch_class"] is None
    assert r["decision"]["tonic_name"] is None
    assert r["decision"]["maqam"] is None
    assert r["decision"]["jins"] is None


def test_protection():
    e = make_analyzer()

    r = e.analyze(
        make_functional(),
        make_cadential(),
        make_stable(),
        make_raw(),
        candidates=[7, 0],
    )

    protection = r["protection"]

    assert protection["source_pitch_modified"] is False
    assert protection["source_timing_modified"] is False
    assert protection["source_performance_modified"] is False
    assert protection["tonic_decision_made"] is False
    assert protection["maqam_decision_made"] is False
    assert protection["jins_decision_made"] is False


if __name__ == "__main__":
    run()