from src.maqam.tonic_evidence_calibration import (
    TonicEvidenceCalibration,
)


def make_analyzer():
    return TonicEvidenceCalibration()


def make_fusion():
    return {
        "decision": {
            "status": "EVIDENCE_ONLY",
            "tonic_pitch_class": None,
            "tonic_name": None,
            "maqam": None,
            "jins": None,
        },
        "ranking": {
            "candidates": [
                {
                    "tonic_pitch_class": 7,
                    "tonic_name": "G",
                    "fused_score": 0.586530,
                    "components": {
                        "functional": 0.400760,
                        "cadential": 0.591304,
                        "stable_center": 0.646084,
                        "microtonal": 0.885423,
                        "tonic_relative": 0.089706,
                        "intervallic_relationship": 0.774768,
                    },
                    "evidence_only": True,
                },
                {
                    "tonic_pitch_class": 0,
                    "tonic_name": "C",
                    "fused_score": 0.589766,
                    "components": {
                        "functional": 0.369567,
                        "cadential": 0.538975,
                        "stable_center": 0.700404,
                        "microtonal": 0.885423,
                        "tonic_relative": 0.089706,
                        "intervallic_relationship": 0.821936,
                    },
                    "evidence_only": True,
                },
            ]
        },
    }


def test_build():
    assert (
        TonicEvidenceCalibration.VERSION
        == "1.0.0"
    )

    assert (
        TonicEvidenceCalibration.FEATURE_VERSION
        == "1.0.0"
    )

    assert (
        TonicEvidenceCalibration.PATCH_VERSION
        == "1.0.0"
    )


def test_component_extraction():
    e = make_analyzer()

    candidates = e._extract_candidates(
        make_fusion()
    )

    assert len(candidates) == 2

    components = e._extract_components(
        candidates[0]
    )

    assert len(components) == 6

    assert (
        components["functional"]
        == 0.400760
    )

    assert (
        components[
            "intervallic_relationship"
        ]
        == 0.774768
    )


def test_supporting_evidence():
    e = make_analyzer()

    candidates = e._extract_candidates(
        make_fusion()
    )

    result = e._supporting_evidence(
        candidates[0],
        candidates[1],
    )

    assert "functional" in (
        result["first"]
    )

    assert "cadential" in (
        result["first"]
    )

    assert (
        "stable_center"
        in result["second"]
    )

    assert (
        "intervallic_relationship"
        in result["second"]
    )


def test_opposing_evidence():
    e = make_analyzer()

    candidates = e._extract_candidates(
        make_fusion()
    )

    result = e._opposing_evidence(
        candidates[0],
        candidates[1],
    )

    assert isinstance(
        result["first"],
        list,
    )

    assert isinstance(
        result["second"],
        list,
    )


def test_agreement_score():
    e = make_analyzer()

    candidates = e._extract_candidates(
        make_fusion()
    )

    score = e._agreement_score(
        candidates[0],
        candidates[1],
    )

    assert (
        0.0
        <= score
        <= 1.0
    )


def test_conflict_score():
    e = make_analyzer()

    candidates = e._extract_candidates(
        make_fusion()
    )

    score = e._conflict_score(
        candidates[0],
        candidates[1],
    )

    assert (
        0.0
        <= score
        <= 1.0
    )

    assert score > 0.0


def test_evidence_spread():
    e = make_analyzer()

    candidates = e._extract_candidates(
        make_fusion()
    )

    spread = e._evidence_spread(
        candidates[0]
    )

    assert (
        0.0
        <= spread
        <= 1.0
    )

    assert spread > 0.0


def test_statistics():
    e = make_analyzer()

    candidates = e._extract_candidates(
        make_fusion()
    )

    result = e._candidate_statistics(
        candidates[0]
    )

    assert (
        0.0
        <= result["evidence_mean"]
        <= 1.0
    )

    assert (
        result["evidence_std"]
        >= 0.0
    )

    assert (
        0.0
        <= result["evidence_spread"]
        <= 1.0
    )

    assert (
        result["strongest_evidence"][
            "component"
        ]
        == "microtonal"
    )


