"""
PhoenixVoiceEngine
Tonic Decision Gate V1.0 Tests
"""

from src.maqam.tonic_decision_gate import TonicDecisionGate


def readiness_fixture_ready():
    return {
        "readiness": {
            "global": {
                "status": "READY",
                "readiness_score": 0.95,
                "top_candidate": "C",
                "top_readiness": 0.95,
                "second_candidate": "G",
                "second_readiness": 0.40,
                "global_blockers": [],
            },
            "candidates": [
                {
                    "tonic": "C",
                    "status": "READY",
                    "readiness_score": 0.95,
                    "supporting_components": [
                        "stable_center",
                        "intervallic_relationship",
                    ],
                    "opposing_components": [],
                    "blockers": [],
                    "checks": {
                        "overall_reliability": True,
                        "consensus_quality": True,
                        "agreement": True,
                    },
                }
            ],
        }
    }


def readiness_fixture_not_ready():
    return {
        "readiness": {
            "global": {
                "status": "NOT_READY",
                "readiness_score": 0.35,
                "top_candidate": "C",
                "top_readiness": 0.35,
                "second_candidate": "G",
                "second_readiness": 0.30,
                "global_blockers": [
                    "OVERALL_RELIABILITY_BELOW_THRESHOLD",
                    "CONSENSUS_QUALITY_BELOW_THRESHOLD",
                    "MEANINGFUL_G_C_CONFLICT",
                ],
            },
            "candidates": [
                {
                    "tonic": "C",
                    "status": "NOT_READY",
                    "readiness_score": 0.35,
                    "supporting_components": [
                        "stable_center",
                    ],
                    "opposing_components": [
                        "functional",
                    ],
                    "blockers": [
                        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT",
                    ],
                    "checks": {
                        "overall_reliability": False,
                        "consensus_quality": False,
                        "agreement": False,
                    },
                },
                {
                    "tonic": "G",
                    "status": "NOT_READY",
                    "readiness_score": 0.30,
                    "supporting_components": [
                        "functional",
                    ],
                    "opposing_components": [
                        "stable_center",
                    ],
                    "blockers": [
                        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT",
                    ],
                    "checks": {
                        "overall_reliability": False,
                        "consensus_quality": False,
                        "agreement": False,
                    },
                },
            ],
        }
    }


def reliability_fixture_ready():
    return {
        "reliability": {
            "overall_score": 0.82
        }
    }


def reliability_fixture_not_ready():
    return {
        "reliability": {
            "overall_score": 0.374311
        }
    }


def consensus_fixture_ready():
    return {
        "consensus": {
            "status": "STRONG_CONSENSUS",
            "agreement": {
                "agreement_score": 0.82,
                "conflict_score": 0.18,
                "weighted_agreement": 0.82,
                "dominant_tonic": "C",
                "dominant_share": 0.82,
            },
            "quality": {
                "top_tonic": "C",
                "support_share": 0.82,
                "support_margin": 0.32,
                "consensus_quality": 0.82,
            },
        }
    }


def consensus_fixture_not_ready():
    return {
        "consensus": {
            "status": "MODERATE_CONSENSUS",
            "agreement": {
                "agreement_score": 0.456026,
                "conflict_score": 0.543974,
                "weighted_agreement": 0.412051,
                "dominant_tonic": "G",
                "dominant_share": 0.5,
            },
            "quality": {
                "top_tonic": "C",
                "support_share": 0.642711,
                "support_margin": 0.080822,
                "consensus_quality": 0.455721,
            },
        }
    }


def conflict_fixture_ready():
    return {
        "conflict": {
            "balance": {
                "weighted_preference": "C",
                "dominance": 0.82,
            },
            "severity": {
                "score": 0.18,
                "label": "LOW",
                "meaningful_G_components": 0,
                "meaningful_C_components": 2,
            },
        }
    }


def conflict_fixture_not_ready():
    return {
        "conflict": {
            "balance": {
                "weighted_preference": "C",
                "dominance": 0.751351,
            },
            "severity": {
                "score": 0.444383,
                "label": "LOW",
                "meaningful_G_components": 1,
                "meaningful_C_components": 1,
            },
        }
    }


# ============================================================
# TEST 1
# ============================================================

def test_build():
    e = TonicDecisionGate()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.0"


# ============================================================
# TEST 2
# ============================================================

