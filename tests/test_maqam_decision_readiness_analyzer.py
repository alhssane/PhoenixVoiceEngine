"""
PhoenixVoiceEngine
Maqam Decision Readiness Analyzer V1.0
"""

from src.maqam.maqam_decision_readiness_analyzer import (
    MaqamDecisionReadinessAnalyzer,
)


# ============================================================
# Fixtures
# ============================================================

def ready_tonic():
    return {
        "status": "DECIDED",
        "tonic_pitch_class": 0,
        "tonic_name": "C",
    }


def abstained_tonic():
    return {
        "status": "ABSTAIN",
        "tonic_pitch_class": None,
        "tonic_name": None,
    }


def rast_candidate():
    return {
        "maqam": "Rast",
        "tonic_pitch_class": 0,
        "tonic_name": "C",
        "readiness_score": 0.90,
        "candidate_support": 0.85,
        "support_share": 0.75,
        "support_margin": 0.25,
        "support_rank": 1,
        "supporting_components": [
            "maqam_structure",
            "jins_compatibility",
        ],
        "strong_candidate_components": 2,
        "opposing_components": [],
        "meaningful_opposing_components": 0,
        "blockers": [],
        "status": "READY",
    }


def bayati_candidate():
    return {
        "maqam": "Bayati",
        "tonic_pitch_class": 0,
        "tonic_name": "C",
        "readiness_score": 0.35,
        "candidate_support": 0.30,
        "support_share": 0.25,
        "support_margin": -0.20,
        "support_rank": 2,
        "supporting_components": [
            "maqam_structure",
        ],
        "strong_candidate_components": 0,
        "opposing_components": [
            "weak_structure",
        ],
        "meaningful_opposing_components": 1,
        "blockers": [
            "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT",
        ],
        "status": "NOT_READY",
    }


def good_consensus():
    return {
        "consensus": {
            "agreement": {
                "agreement_score": 0.80,
                "conflict_score": 0.20,
            },
            "quality": {
                "consensus_quality": 0.85,
            },
        }
    }


def bad_consensus():
    return {
        "consensus": {
            "agreement": {
                "agreement_score": 0.30,
                "conflict_score": 0.70,
            },
            "quality": {
                "consensus_quality": 0.35,
            },
        }
    }


def good_reliability():
    return {
        "reliability": {
            "overall_score": 0.85,
        }
    }


def bad_reliability():
    return {
        "reliability": {
            "overall_score": 0.30,
        }
    }


def good_conflict():
    return {
        "conflict": {
            "severity": {
                "score": 0.20,
                "label": "LOW",
                "meaningful_G_components": 0,
                "meaningful_C_components": 0,
            },
            "balance": {
                "conflict_score": 0.20,
            },
        }
    }


def bad_conflict():
    return {
        "conflict": {
            "severity": {
                "score": 0.80,
                "label": "HIGH",
                "meaningful_G_components": 1,
                "meaningful_C_components": 1,
            },
            "balance": {
                "conflict_score": 0.70,
            },
        }
    }


# ============================================================
# TEST 1
# ============================================================

def test_build():

    e = MaqamDecisionReadinessAnalyzer()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.0"


# ============================================================
# TEST 2
# ============================================================

def test_candidate_extraction():

    e = MaqamDecisionReadinessAnalyzer()

    data = {
        "candidates": [
            rast_candidate(),
            bayati_candidate(),
        ]
    }

    candidates = e._extract_candidates(
        data
    )

    assert len(candidates) == 2
    assert candidates[0]["maqam"] == "Rast"
    assert candidates[1]["maqam"] == "Bayati"


# ============================================================
# TEST 3
# ============================================================

def test_tonic_extraction():

    e = MaqamDecisionReadinessAnalyzer()

    data = {
        "decision": ready_tonic()
    }

    tonic = e._extract_tonic_decision(
        data
    )

    assert tonic["status"] == "DECIDED"
    assert tonic["tonic_pitch_class"] == 0
    assert tonic["tonic_name"] == "C"