def test_candidate_generation():
    e = make_analyzer()

    result = e.analyze(
        make_fusion(),
        candidates=[7, 0],
    )

    assert (
        len(
            result["ranking"][
                "candidates"
            ]
        )
        == 2
    )


def test_score_range():
    e = make_analyzer()

    result = e.analyze(
        make_fusion(),
        candidates=[7, 0],
    )

    for candidate in (
        result["ranking"][
            "candidates"
        ]
    ):
        assert (
            0.0
            <= candidate[
                "original_fused_score"
            ]
            <= 1.0
        )

        assert (
            0.0
            <= candidate[
                "evidence_mean"
            ]
            <= 1.0
        )

        assert (
            0.0
            <= candidate[
                "evidence_std"
            ]
        )

        assert (
            0.0
            <= candidate[
                "evidence_spread"
            ]
            <= 1.0
        )


def test_g_vs_c_conflict():
    e = make_analyzer()

    result = e.analyze(
        make_fusion(),
        candidates=[7, 0],
    )

    pair = result[
        "pair_calibration"
    ]

    assert pair is not None

    assert (
        pair["first_tonic"]
        == "C"
    )

    assert (
        pair["second_tonic"]
        == "G"
    )

    assert (
        0.0
        <= pair["agreement_score"]
        <= 1.0
    )

    assert (
        0.0
        <= pair["conflict_score"]
        <= 1.0
    )

    assert (
        pair["conflict_score"]
        > 0.0
    )


def test_group_preferences():
    e = make_analyzer()

    result = e.analyze(
        make_fusion(),
        candidates=[7, 0],
    )

    preferences = result[
        "group_preferences"
    ]

    assert (
        preferences["functional"][
            "preferred_tonic"
        ]
        == "G"
    )

    assert (
        preferences["cadential"][
            "preferred_tonic"
        ]
        == "G"
    )

    assert (
        preferences["stable_center"][
            "preferred_tonic"
        ]
        == "C"
    )

    assert (
        preferences[
            "intervallic_relationship"
        ][
            "preferred_tonic"
        ]
        == "C"
    )


def test_evidence_only():
    e = make_analyzer()

    result = e.analyze(
        make_fusion(),
        candidates=[7, 0],
    )

    assert (
        result["decision"]["status"]
        == "EVIDENCE_ONLY"
    )

    assert (
        result["decision"][
            "tonic_pitch_class"
        ]
        is None
    )

    assert (
        result["decision"]["tonic_name"]
        is None
    )

    assert (
        result["decision"]["maqam"]
        is None
    )

    assert (
        result["decision"]["jins"]
        is None
    )


def test_no_source_correction():
    e = make_analyzer()

    result = e.analyze(
        make_fusion(),
        candidates=[7, 0],
    )

    protection = result[
        "protection"
    ]

    assert (
        protection[
            "source_pitch_modified"
        ]
        is False
    )

    assert (
        protection[
            "source_timing_modified"
        ]
        is False
    )

    assert (
        protection[
            "source_performance_modified"
        ]
        is False
    )


def test_no_tonic_decision():
    e = make_analyzer()

    result = e.analyze(
        make_fusion(),
        candidates=[7, 0],
    )

    assert (
        result["protection"][
            "tonic_decision_made"
        ]
        is False
    )

    assert (
        result["protection"][
            "maqam_decision_made"
        ]
        is False
    )

    assert (
        result["protection"][
            "jins_decision_made"
        ]
        is False
    )

    assert (
        result["protection"][
            "source_scores_modified"
        ]
        is False
    )

    assert (
        result["protection"][
            "original_scores_preserved"
        ]
        is True
    )


def run():
    print(
        "PhoenixVoiceEngine"
    )
    print(
        "Tonic Evidence Calibration V1.0"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_component_extraction,
        test_supporting_evidence,
        test_opposing_evidence,
        test_agreement_score,
        test_conflict_score,
        test_evidence_spread,
        test_statistics,
        test_candidate_generation,
        test_score_range,
        test_g_vs_c_conflict,
        test_group_preferences,
        test_evidence_only,
        test_no_source_correction,
        test_no_tonic_decision,
    ]

    for i, fn in enumerate(
        tests,
        1,
    ):
        fn()

        print(
            f"TEST {i}: "
            f"{fn.__name__} - PASS"
        )

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()