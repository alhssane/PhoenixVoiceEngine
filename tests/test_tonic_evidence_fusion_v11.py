from src.maqam.tonic_evidence_fusion_v11 import (
    TonicEvidenceFusionV11,
)


def make_analyzer():
    return TonicEvidenceFusionV11()


def make_original_fusion():
    return {
        "decision": {
            "status": "EVIDENCE_ONLY",
            "tonic_pitch_class": None,
            "tonic_name": None,
            "maqam": None,
            "jins": None,
            "confidence": None,
        },
        "ranking": {
            "candidates": [
                {
                    "tonic_pitch_class": 7,
                    "tonic_name": "G",
                    "fused_score": 0.524349,
                    "components": {
                        "functional": 0.400760,
                        "cadential": 0.591304,
                        "stable_center": 0.646084,
                        "microtonal": 0.885423,
                        "tonic_relative": 0.089706,
                    },
                    "evidence_only": True,
                },
                {
                    "tonic_pitch_class": 0,
                    "tonic_name": "C",
                    "fused_score": 0.510156,
                    "components": {
                        "functional": 0.369567,
                        "cadential": 0.538975,
                        "stable_center": 0.700404,
                        "microtonal": 0.885423,
                        "tonic_relative": 0.089706,
                    },
                    "evidence_only": True,
                },
            ]
        },
    }


def make_intervallic():
    return {
        "decision": {
            "status": "EVIDENCE_ONLY",
        },
        "ranking": {
            "candidates": [
                {
                    "tonic_pitch_class": 7,
                    "tonic_name": "G",
                    "score": 0.774768,
                    "components": {
                        "pitch_recurrence": 0.526006,
                        "tonic_transition": 0.789888,
                        "stable_center_coverage": 1.0,
                        "relationship_availability": 0.9,
                    },
                    "evidence_only": True,
                },
                {
                    "tonic_pitch_class": 0,
                    "tonic_name": "C",
                    "score": 0.821936,
                    "components": {
                        "pitch_recurrence": 0.673119,
                        "tonic_transition": 0.8,
                        "stable_center_coverage": 1.0,
                        "relationship_availability": 0.9,
                    },
                    "evidence_only": True,
                },
            ]
        },
    }


def make_empty():
    return {
        "evidence": {}
    }


def test_build():
    assert (
        TonicEvidenceFusionV11.VERSION
        == "1.0.0"
    )

    assert (
        TonicEvidenceFusionV11.FEATURE_VERSION
        == "1.0.0"
    )

    assert (
        TonicEvidenceFusionV11.PATCH_VERSION
        == "1.1.0"
    )


def test_weights_sum_to_one():
    e = make_analyzer()

    assert abs(
        sum(e.WEIGHTS.values())
        - 1.0
    ) < 1e-9


def test_original_scores_preserved():
    e = make_analyzer()

    original = make_original_fusion()

    result = e._extract_original_components(
        original,
        7,
    )

    assert (
        result["functional"]
        == 0.400760
    )

    assert (
        result["cadential"]
        == 0.591304
    )

    assert (
        result["stable_center"]
        == 0.646084
    )

    assert (
        result["microtonal"]
        == 0.885423
    )

    assert (
        result["tonic_relative"]
        == 0.089706
    )


def test_intervallic_extraction():
    e = make_analyzer()

    result = e._extract_intervallic(
        make_intervallic(),
        7,
    )

    assert (
        result["score"]
        == 0.774768
    )

    assert (
        result["components"][
            "tonic_transition"
        ]
        == 0.789888
    )


def test_intervallic_c():
    e = make_analyzer()

    result = e._extract_intervallic(
        make_intervallic(),
        0,
    )

    assert (
        result["score"]
        == 0.821936
    )


def test_fusion_candidate():
    e = make_analyzer()

    original = e._extract_original_components(
        make_original_fusion(),
        7,
    )

    intervallic = e._extract_intervallic(
        make_intervallic(),
        7,
    )

    result = e._fuse_candidate(
        7,
        original,
        intervallic,
    )

    assert (
        0.0
        <= result["fused_score"]
        <= 1.0
    )

    assert (
        result["components"][
            "intervallic_relationship"
        ]
        == 0.774768
    )


def test_intervallic_component_present():
    e = make_analyzer()

    result = e.analyze(
        make_empty(),
        make_empty(),
        make_empty(),
        make_empty(),
        make_original_fusion(),
        make_intervallic(),
        candidates=[7, 0],
    )

    for candidate in result[
        "ranking"
    ]["candidates"]:

        assert (
            "intervallic_relationship"
            in candidate["components"]
        )


def test_fused_score_range():
    e = make_analyzer()

    result = e.analyze(
        make_empty(),
        make_empty(),
        make_empty(),
        make_empty(),
        make_original_fusion(),
        make_intervallic(),
        candidates=[7, 0],
    )

    for candidate in result[
        "ranking"
    ]["candidates"]:

        assert (
            0.0
            <= candidate["fused_score"]
            <= 1.0
        )


def test_ranking_generated():
    e = make_analyzer()

    result = e.analyze(
        make_empty(),
        make_empty(),
        make_empty(),
        make_empty(),
        make_original_fusion(),
        make_intervallic(),
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

    assert (
        result["ranking"]["top"]
        is not None
    )

    assert (
        result["ranking"]["second"]
        is not None
    )


def test_margin_generated():
    e = make_analyzer()

    result = e.analyze(
        make_empty(),
        make_empty(),
        make_empty(),
        make_empty(),
        make_original_fusion(),
        make_intervallic(),
        candidates=[7, 0],
    )

    assert (
        result["ranking"]["margin"]
        >= 0.0
    )


def test_original_decision_not_overridden():
    e = make_analyzer()

    result = e.analyze(
        make_empty(),
        make_empty(),
        make_empty(),
        make_empty(),
        make_original_fusion(),
        make_intervallic(),
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
        result["protection"][
            "original_v10_decision_overridden"
        ]
        is False
    )


def test_protection():
    e = make_analyzer()

    result = e.analyze(
        make_empty(),
        make_empty(),
        make_empty(),
        make_empty(),
        make_original_fusion(),
        make_intervallic(),
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

    assert (
        protection[
            "tonic_decision_made"
        ]
        is False
    )

    assert (
        protection[
            "maqam_decision_made"
        ]
        is False
    )

    assert (
        protection[
            "jins_decision_made"
        ]
        is False
    )

    assert (
        protection[
            "original_scores_preserved"
        ]
        is True
    )

    assert (
        protection[
            "intervallic_evidence_added"
        ]
        is True
    )


def test_evidence_only():
    e = make_analyzer()

    result = e.analyze(
        make_empty(),
        make_empty(),
        make_empty(),
        make_empty(),
        make_original_fusion(),
        make_intervallic(),
        candidates=[7, 0],
    )

    assert (
        result["decision"]["status"]
        == "EVIDENCE_ONLY"
    )

    assert (
        result["decision"]["maqam"]
        is None
    )

    assert (
        result["decision"]["jins"]
        is None
    )


def run():
    print("PhoenixVoiceEngine")
    print(
        "Tonic Evidence Fusion V1.1"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_weights_sum_to_one,
        test_original_scores_preserved,
        test_intervallic_extraction,
        test_intervallic_c,
        test_fusion_candidate,
        test_intervallic_component_present,
        test_fused_score_range,
        test_ranking_generated,
        test_margin_generated,
        test_original_decision_not_overridden,
        test_protection,
        test_evidence_only,
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