# ============================================================
# TEST 4
# ============================================================

def test_reliability_extraction():

    e = MaqamDecisionReadinessAnalyzer()

    value = e._extract_reliability(
        good_reliability()
    )

    assert value == 0.85


# ============================================================
# TEST 5
# ============================================================

def test_consensus_extraction():

    e = MaqamDecisionReadinessAnalyzer()

    result = e._extract_consensus(
        good_consensus()
    )

    assert result["agreement_score"] == 0.80
    assert result["conflict_score"] == 0.20
    assert result["quality"] == 0.85


# ============================================================
# TEST 6
# ============================================================

def test_conflict_extraction():

    e = MaqamDecisionReadinessAnalyzer()

    result = e._extract_conflict(
        good_conflict()
    )

    assert result["severity"] == 0.20
    assert result["conflict_score"] == 0.20
    assert result["label"] == "LOW"
    assert result["meaningful_opposition"] is False


# ============================================================
# TEST 7
# ============================================================

def test_ready_candidate():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        rast_candidate(),
        0.85,
        0.85,
        0.80,
        0.20,
        0.20,
        ready_tonic(),
    )

    assert result["maqam"] == "Rast"
    assert result["status"] == "READY"
    assert result["blockers"] == []


# ============================================================
# TEST 8
# ============================================================

def test_not_ready_candidate():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        bayati_candidate(),
        0.85,
        0.85,
        0.80,
        0.20,
        0.20,
        ready_tonic(),
    )

    assert result["status"] == "NOT_READY"
    assert len(result["blockers"]) > 0


# ============================================================
# TEST 9
# ============================================================

def test_low_reliability_blocks():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        rast_candidate(),
        0.30,
        0.85,
        0.80,
        0.20,
        0.20,
        ready_tonic(),
    )

    assert result["status"] == "NOT_READY"

    assert (
        "OVERALL_RELIABILITY_BELOW_THRESHOLD"
        in result["blockers"]
    )


# ============================================================
# TEST 10
# ============================================================

def test_low_consensus_blocks():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        rast_candidate(),
        0.85,
        0.35,
        0.30,
        0.20,
        0.20,
        ready_tonic(),
    )

    assert result["status"] == "NOT_READY"

    assert (
        "CONSENSUS_QUALITY_BELOW_THRESHOLD"
        in result["blockers"]
    )

    assert (
        "AGREEMENT_BELOW_THRESHOLD"
        in result["blockers"]
    )


# ============================================================
# TEST 11
# ============================================================

def test_high_conflict_blocks():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        rast_candidate(),
        0.85,
        0.85,
        0.80,
        0.70,
        0.80,
        ready_tonic(),
    )

    assert result["status"] == "NOT_READY"

    assert (
        "CONFLICT_SCORE_TOO_HIGH"
        in result["blockers"]
    )

    assert (
        "CONFLICT_SEVERITY_TOO_HIGH"
        in result["blockers"]
    )


# ============================================================
# TEST 12
# ============================================================

def test_low_candidate_support_blocks():

    candidate = rast_candidate()

    candidate["candidate_support"] = 0.20

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        candidate,
        0.85,
        0.85,
        0.80,
        0.20,
        0.20,
        ready_tonic(),
    )

    assert result["status"] == "NOT_READY"

    assert (
        "CANDIDATE_SUPPORT_BELOW_THRESHOLD"
        in result["blockers"]
    )


# ============================================================
# TEST 13
# ============================================================

def test_low_support_margin_blocks():

    candidate = rast_candidate()

    candidate["support_margin"] = 0.02

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        candidate,
        0.85,
        0.85,
        0.80,
        0.20,
        0.20,
        ready_tonic(),
    )

    assert result["status"] == "NOT_READY"

    assert (
        "SUPPORT_MARGIN_BELOW_THRESHOLD"
        in result["blockers"]
    )


# ============================================================
# TEST 14
# ============================================================