def test_readiness_extraction():
    e = TonicDecisionGate()

    result = e._extract_readiness(
        readiness_fixture_not_ready()
    )

    assert result["status"] == "NOT_READY"
    assert result["readiness_score"] == 0.35
    assert result["top_candidate"] == "C"

    assert (
        "MEANINGFUL_G_C_CONFLICT"
        in result["global_blockers"]
    )


# ============================================================
# TEST 3
# ============================================================

def test_reliability_extraction():
    e = TonicDecisionGate()

    result = e._extract_reliability(
        reliability_fixture_not_ready()
    )

    assert (
        result["overall_score"]
        == 0.374311
    )


# ============================================================
# TEST 4
# ============================================================

def test_consensus_extraction():
    e = TonicDecisionGate()

    result = e._extract_consensus(
        consensus_fixture_not_ready()
    )

    assert (
        result["agreement_score"]
        == 0.456026
    )

    assert (
        result["conflict_score"]
        == 0.543974
    )

    assert (
        result["consensus_quality"]
        == 0.455721
    )

    assert (
        result["top_tonic"]
        == "C"
    )


# ============================================================
# TEST 5
# ============================================================

def test_conflict_extraction():
    e = TonicDecisionGate()

    result = e._extract_conflict(
        conflict_fixture_not_ready()
    )

    assert (
        result["severity_score"]
        == 0.444383
    )

    assert (
        result["meaningful_G_components"]
        == 1
    )

    assert (
        result["meaningful_C_components"]
        == 1
    )


# ============================================================
# TEST 6
# ============================================================

def test_not_ready_checks():
    e = TonicDecisionGate()

    readiness = e._extract_readiness(
        readiness_fixture_not_ready()
    )

    reliability = e._extract_reliability(
        reliability_fixture_not_ready()
    )

    consensus = e._extract_consensus(
        consensus_fixture_not_ready()
    )

    conflict = e._extract_conflict(
        conflict_fixture_not_ready()
    )

    checks = e._build_checks(
        readiness,
        reliability,
        consensus,
        conflict,
    )

    assert (
        checks["readiness_status_ready"]
        is False
    )

    assert (
        checks["readiness_score"]
        is False
    )

    assert (
        checks["overall_reliability"]
        is False
    )

    assert (
        checks["consensus_quality"]
        is False
    )

    assert (
        checks["agreement_score"]
        is False
    )

    assert (
        checks["conflict_score"]
        is False
    )

    assert (
        checks["no_meaningful_G_C_conflict"]
        is False
    )


# ============================================================
# TEST 7
# ============================================================

def test_not_ready_gate():
    e = TonicDecisionGate()

    result = e.analyze(
        readiness_data=readiness_fixture_not_ready(),
        reliability_data=reliability_fixture_not_ready(),
        consensus_data=consensus_fixture_not_ready(),
        conflict_data=conflict_fixture_not_ready(),
    )

    gate = result["gate"]

    assert (
        gate["status"]
        == "CLOSED"
    )

    assert (
        gate["level"]
        == "ABSTAIN"
    )

    assert (
        gate["decision_allowed"]
        is False
    )

    assert (
        gate["abstention_required"]
        is True
    )


# ============================================================
# TEST 8
# ============================================================

def test_not_ready_blockers():
    e = TonicDecisionGate()

    result = e.analyze(
        readiness_data=readiness_fixture_not_ready(),
        reliability_data=reliability_fixture_not_ready(),
        consensus_data=consensus_fixture_not_ready(),
        conflict_data=conflict_fixture_not_ready(),
    )

    blockers = result[
        "gate"
    ]["blockers"]

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
        "MEANINGFUL_G_C_CONFLICT"
        in blockers
    )


# ============================================================
# TEST 9
# ============================================================

def test_ready_checks():
    e = TonicDecisionGate()

    readiness = e._extract_readiness(
        readiness_fixture_ready()
    )

    reliability = e._extract_reliability(
        reliability_fixture_ready()
    )

    consensus = e._extract_consensus(
        consensus_fixture_ready()
    )

    conflict = e._extract_conflict(
        conflict_fixture_ready()
    )

    checks = e._build_checks(
        readiness,
        reliability,
        consensus,
        conflict,
    )

    assert all(
        checks.values()
    )


# ============================================================
# TEST 10
# ============================================================

