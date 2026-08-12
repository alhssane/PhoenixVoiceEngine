"""
PhoenixVoiceEngine
Tonic Evidence Reliability Analyzer V1.0 Tests
"""

from src.maqam.tonic_evidence_reliability_analyzer import (
    TonicEvidenceReliabilityAnalyzer,
)


def _fusion_fixture():
    return {
        "version": "1.0.0",
        "feature_version": "1.0.0",
        "patch_version": "1.1.0",
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
        "decision": {
            "status": "EVIDENCE_ONLY",
            "tonic_pitch_class": None,
            "tonic_name": None,
            "maqam": None,
            "jins": None,
            "confidence": None,
        },
    }


def _calibration_fixture():
    return {
        "version": "1.0.0",
        "ranking": {
            "candidates": [
                {
                    "tonic_name": "G",
                    "evidence_spread": 0.48,
                    "components": {
                        "functional": 0.400760,
                        "cadential": 0.591304,
                        "stable_center": 0.646084,
                        "microtonal": 0.885423,
                        "tonic_relative": 0.089706,
                        "intervallic_relationship": 0.774768,
                    },
                },
                {
                    "tonic_name": "C",
                    "evidence_spread": 0.61,
                    "components": {
                        "functional": 0.369567,
                        "cadential": 0.538975,
                        "stable_center": 0.700404,
                        "microtonal": 0.885423,
                        "tonic_relative": 0.089706,
                        "intervallic_relationship": 0.821936,
                    },
                },
            ]
        },
    }


def test_build():
    e = TonicEvidenceReliabilityAnalyzer()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.0"


def test_component_extraction():
    e = TonicEvidenceReliabilityAnalyzer()

    candidate = _fusion_fixture()["ranking"][
        "candidates"
    ][0]

    result = e._extract_components(
        candidate
    )

    assert len(result) == 6
    assert "functional" in result
    assert "cadential" in result
    assert "intervallic_relationship" in result


def test_component_separation():
    e = TonicEvidenceReliabilityAnalyzer()

    candidates = _fusion_fixture()["ranking"][
        "candidates"
    ]

    result = e._component_separation(
        candidates
    )

    assert "functional" in result
    assert result["functional"]["available"] is True
    assert result["functional"]["absolute_difference"] > 0.0


def test_preferences():
    e = TonicEvidenceReliabilityAnalyzer()

    candidates = _fusion_fixture()["ranking"][
        "candidates"
    ]

    result = e._component_preferences(
        candidates
    )

    assert result["functional"] == "G"
    assert result["cadential"] == "G"
    assert result["stable_center"] == "C"
    assert result["intervallic_relationship"] == "C"


def test_strength():
    e = TonicEvidenceReliabilityAnalyzer()

    result = e._strength_score(
        0.40,
        0.36,
    )

    assert 0.0 <= result <= 1.0
    assert result == 0.40


def test_separation():
    e = TonicEvidenceReliabilityAnalyzer()

    result = e._separation_score(
        0.40,
        0.36,
    )

    assert 0.0 <= result <= 1.0
    assert abs(result - 0.04) < 1e-9


def test_reliability_range():
    e = TonicEvidenceReliabilityAnalyzer()

    result = e._reliability_score(
        availability=1.0,
        strength=0.8,
        separation=0.4,
        stability=0.7,
        agreement=0.6,
        conflict=0.2,
    )

    assert 0.0 <= result <= 1.0


def test_g_vs_c_reliability():
    e = TonicEvidenceReliabilityAnalyzer()

    result = e.analyze(
        _fusion_fixture(),
        calibration_data=_calibration_fixture(),
        candidates=[7, 0],
    )

    assert len(
        result["reliability"]["components"]
    ) == 6

    assert (
        result["reliability"]["overall_score"]
        >= 0.0
    )

    assert (
        result["reliability"]["overall_score"]
        <= 1.0
    )


def test_strongest_component_present():
    e = TonicEvidenceReliabilityAnalyzer()

    result = e.analyze(
        _fusion_fixture(),
        calibration_data=_calibration_fixture(),
        candidates=[7, 0],
    )

    strongest = result[
        "reliability"
    ]["strongest_component"]

    assert strongest is not None
    assert (
        "component"
        in strongest
    )


def test_evidence_only():
    e = TonicEvidenceReliabilityAnalyzer()

    result = e.analyze(
        _fusion_fixture(),
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


def test_no_source_correction():
    e = TonicEvidenceReliabilityAnalyzer()

    result = e.analyze(
        _fusion_fixture(),
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


def test_original_scores_preserved():
    e = TonicEvidenceReliabilityAnalyzer()

    fixture = _fusion_fixture()

    result = e.analyze(
        fixture,
        candidates=[7, 0],
    )

    original = fixture[
        "ranking"
    ]["candidates"]

    analyzed = result[
        "reliability"
    ]["components"]

    assert len(analyzed) == 6

    assert (
        result["protection"][
            "original_scores_preserved"
        ]
        is True
    )

    assert (
        result["protection"][
            "source_scores_modified"
        ]
        is False
    )


def run():
    print(
        "PhoenixVoiceEngine"
    )
    print(
        "Tonic Evidence Reliability Analyzer V1.0"
    )
    print(
        "=" * 60
    )

    tests = [
        test_build,
        test_component_extraction,
        test_component_separation,
        test_preferences,
        test_strength,
        test_separation,
        test_reliability_range,
        test_g_vs_c_reliability,
        test_strongest_component_present,
        test_evidence_only,
        test_no_source_correction,
        test_original_scores_preserved,
    ]

    for index, test in enumerate(
        tests,
        start=1,
    ):

        test()

        print(
            f"TEST {index}: "
            f"{test.__name__} - PASS"
        )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":
    run()