def test_meaningful_opposition_blocks():

    candidate = rast_candidate()

    candidate[
        "meaningful_opposing_components"
    ] = 1

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        candidate,
        0.85,
        0.85,
        0.80,
        0.20,
        0.20,
        ready_tonic(),
    )

    assert result["status"] == "NOT_READY"

    assert (
        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
        in result["blockers"]
    )


# ============================================================
# TEST 15
# ============================================================

def test_tonic_not_decided_blocks():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        rast_candidate(),
        0.85,
        0.85,
        0.80,
        0.20,
        0.20,
        abstained_tonic(),
    )

    assert result["status"] == "NOT_READY"

    assert (
        "TONIC_DECISION_NOT_AVAILABLE"
        in result["blockers"]
    )


# ============================================================
# TEST 16
# ============================================================

def test_tonic_mismatch_blocks():

    tonic = {
        "status": "DECIDED",
        "tonic_pitch_class": 7,
        "tonic_name": "G",
    }

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        rast_candidate(),
        0.85,
        0.85,
        0.80,
        0.20,
        0.20,
        tonic,
    )

    assert result["status"] == "NOT_READY"

    assert (
        "TONIC_MISMATCH"
        in result["blockers"]
    )


# ============================================================
# TEST 17
# ============================================================

def test_global_ready():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        good_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    assert (
        result["readiness"]["global"]["status"]
        == "READY"
    )

    assert (
        result["readiness"]["global"]["global_blockers"]
        == []
    )


# ============================================================
# TEST 18
# ============================================================

def test_global_not_ready_from_reliability():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        bad_reliability(),
        good_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    assert (
        result["readiness"]["global"]["status"]
        == "NOT_READY"
    )

    assert (
        "OVERALL_RELIABILITY_BELOW_THRESHOLD"
        in result["readiness"]["global"]["global_blockers"]
    )


# ============================================================
# TEST 19
# ============================================================

def test_global_not_ready_from_conflict():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        bad_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    assert (
        result["readiness"]["global"]["status"]
        == "NOT_READY"
    )

    assert (
        "CONFLICT_SCORE_TOO_HIGH"
        in result["readiness"]["global"]["global_blockers"]
    )

    assert (
        "CONFLICT_SEVERITY_TOO_HIGH"
        in result["readiness"]["global"]["global_blockers"]
    )


# ============================================================
# TEST 20
# ============================================================

def test_abstained_tonic_never_becomes_ready():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        good_conflict(),
        {
            "decision": abstained_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    assert (
        result["readiness"]["global"]["status"]
        == "NOT_READY"
    )

    assert (
        "TONIC_DECISION_NOT_AVAILABLE"
        in result["readiness"]["global"]["global_blockers"]
    )


# ============================================================
# TEST 21
# ============================================================

def test_candidate_generation_and_ranking():

    e = MaqamDecisionReadinessAnalyzer()

    weak = bayati_candidate()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        good_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            weak,
            rast_candidate(),
        ],
    )

    candidates = (
        result["readiness"]["candidates"]
    )

    assert len(candidates) == 2

    assert (
        candidates[0]["maqam"]
        == "Rast"
    )

    assert (
        candidates[1]["maqam"]
        == "Bayati"
    )


# ============================================================
# TEST 22
# ============================================================

def test_readiness_score_range():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        good_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    score = (
        result["readiness"]["global"][
            "readiness_score"
        ]
    )

    assert 0.0 <= score <= 1.0


# ============================================================
# TEST 23
# ============================================================

def test_candidate_readiness_ratio_range():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        good_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    candidate = (
        result["readiness"]["candidates"][0]
    )

    assert (
        0.0
        <= candidate["readiness_ratio"]
        <= 1.0
    )


# ============================================================
# TEST 24
# ============================================================

def test_readiness_is_not_decision():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        good_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    decision = result["decision"]

    assert (
        decision["status"]
        == "EVIDENCE_ONLY"
    )

    assert decision["maqam"] is None
    assert decision["jins"] is None
    assert (
        decision["confidence"]
        is None
    )

    assert (
        "READINESS_IS_NOT_A_MAQAM_DECISION"
        in decision["reason"]
    )