def test_ready_gate():
    e = TonicDecisionGate()

    result = e.analyze(
        readiness_data=readiness_fixture_ready(),
        reliability_data=reliability_fixture_ready(),
        consensus_data=consensus_fixture_ready(),
        conflict_data=conflict_fixture_ready(),
    )

    gate = result["gate"]

    assert (
        gate["status"]
        == "OPEN"
    )

    assert (
        gate["level"]
        == "ALLOW"
    )

    assert (
        gate["decision_allowed"]
        is True
    )

    assert (
        gate["abstention_required"]
        is False
    )


# ============================================================
# TEST 11
# ============================================================

def test_candidate_gate():
    e = TonicDecisionGate()

    result = e.analyze(
        readiness_data=readiness_fixture_ready(),
        reliability_data=reliability_fixture_ready(),
        consensus_data=consensus_fixture_ready(),
        conflict_data=conflict_fixture_ready(),
    )

    candidates = result[
        "candidate_gates"
    ]

    assert len(candidates) == 1

    candidate = candidates[0]

    assert (
        candidate["tonic"]
        == "C"
    )

    assert (
        candidate["status"]
        == "OPEN"
    )

    assert (
        candidate["decision_allowed"]
        is True
    )


# ============================================================
# TEST 12
# ============================================================

def test_gate_never_selects_tonic():
    e = TonicDecisionGate()

    result = e.analyze(
        readiness_data=readiness_fixture_ready(),
        reliability_data=reliability_fixture_ready(),
        consensus_data=consensus_fixture_ready(),
        conflict_data=conflict_fixture_ready(),
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
    e = TonicDecisionGate()

    result = e.analyze(
        readiness_data=readiness_fixture_not_ready(),
        reliability_data=reliability_fixture_not_ready(),
        consensus_data=consensus_fixture_not_ready(),
        conflict_data=conflict_fixture_not_ready(),
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
            "gate_selected_tonic"
        ]
        is False
    )


# ============================================================
# TEST 14
# ============================================================

def test_thresholds():
    e = TonicDecisionGate()

    assert (
        e.MIN_READINESS_SCORE
        == 0.80
    )

    assert (
        e.MIN_OVERALL_RELIABILITY
        == 0.55
    )

    assert (
        e.MIN_CONSENSUS_QUALITY
        == 0.60
    )

    assert (
        e.MIN_AGREEMENT_SCORE
        == 0.60
    )

    assert (
        e.MAX_CONFLICT_SCORE
        == 0.35
    )

    assert (
        e.MAX_CONFLICT_SEVERITY
        == 0.40
    )


# ============================================================
# TEST 15
# ============================================================

def test_candidate_blocked_by_opposition():
    e = TonicDecisionGate()

    candidate = {
        "tonic": "C",
        "status": "READY",
        "readiness_score": 0.95,
        "supporting_components": [
            "stable_center",
        ],
        "opposing_components": [
            "functional",
        ],
        "blockers": [
            "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
        ],
        "checks": {
            "overall_reliability": True,
            "consensus_quality": True,
            "agreement": True,
            "no_meaningful_opposition": False,
        },
    }

    result = e._candidate_gate(
        candidate
    )

    assert (
        result["status"]
        == "CLOSED"
    )

    assert (
        result["decision_allowed"]
        is False
    )


# ============================================================
# TEST 16
# ============================================================

def test_bender_must_abstain():
    e = TonicDecisionGate()

    result = e.analyze(
        readiness_data=readiness_fixture_not_ready(),
        reliability_data=reliability_fixture_not_ready(),
        consensus_data=consensus_fixture_not_ready(),
        conflict_data=conflict_fixture_not_ready(),
    )

    assert (
        result["gate"]["status"]
        == "CLOSED"
    )

    assert (
        result["gate"]["level"]
        == "ABSTAIN"
    )

    assert (
        result["gate"]["decision_allowed"]
        is False
    )

    assert (
        result["decision"]["status"]
        == "EVIDENCE_ONLY"
    )


# ============================================================
# RUNNER
# ============================================================

def run():

    print("PhoenixVoiceEngine")
    print(
        "Tonic Decision Gate V1.0"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_readiness_extraction,
        test_reliability_extraction,
        test_consensus_extraction,
        test_conflict_extraction,
        test_not_ready_checks,
        test_not_ready_gate,
        test_not_ready_blockers,
        test_ready_checks,
        test_ready_gate,
        test_candidate_gate,
        test_gate_never_selects_tonic,
        test_protection,
        test_thresholds,
        test_candidate_blocked_by_opposition,
        test_bender_must_abstain,
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