"""
PhoenixVoiceEngine
Tonic Decision Readiness Analyzer V1.0 Tests
"""

from src.maqam.tonic_decision_readiness_analyzer import (
    TonicDecisionReadinessAnalyzer,
)


# ============================================================
# Fixtures
# ============================================================

def consensus_fixture():
    return {
        "version": "1.0.0",
        "consensus": {
            "status": "MODERATE_CONSENSUS",

            "agreement": {
                "agreement_score": 0.456026,
                "conflict_score": 0.543974,
                "dominant_tonic": "G",
                "dominant_share": 0.5,
                "weighted_agreement": 0.412051,
            },

            "weighted_tonic_support": {
                "G": 0.101172,
                "C": 0.181994,
            },

            "quality": {
                "top_tonic": "C",
                "support_share": 0.642711,
                "support_margin": 0.080822,
                "consensus_quality": 0.455721,
            },
        },

        "evidence_preferences": {
            "functional": "G",
            "cadential": "G",
            "stable_center": "C",
            "microtonal": "TIE",
            "tonic_relative": "TIE",
            "intervallic_relationship": "C",
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
            ],
        },

        "evidence_preferences": {
            "functional": "G",
            "cadential": "G",
            "stable_center": "C",
            "microtonal": "TIE",
            "tonic_relative": "TIE",
            "intervallic_relationship": "C",
        },
    }


def conflict_fixture():
    return {
        "version": "1.0.0",

        "evidence_preferences": {
            "functional": "G",
            "cadential": "G",
            "stable_center": "C",
            "microtonal": "TIE",
            "tonic_relative": "TIE",
            "intervallic_relationship": "C",
        },

        "conflict": {
            "balance": {
                "G": {
                    "support": 0.020111,
                    "share": 0.124325,
                    "components": [
                        "functional",
                        "cadential",
                    ],
                },

                "C": {
                    "support": 0.141653,
                    "share": 0.875675,
                    "components": [
                        "stable_center",
                        "intervallic_relationship",
                    ],
                },

                "total_support": 0.161764,
                "balance": 0.248649,
                "dominance": 0.751351,
                "weighted_preference": "C",
            },

            "severity": {
                "score": 0.444383,
                "label": "LOW",
                "conflict_score": 0.543974,
                "balance_score": 0.248649,
                "meaningful_G_components": 1,
                "meaningful_C_components": 1,
                "opposing_presence": 0.5,
            },

            "strongest_by_group": {
                "G": {
                    "component": "cadential",
                    "effective_weight": 0.011692,
                    "reliability": 0.270103,
                    "strength": 0.300401,
                    "separation": 0.052329,
                    "meaningful_separation": True,
                },

                "C": {
                    "component": "stable_center",
                    "effective_weight": 0.081680,
                    "reliability": 0.453455,
                    "strength": 0.829013,
                    "separation": 0.054320,
                    "meaningful_separation": True,
                },
            },

            "consensus_context": {
                "agreement_score": 0.456026,
                "conflict_score": 0.543974,
                "weighted_agreement": 0.412051,
                "support_share": 0.642711,
                "support_margin": 0.080822,
                "consensus_quality": 0.455721,
            },
        },

        "decision_safety": {
            "tonic_decision_safe": False,
            "level": "CAUTION",
            "conflict_requires_abstention": False,
        },
    }


# ============================================================
# TEST 1
# ============================================================

def test_build():
    e = TonicDecisionReadinessAnalyzer()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.0"


# ============================================================
# TEST 2
# ============================================================

def test_consensus_extraction():
    e = TonicDecisionReadinessAnalyzer()

    result = e._extract_consensus(
        consensus_fixture()
    )

    assert result["status"] == (
        "MODERATE_CONSENSUS"
    )

    assert result["agreement_score"] == 0.456026
    assert result["conflict_score"] == 0.543974

    assert result["top_tonic"] == "C"

    assert result["weighted_support"]["G"] == 0.101172
    assert result["weighted_support"]["C"] == 0.181994


# ============================================================
# TEST 3
# ============================================================