# ============================================================
# TEST 25
# ============================================================

def test_no_jins_decision():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        good_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    assert (
        result["decision"]["jins"]
        is None
    )

    assert (
        result["protection"][
            "jins_decision_made"
        ]
        is False
    )


# ============================================================
# TEST 26
# ============================================================

def test_protection():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        good_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    protection = (
        result["protection"]
    )

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
            "source_audio_modified"
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
            "original_scores_preserved"
        ]
        is True
    )


# ============================================================
# TEST 27
# ============================================================

def test_thresholds_present():

    e = MaqamDecisionReadinessAnalyzer()

    assert (
        0.0
        <= e.MIN_OVERALL_RELIABILITY
        <= 1.0
    )

    assert (
        0.0
        <= e.MIN_CONSENSUS_QUALITY
        <= 1.0
    )

    assert (
        0.0
        <= e.MIN_AGREEMENT_SCORE
        <= 1.0
    )

    assert (
        0.0
        <= e.MAX_CONFLICT_SCORE
        <= 1.0
    )

    assert (
        0.0
        <= e.MAX_CONFLICT_SEVERITY
        <= 1.0
    )

    assert (
        0.0
        <= e.MIN_READINESS_SCORE
        <= 1.0
    )

    assert (
        0.0
        <= e.MIN_SUPPORT_SHARE
        <= 1.0
    )

    assert (
        e.MIN_SUPPORT_MARGIN
        >= 0.0
    )


# ============================================================
# TEST 28
# ============================================================

def test_meaningful_conflicting_evidence_detected():

    e = MaqamDecisionReadinessAnalyzer()

    result = e._extract_conflict(
        bad_conflict()
    )

    assert (
        result["meaningful_opposition"]
        is True
    )


# ============================================================
# TEST 29
# ============================================================

def test_candidate_status_not_ready_with_blocker():

    candidate = rast_candidate()

    candidate["status"] = "READY"
    candidate["blockers"] = [
        "EXTERNAL_BLOCKER"
    ]

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze_candidate(
        candidate,
        0.85,
        0.85,
        0.80,
        0.20,
        0.20,
        ready_tonic(),
    )

    assert result["status"] == "NOT_READY"

    assert (
        "EXTERNAL_BLOCKER"
        in result["blockers"]
    )


# ============================================================
# TEST 30
# ============================================================

def test_evidence_only_flag():

    e = MaqamDecisionReadinessAnalyzer()

    result = e.analyze(
        good_consensus(),
        good_reliability(),
        good_conflict(),
        {
            "decision": ready_tonic()
        },
        candidates=[
            rast_candidate()
        ],
    )

    for candidate in (
        result["readiness"]["candidates"]
    ):
        assert (
            candidate["evidence_only"]
            is True
        )


# ============================================================
# RUNNER
# ============================================================

def run():

    print("PhoenixVoiceEngine")
    print(
        "Maqam Decision Readiness Analyzer V1.0"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_candidate_extraction,
        test_tonic_extraction,
        test_reliability_extraction,
        test_consensus_extraction,
        test_conflict_extraction,
        test_ready_candidate,
        test_not_ready_candidate,
        test_low_reliability_blocks,
        test_low_consensus_blocks,
        test_high_conflict_blocks,
        test_low_candidate_support_blocks,
        test_low_support_margin_blocks,
        test_meaningful_opposition_blocks,
        test_tonic_not_decided_blocks,
        test_tonic_mismatch_blocks,
        test_global_ready,
        test_global_not_ready_from_reliability,
        test_global_not_ready_from_conflict,
        test_abstained_tonic_never_becomes_ready,
        test_candidate_generation_and_ranking,
        test_readiness_score_range,
        test_candidate_readiness_ratio_range,
        test_readiness_is_not_decision,
        test_no_jins_decision,
        test_protection,
        test_thresholds_present,
        test_meaningful_conflicting_evidence_detected,
        test_candidate_status_not_ready_with_blocker,
        test_evidence_only_flag,
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