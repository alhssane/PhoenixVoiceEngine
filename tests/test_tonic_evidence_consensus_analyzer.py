"""
PhoenixVoiceEngine
Tonic Evidence Consensus Analyzer V1.0 Tests
"""

from src.maqam.tonic_evidence_consensus_analyzer import (
    TonicEvidenceConsensusAnalyzer,
)


def fusion_fixture():
    return {
        "version": "1.0.0",
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


def reliability_fixture():
    return {
        "version": "1.0.0",
        "feature_version": "1.1.0",
        "patch_version": "1.1.0",

        "reliability": {
            "overall_score": 0.374311,

            "components": [
                {
                    "component": "stable_center",
                    "reliability_score": 0.453455,
                    "availability": 1.0,
                    "strength": 0.829013,
                    "separation": 0.054320,
                    "stability": 0.717277,
                    "agreement": 0.333333,
                    "conflict": 0.666667,
                    "preferred_tonic": "C",
                    "meaningful_separation": True,
                },
                {
                    "component": "intervallic_relationship",
                    "reliability_score": 0.442394,
                    "availability": 0.9,
                    "strength": 0.798352,
                    "separation": 0.047168,
                    "stability": 0.774781,
                    "agreement": 0.333333,
                    "conflict": 0.666667,
                    "preferred_tonic": "C",
                    "meaningful_separation": False,
                },
                {
                    "component": "tonic_relative",
                    "reliability_score": 0.372902,
                    "availability": 1.0,
                    "strength": 0.807255,
                    "separation": 0.0,
                    "stability": 0.807255,
                    "agreement": 0.0,
                    "conflict": 1.0,
                    "preferred_tonic": "TIE",
                    "meaningful_separation": False,
                },
                {
                    "component": "functional",
                    "reliability_score": 0.357733,
                    "availability": 1.0,
                    "strength": 0.188630,
                    "separation": 0.031193,
                    "stability": 0.902174,
                    "agreement": 0.333333,
                    "conflict": 0.666667,
                    "preferred_tonic": "G",
                    "meaningful_separation": False,
                },
                {
                    "component": "microtonal",
                    "reliability_score": 0.349278,
                    "availability": 0.988333,
                    "strength": 0.811510,
                    "separation": 0.0,
                    "stability": 0.693628,
                    "agreement": 0.0,
                    "conflict": 1.0,
                    "preferred_tonic": "TIE",
                    "meaningful_separation": False,
                },
                {
                    "component": "cadential",
                    "reliability_score": 0.270103,
                    "availability": 0.688407,
                    "strength": 0.300401,
                    "separation": 0.052329,
                    "stability": 0.564813,
                    "agreement": 0.333333,
                    "conflict": 0.666667,
                    "preferred_tonic": "G",
                    "meaningful_separation": True,
                },
            ]
        },

        "evidence_preferences": {
            "functional": "G",
            "cadential": "G",
            "stable_center": "C",
            "microtonal": "TIE",
            "tonic_relative": "TIE",
            "intervallic_relationship": "C",
        },

        "separation": {
            "stable_center": {
                "difference": 0.054320,
                "meaningful": True,
                "top_tonic": "C",
                "second_tonic": "G",
            },
            "intervallic_relationship": {
                "difference": 0.047168,
                "meaningful": False,
                "top_tonic": "C",
                "second_tonic": "G",
            },
            "functional": {
                "difference": 0.031193,
                "meaningful": False,
                "top_tonic": "G",
                "second_tonic": "C",
            },
            "cadential": {
                "difference": 0.052329,
                "meaningful": True,
                "top_tonic": "G",
                "second_tonic": "C",
            },
        }
    }


def calibration_fixture():
    return {
        "version": "1.0.0",
        "decision": {
            "status": "EVIDENCE_ONLY"
        }
    }


def test_build():
    e = TonicEvidenceConsensusAnalyzer()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.0"


def test_component_extraction():
    e = TonicEvidenceConsensusAnalyzer()

    result = e._extract_reliability(
        reliability_fixture()
    )

    assert len(result) == 6
    assert (
        result["stable_center"]
        ["reliability_score"]
        == 0.453455
    )


def test_preferences():
    e = TonicEvidenceConsensusAnalyzer()

    result = e._extract_preferences(
        reliability_fixture(),
        fusion_fixture(),
    )

    assert result["functional"] == "G"
    assert result["cadential"] == "G"
    assert result["stable_center"] == "C"
    assert (
        result["intervallic_relationship"]
        == "C"
    )
    assert result["microtonal"] == "TIE"
    assert result["tonic_relative"] == "TIE"


def test_groups():
    e = TonicEvidenceConsensusAnalyzer()

    preferences = e._extract_preferences(
        reliability_fixture(),
        fusion_fixture(),
    )

    groups = e._groups(
        preferences
    )

    assert "G" in groups
    assert "C" in groups

    assert "functional" in groups["G"]
    assert "cadential" in groups["G"]

    assert "stable_center" in groups["C"]
    assert (
        "intervallic_relationship"
        in groups["C"]
    )


def test_agreement_conflict():
    e = TonicEvidenceConsensusAnalyzer()

    preferences = e._extract_preferences(
        reliability_fixture(),
        fusion_fixture(),
    )

    reliability = e._extract_reliability(
        reliability_fixture()
    )

    result = e._agreement_metrics(
        preferences,
        reliability,
    )

    assert (
        result["decisive_component_count"]
        == 4
    )

    assert (
        result["tie_component_count"]
        == 2
    )

    assert (
        result["agreement_score"]
        >= 0.0
    )

    assert (
        result["conflict_score"]
        >= 0.0
    )

    assert (
        result["dominant_tonic"]
        in ("G", "C")
    )


def test_weighted_support():
    e = TonicEvidenceConsensusAnalyzer()

    preferences = e._extract_preferences(
        reliability_fixture(),
        fusion_fixture(),
    )

    reliability = e._extract_reliability(
        reliability_fixture()
    )

    result = e._weighted_tonic_support(
        preferences,
        reliability,
    )

    assert "G" in result
    assert "C" in result

    assert result["G"] >= 0.0
    assert result["C"] >= 0.0


def test_no_full_weight_without_separation():
    e = TonicEvidenceConsensusAnalyzer()

    preferences = {
        "functional": "G",
        "cadential": "G",
        "stable_center": "C",
        "microtonal": "TIE",
        "tonic_relative": "TIE",
        "intervallic_relationship": "C",
    }

    reliability = {
        "functional": {
            "reliability_score": 0.90,
            "separation": 0.0,
            "meaningful_separation": False,
        },
        "cadential": {
            "reliability_score": 0.90,
            "separation": 0.0,
            "meaningful_separation": False,
        },
        "stable_center": {
            "reliability_score": 0.90,
            "separation": 0.0,
            "meaningful_separation": False,
        },
        "microtonal": {
            "reliability_score": 0.90,
            "separation": 0.0,
            "meaningful_separation": False,
        },
        "tonic_relative": {
            "reliability_score": 0.90,
            "separation": 0.0,
            "meaningful_separation": False,
        },
        "intervallic_relationship": {
            "reliability_score": 0.90,
            "separation": 0.0,
            "meaningful_separation": False,
        },
    }

    result = e._weighted_tonic_support(
        preferences,
        reliability,
    )

    # No separation means no meaningful tonic support.
    assert result["G"] == 0.0
    assert result["C"] == 0.0


def test_consensus_quality():
    e = TonicEvidenceConsensusAnalyzer()

    agreement = e._agreement_metrics(
        e._extract_preferences(
            reliability_fixture(),
            fusion_fixture(),
        ),
        e._extract_reliability(
            reliability_fixture()
        ),
    )

    support = e._weighted_tonic_support(
        e._extract_preferences(
            reliability_fixture(),
            fusion_fixture(),
        ),
        e._extract_reliability(
            reliability_fixture()
        ),
    )

    result = e._consensus_quality(
        agreement_score=agreement[
            "agreement_score"
        ],
        conflict_score=agreement[
            "conflict_score"
        ],
        weighted_support=support,
        reliability_data=reliability_fixture(),
    )

    assert (
        0.0
        <= result["consensus_quality"]
        <= 1.0
    )

    assert (
        result["top_tonic"]
        in ("G", "C")
    )


def test_conflicting_status():
    e = TonicEvidenceConsensusAnalyzer()

    status = e._status(
        agreement=0.45,
        conflict=0.55,
        support_share=0.55,
        support_margin=0.02,
    )

    assert status == "CONFLICTING_EVIDENCE"


def test_evidence_only():
    e = TonicEvidenceConsensusAnalyzer()

    result = e.analyze(
        fusion_data=fusion_fixture(),
        reliability_data=reliability_fixture(),
        calibration_data=calibration_fixture(),
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


def test_conflict_remains_visible():
    e = TonicEvidenceConsensusAnalyzer()

    result = e.analyze(
        fusion_data=fusion_fixture(),
        reliability_data=reliability_fixture(),
        calibration_data=calibration_fixture(),
        candidates=[7, 0],
    )

    preferences = result[
        "evidence_preferences"
    ]

    assert preferences["functional"] == "G"
    assert preferences["cadential"] == "G"
    assert preferences["stable_center"] == "C"
    assert (
        preferences[
            "intervallic_relationship"
        ]
        == "C"
    )


def test_protection():
    e = TonicEvidenceConsensusAnalyzer()

    result = e.analyze(
        fusion_data=fusion_fixture(),
        reliability_data=reliability_fixture(),
        calibration_data=calibration_fixture(),
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
            "source_scores_modified"
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
            "original_decision_overridden"
        ]
        is False
    )

    assert (
        protection[
            "evidence_conflict_hidden"
        ]
        is False
    )


def test_candidate_generation():
    e = TonicEvidenceConsensusAnalyzer()

    result = e._extract_candidates(
        fusion_fixture(),
        candidates=[7],
    )

    assert len(result) == 1
    assert (
        result[0][
            "tonic_pitch_class"
        ]
        == 7
    )


def test_score_ranges():
    e = TonicEvidenceConsensusAnalyzer()

    result = e.analyze(
        fusion_data=fusion_fixture(),
        reliability_data=reliability_fixture(),
        calibration_data=calibration_fixture(),
        candidates=[7, 0],
    )

    consensus = result[
        "consensus"
    ]

    assert (
        0.0
        <= consensus[
            "agreement"
        ]["agreement_score"]
        <= 1.0
    )

    assert (
        0.0
        <= consensus[
            "agreement"
        ]["conflict_score"]
        <= 1.0
    )

    assert (
        0.0
        <= consensus[
            "quality"
        ]["consensus_quality"]
        <= 1.0
    )


def test_no_tonic_decision():
    e = TonicEvidenceConsensusAnalyzer()

    result = e.analyze(
        fusion_data=fusion_fixture(),
        reliability_data=reliability_fixture(),
        calibration_data=calibration_fixture(),
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
        "Tonic Evidence Consensus Analyzer V1.0"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_component_extraction,
        test_preferences,
        test_groups,
        test_agreement_conflict,
        test_weighted_support,
        test_no_full_weight_without_separation,
        test_consensus_quality,
        test_conflicting_status,
        test_evidence_only,
        test_conflict_remains_visible,
        test_protection,
        test_candidate_generation,
        test_score_ranges,
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