def test_reliability_extraction():
    e = TonicDecisionReadinessAnalyzer()

    result = e._extract_reliability(
        reliability_fixture()
    )

    assert result["overall_score"] == 0.374311

    assert (
        "stable_center"
        in result["components"]
    )

    assert (
        result["components"]["stable_center"][
            "reliability_score"
        ]
        == 0.453455
    )

    assert (
        result["components"]["stable_center"][
            "preferred_tonic"
        ]
        == "C"
    )


# ============================================================
# TEST 4
# ============================================================

def test_conflict_extraction():
    e = TonicDecisionReadinessAnalyzer()

    result = e._extract_conflict(
        conflict_fixture()
    )

    assert result["severity_score"] == 0.444383
    assert result["severity_label"] == "LOW"

    assert result["weighted_preference"] == "C"

    assert result["meaningful_G_components"] == 1
    assert result["meaningful_C_components"] == 1

    assert result["G_support"] == 0.020111
    assert result["C_support"] == 0.141653


# ============================================================
# TEST 5
# ============================================================

def test_preferences():
    e = TonicDecisionReadinessAnalyzer()

    result = e._extract_preferences(
        consensus_fixture(),
        reliability_fixture(),
        conflict_fixture(),
    )

    assert result["functional"] == "G"
    assert result["cadential"] == "G"
    assert result["stable_center"] == "C"
    assert result["intervallic_relationship"] == "C"

    assert result["microtonal"] == "TIE"
    assert result["tonic_relative"] == "TIE"


# ============================================================
# TEST 6
# ============================================================

def test_meaningful_component_count():
    e = TonicDecisionReadinessAnalyzer()

    reliability = e._extract_reliability(
        reliability_fixture()
    )

    count = e._meaningful_component_count(
        reliability
    )

    assert count == 2


# ============================================================
# TEST 7
# ============================================================

def test_candidate_readiness_g():
    e = TonicDecisionReadinessAnalyzer()

    consensus = e._extract_consensus(
        consensus_fixture()
    )

    reliability = e._extract_reliability(
        reliability_fixture()
    )

    conflict = e._extract_conflict(
        conflict_fixture()
    )

    preferences = e._extract_preferences(
        consensus_fixture(),
        reliability_fixture(),
        conflict_fixture(),
    )

    result = e._candidate_readiness(
        tonic="G",
        consensus=consensus,
        reliability=reliability,
        conflict=conflict,
        preferences=preferences,
    )

    assert result["tonic"] == "G"

    assert (
        0.0
        <= result["readiness_score"]
        <= 1.0
    )

    assert (
        result["candidate_support"]
        == 0.101172
    )

    assert (
        "functional"
        in result["supporting_components"]
    )

    assert (
        "cadential"
        in result["supporting_components"]
    )


# ============================================================
# TEST 8
# ============================================================

def test_candidate_readiness_c():
    e = TonicDecisionReadinessAnalyzer()

    consensus = e._extract_consensus(
        consensus_fixture()
    )

    reliability = e._extract_reliability(
        reliability_fixture()
    )

    conflict = e._extract_conflict(
        conflict_fixture()
    )

    preferences = e._extract_preferences(
        consensus_fixture(),
        reliability_fixture(),
        conflict_fixture(),
    )

    result = e._candidate_readiness(
        tonic="C",
        consensus=consensus,
        reliability=reliability,
        conflict=conflict,
        preferences=preferences,
    )

    assert result["tonic"] == "C"

    assert (
        result["candidate_support"]
        == 0.181994
    )

    assert (
        "stable_center"
        in result["supporting_components"]
    )

    assert (
        "intervallic_relationship"
        in result["supporting_components"]
    )


# ============================================================
# TEST 9
# ============================================================

def test_bender_not_ready():
    e = TonicDecisionReadinessAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
        conflict_data=conflict_fixture(),
        candidates=[7, 0],
    )

    global_result = (
        result["readiness"]["global"]
    )

    assert (
        global_result["status"]
        == "NOT_READY"
    )

    assert (
        global_result["readiness_score"]
        >= 0.0
    )

    assert (
        global_result["readiness_score"]
        <= 1.0
    )

    assert (
        "MEANINGFUL_G_C_CONFLICT"
        in global_result["global_blockers"]
    )


