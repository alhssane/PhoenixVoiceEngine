"""
PhoenixVoiceEngine
Tonic Evidence Reliability Analyzer V1.1 Tests
"""

from src.maqam.tonic_evidence_reliability_analyzer_v11 import (
    TonicEvidenceReliabilityAnalyzerV11,
)


def fusion_fixture():
    return {
        "version": "1.0.0",
        "feature_version": "1.1.0",
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


def functional_fixture():
    return {
        "evidence": {
            "tonic_role_comparison": [
                {
                    "tonic_pitch_class": 7,
                    "role": {
                        "event_count": 66,
                        "duration_share": 0.16056,
                        "phrase_initial_ratio": 0.217391,
                        "phrase_final_ratio": 0.26087,
                    },
                },
                {
                    "tonic_pitch_class": 0,
                    "role": {
                        "event_count": 75,
                        "duration_share": 0.179328,
                        "phrase_initial_ratio": 0.173913,
                        "phrase_final_ratio": 0.152174,
                    },
                },
            ]
        }
    }


def cadential_fixture():
    return {
        "ranking": {
            "candidates": [
                {
                    "tonic_pitch_class": 7,
                    "ending_phrase_ratio": 0.26087,
                    "recurring_contexts": [
                        {
                            "count": 6,
                            "ending_ratio": 0.50,
                        },
                        {
                            "count": 3,
                            "ending_ratio": 0.25,
                        },
                    ],
                },
                {
                    "tonic_pitch_class": 0,
                    "ending_phrase_ratio": 0.152174,
                    "recurring_contexts": [
                        {
                            "count": 3,
                            "ending_ratio": 0.428571,
                        },
                    ],
                },
            ]
        }
    }


def stable_fixture():
    return {
        "evidence": {
            "stable_pitch_centers": [
                {
                    "pitch_class": 7,
                    "region_count": 53,
                    "total_duration": 31.25,
                    "raw_hz_sample_count": 2930,
                    "center_cents": -17.1294,
                    "median_region_deviation_cents": 7.7751,
                    "mean_stability_score": 0.729585,
                },
                {
                    "pitch_class": 0,
                    "region_count": 102,
                    "total_duration": 39.99,
                    "raw_hz_sample_count": 3919,
                    "center_cents": -14.5198,
                    "median_region_deviation_cents": 10.0,
                    "mean_stability_score": 0.723007,
                },
            ]
        }
    }


def tonic_relative_fixture():
    return {
        "ranking": {
            "candidates": [
                {
                    "tonic_pitch_class": 7,
                    "relative_evidence_score": 0.20,
                },
                {
                    "tonic_pitch_class": 0,
                    "relative_evidence_score": 0.10,
                },
            ]
        }
    }


def intervallic_fixture():
    return {
        "ranking": {
            "candidates": [
                {
                    "tonic_pitch_class": 7,
                    "components": {
                        "pitch_recurrence": 0.526006,
                        "tonic_transition": 0.789888,
                        "stable_center_coverage": 1.0,
                        "relationship_availability": 0.9,
                    },
                    "intervallic_detail": {
                        "pitch_recurrence": 0.526006,
                        "tonic_transition": 0.789888,
                        "stable_center_coverage": 1.0,
                        "relationship_availability": 0.9,
                    },
                },
                {
                    "tonic_pitch_class": 0,
                    "components": {
                        "pitch_recurrence": 0.673119,
                        "tonic_transition": 0.8,
                        "stable_center_coverage": 1.0,
                        "relationship_availability": 0.9,
                    },
                    "intervallic_detail": {
                        "pitch_recurrence": 0.673119,
                        "tonic_transition": 0.8,
                        "stable_center_coverage": 1.0,
                        "relationship_availability": 0.9,
                    },
                },
            ]
        }
    }


def test_build():
    e = TonicEvidenceReliabilityAnalyzerV11()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.1.0"
    assert e.PATCH_VERSION == "1.1.0"


def test_component_specific_functional():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e._functional_reliability(
        functional_fixture(),
        7,
    )

    assert result["availability"] > 0
    assert result["strength"] > 0
    assert result["stability"] > 0


def test_component_specific_cadential():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e._cadential_reliability(
        cadential_fixture(),
        7,
    )

    assert result["availability"] > 0
    assert result["strength"] > 0
    assert result["stability"] > 0


def test_component_specific_stable_center():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e._stable_center_reliability(
        stable_fixture(),
        7,
    )

    assert result["availability"] > 0
    assert result["strength"] > 0
    assert result["stability"] > 0


def test_component_specific_microtonal():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e._microtonal_reliability(
        stable_fixture(),
        7,
    )

    assert result["availability"] > 0
    assert result["strength"] > 0
    assert result["stability"] > 0


def test_component_specific_tonic_relative():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e._tonic_relative_reliability(
        tonic_relative_fixture(),
        7,
    )

    assert result["availability"] == 1.0
    assert result["strength"] > 0


def test_component_specific_intervallic():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e._intervallic_reliability(
        intervallic_fixture(),
        0,
    )

    assert result["availability"] > 0
    assert result["strength"] > 0
    assert result["stability"] > 0


def test_separation():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e._separation(
        fusion_fixture()["ranking"]["candidates"]
    )

    assert result["functional"]["difference"] > 0
    assert result["stable_center"]["difference"] > 0


def test_preferences():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e._preferences(
        fusion_fixture()["ranking"]["candidates"]
    )

    assert result["functional"] == "G"
    assert result["cadential"] == "G"
    assert result["stable_center"] == "C"
    assert result["intervallic_relationship"] == "C"


def test_reliability_range():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e._reliability_score(
        availability=1.0,
        strength=0.8,
        separation=0.2,
        stability=0.7,
        agreement=0.5,
        conflict=0.5,
    )

    assert 0.0 <= result <= 1.0


def test_full_analysis():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e.analyze(
        fusion_fixture(),
        functional_data=functional_fixture(),
        cadential_data=cadential_fixture(),
        stable_center_data=stable_fixture(),
        tonic_relative_data=tonic_relative_fixture(),
        intervallic_data=intervallic_fixture(),
        candidates=[7, 0],
    )

    assert (
        len(
            result["reliability"]["components"]
        )
        == 6
    )

    assert (
        result["reliability"]["overall_score"]
        >= 0.0
    )

    assert (
        result["reliability"]["overall_score"]
        <= 1.0
    )


def test_source_specific_stability():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e.analyze(
        fusion_fixture(),
        functional_data=functional_fixture(),
        cadential_data=cadential_fixture(),
        stable_center_data=stable_fixture(),
        tonic_relative_data=tonic_relative_fixture(),
        intervallic_data=intervallic_fixture(),
        candidates=[7, 0],
    )

    values = {
        item["component"]: item["stability"]
        for item in result[
            "reliability"
        ]["components"]
    }

    # V1.1 must not use one identical generic
    # stability value for every component.
    assert len(
        set(values.values())
    ) > 1


def test_evidence_only():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e.analyze(
        fusion_fixture(),
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
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e.analyze(
        fusion_fixture(),
        candidates=[7, 0],
    )

    protection = result["protection"]

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
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e.analyze(
        fusion_fixture(),
        candidates=[7, 0],
    )

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

    assert (
        result["protection"][
            "original_decision_overridden"
        ]
        is False
    )


def test_no_tonic_decision():
    e = TonicEvidenceReliabilityAnalyzerV11()

    result = e.analyze(
        fusion_fixture(),
        candidates=[7, 0],
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


def run():
    print("PhoenixVoiceEngine")
    print(
        "Tonic Evidence Reliability Analyzer V1.1"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_component_specific_functional,
        test_component_specific_cadential,
        test_component_specific_stable_center,
        test_component_specific_microtonal,
        test_component_specific_tonic_relative,
        test_component_specific_intervallic,
        test_separation,
        test_preferences,
        test_reliability_range,
        test_full_analysis,
        test_source_specific_stability,
        test_evidence_only,
        test_no_source_correction,
        test_original_scores_preserved,
        test_no_tonic_decision,
    ]

    for index, fn in enumerate(
        tests,
        start=1,
    ):
        fn()
        print(
            f"TEST {index}: "
            f"{fn.__name__} - PASS"
        )

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()