# ============================================================
# TEST 10
# ============================================================

def test_blockers_present():
    e = TonicDecisionReadinessAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
        conflict_data=conflict_fixture(),
        candidates=[7, 0],
    )

    global_result = (
        result["readiness"]["global"]
    )

    blockers = (
        global_result["global_blockers"]
    )

    assert isinstance(
        blockers,
        list,
    )

    assert len(blockers) > 0

    assert (
        "OVERALL_RELIABILITY_BELOW_THRESHOLD"
        in blockers
    )

    assert (
        "CONSENSUS_QUALITY_BELOW_THRESHOLD"
        in blockers
    )

    assert (
        "CONFLICT_SCORE_TOO_HIGH"
        in blockers
    )


# ============================================================
# TEST 11
# ============================================================

def test_candidate_checks():
    e = TonicDecisionReadinessAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
        conflict_data=conflict_fixture(),
        candidates=[7, 0],
    )

    candidates = (
        result["readiness"]["candidates"]
    )

    assert len(candidates) == 2

    for candidate in candidates:

        assert (
            candidate["status"]
            in (
                "READY",
                "CONDITIONALLY_READY",
                "NOT_READY",
            )
        )

        assert (
            0.0
            <= candidate["readiness_score"]
            <= 1.0
        )

        assert (
            candidate["passed_checks"]
            <= candidate["total_checks"]
        )


# ============================================================
# TEST 12
# ============================================================

def test_readiness_never_becomes_decision():
    e = TonicDecisionReadinessAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
        conflict_data=conflict_fixture(),
        candidates=[7, 0],
    )

    decision = result[
        "decision"
    ]

    assert (
        decision["status"]
        == "EVIDENCE_ONLY"
    )

    assert (
        decision["tonic_pitch_class"]
        is None
    )

    assert (
        decision["tonic_name"]
        is None
    )

    assert (
        decision["maqam"]
        is None
    )

    assert (
        decision["jins"]
        is None
    )

    assert (
        decision["confidence"]
        is None
    )


# ============================================================
# TEST 13
# ============================================================

def test_protection():
    e = TonicDecisionReadinessAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
        conflict_data=conflict_fixture(),
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
            "original_decision_overridden"
        ]
        is False
    )

    assert (
        protection[
            "readiness_promoted_to_decision"
        ]
        is False
    )


# ============================================================
# TEST 14
# ============================================================

def test_candidate_generation():
    e = TonicDecisionReadinessAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
        conflict_data=conflict_fixture(),
        candidates=[7, 0],
    )

    candidates = (
        result["readiness"]["candidates"]
    )

    names = [
        x["tonic"]
        for x in candidates
    ]

    assert names == [
        "G",
        "C",
    ]


# ============================================================
# TEST 15
# ============================================================

def test_thresholds_present():
    e = TonicDecisionReadinessAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
        conflict_data=conflict_fixture(),
        candidates=[7, 0],
    )

    thresholds = result[
        "thresholds"
    ]

    assert (
        thresholds[
            "min_overall_reliability"
        ]
        == 0.55
    )

    assert (
        thresholds[
            "min_consensus_quality"
        ]
        == 0.60
    )

    assert (
        thresholds[
            "max_conflict_score"
        ]
        == 0.35
    )

    assert (
        thresholds[
            "min_support_margin"
        ]
        == 0.15
    )


# ============================================================
# TEST 16
# ============================================================

def test_no_pitch_correction():
    e = TonicDecisionReadinessAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
        conflict_data=conflict_fixture(),
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


# ============================================================
# RUNNER
# ============================================================

def run():

    print("PhoenixVoiceEngine")
    print(
        "Tonic Decision Readiness Analyzer V1.0"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_consensus_extraction,
        test_reliability_extraction,
        test_conflict_extraction,
        test_preferences,
        test_meaningful_component_count,
        test_candidate_readiness_g,
        test_candidate_readiness_c,
        test_bender_not_ready,
        test_blockers_present,
        test_candidate_checks,
        test_readiness_never_becomes_decision,
        test_protection,
        test_candidate_generation,
        test_thresholds_present,
        test_no_pitch_correction,
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