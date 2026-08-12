"""
PhoenixVoiceEngine
Maqam Decision Gate V1.0
Tests
"""

from src.maqam.maqam_decision_gate import (
    MaqamDecisionGate,
)


# ============================================================
# Fixtures
# ============================================================

def ready_readiness():
    return {
        "readiness": {
            "global": {
                "status": "READY",
                "readiness_score": 0.85,
                "top_candidate": "Rast",
                "top_readiness": 0.85,
                "second_candidate": "Bayati",
                "second_readiness": 0.35,
                "global_blockers": [],
            },
            "candidates": [
                {
                    "maqam": "Rast",
                    "tonic_pitch_class": 0,
                    "readiness_score": 0.85,
                    "candidate_support": 0.85,
                    "support_share": 0.75,
                    "support_margin": 0.25,
                    "status": "READY",
                    "blockers": [],
                    "supporting_components": [
                        "maqam_structure",
                        "jins_compatibility",
                    ],
                    "opposing_components": [],
                    "meaningful_opposing_components": 0,
                }
            ],
        }
    }


def not_ready_readiness():
    return {
        "readiness": {
            "global": {
                "status": "NOT_READY",
                "readiness_score": 0.35,
                "top_candidate": "Rast",
                "top_readiness": 0.35,
                "second_candidate": "Bayati",
                "second_readiness": 0.20,
                "global_blockers": [
                    "OVERALL_RELIABILITY_BELOW_THRESHOLD",
                ],
            },
            "candidates": [
                {
                    "maqam": "Rast",
                    "tonic_pitch_class": 0,
                    "readiness_score": 0.35,
                    "candidate_support": 0.30,
                    "support_share": 0.30,
                    "support_margin": 0.02,
                    "status": "NOT_READY",
                    "blockers": [
                        "OVERALL_RELIABILITY_BELOW_THRESHOLD",
                    ],
                    "supporting_components": [],
                    "opposing_components": [
                        "weak_structure",
                    ],
                    "meaningful_opposing_components": 1,
                }
            ],
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
                "consensus_quality": 0.30,
            },
        }
    }


def good_conflict():
    return {
        "conflict": {
            "balance": {
                "conflict_score": 0.20,
            },
            "severity": {
                "score": 0.20,
                "label": "LOW",
                "meaningful_G_components": 0,
                "meaningful_C_components": 0,
            },
        }
    }


def bad_conflict():
    return {
        "conflict": {
            "balance": {
                "conflict_score": 0.70,
            },
            "severity": {
                "score": 0.80,
                "label": "HIGH",
                "meaningful_G_components": 1,
                "meaningful_C_components": 1,
            },
        }
    }


def decided_tonic():
    return {
        "decision": {
            "status": "DECIDED",
            "tonic_pitch_class": 0,
            "tonic_name": "C",
        }
    }


def abstained_tonic():
    return {
        "decision": {
            "status": "ABSTAIN",
            "tonic_pitch_class": None,
            "tonic_name": None,
        }
    }


# ============================================================
# TEST 1
# ============================================================

def test_build():

    e = MaqamDecisionGate()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.0"


# ============================================================
# TEST 2
# ============================================================

def test_readiness_extraction():

    e = MaqamDecisionGate()

    result = e._extract_readiness(
        ready_readiness()
    )

    assert result["status"] == "READY"
    assert result["readiness_score"] == 0.85
    assert result["top_candidate"] == "Rast"
    assert result["top_readiness"] == 0.85
    assert len(result["candidates"]) == 1


# ============================================================
# TEST 3
# ============================================================

def test_reliability_extraction():

    e = MaqamDecisionGate()

    assert (
        e._extract_reliability(
            good_reliability()
        )
        == 0.85
    )


# ============================================================
# TEST 4
# ============================================================

def test_consensus_extraction():

    e = MaqamDecisionGate()

    result = e._extract_consensus(
        good_consensus()
    )

    assert result["quality"] == 0.85
    assert result["agreement_score"] == 0.80
    assert result["conflict_score"] == 0.20


# ============================================================
# TEST 5
# ============================================================

def test_conflict_extraction():

    e = MaqamDecisionGate()

    result = e._extract_conflict(
        good_conflict()
    )

    assert result["severity"] == 0.20
    assert result["conflict_score"] == 0.20
    assert result["label"] == "LOW"
    assert result["meaningful_opposition"] is False


# ============================================================
# TEST 6
# ============================================================

def test_tonic_extraction():

    e = MaqamDecisionGate()

    result = e._extract_tonic_decision(
        decided_tonic()
    )

    assert result["status"] == "DECIDED"
    assert result["tonic_pitch_class"] == 0
    assert result["tonic_name"] == "C"


# ============================================================
# TEST 7
# ============================================================

def test_candidate_gate_ready():

    e = MaqamDecisionGate()

    candidate = e._extract_candidate(
        ready_readiness()[
            "readiness"
        ]["candidates"][0]
    )

    result = e._candidate_gate(
        candidate,
        e._extract_tonic_decision(
            decided_tonic()
        ),
    )

    assert result["status"] == "OPEN"
    assert result["decision_allowed"] is True
    assert result["blockers"] == []


# ============================================================
# TEST 8
# ============================================================

def test_candidate_gate_not_ready():

    e = MaqamDecisionGate()

    candidate = e._extract_candidate(
        not_ready_readiness()[
            "readiness"
        ]["candidates"][0]
    )

    result = e._candidate_gate(
        candidate,
        e._extract_tonic_decision(
            decided_tonic()
        ),
    )

    assert result["status"] == "CLOSED"
    assert result["decision_allowed"] is False
    assert len(result["blockers"]) > 0


# ============================================================
# TEST 9
# ============================================================

def test_closed_readiness_closes_gate():

    e = MaqamDecisionGate()

    result = e.analyze(
        not_ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert result["gate"]["status"] == "CLOSED"
    assert result["gate"]["decision_allowed"] is False
    assert result["gate"]["abstention_required"] is True

    assert (
        "READINESS_STATUS_NOT_READY"
        in result["gate"]["blockers"]
    )


# ============================================================
# TEST 10
# ============================================================

def test_low_reliability_closes_gate():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        bad_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert result["gate"]["status"] == "CLOSED"

    assert (
        "OVERALL_RELIABILITY_BELOW_THRESHOLD"
        in result["gate"]["blockers"]
    )


# ============================================================
# TEST 11
# ============================================================

def test_low_consensus_closes_gate():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        bad_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert result["gate"]["status"] == "CLOSED"

    assert (
        "CONSENSUS_QUALITY_BELOW_THRESHOLD"
        in result["gate"]["blockers"]
    )

    assert (
        "AGREEMENT_BELOW_THRESHOLD"
        in result["gate"]["blockers"]
    )


# ============================================================
# TEST 12
# ============================================================

def test_high_conflict_closes_gate():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        bad_conflict(),
        decided_tonic(),
    )

    assert result["gate"]["status"] == "CLOSED"

    assert (
        "CONFLICT_SCORE_TOO_HIGH"
        in result["gate"]["blockers"]
    )

    assert (
        "CONFLICT_SEVERITY_TOO_HIGH"
        in result["gate"]["blockers"]
    )


# ============================================================
# TEST 13
# ============================================================

def test_abstained_tonic_closes_gate():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        abstained_tonic(),
    )

    assert result["gate"]["status"] == "CLOSED"
    assert result["gate"]["decision_allowed"] is False

    assert (
        "TONIC_DECISION_NOT_AVAILABLE"
        in result["gate"]["blockers"]
    )


# ============================================================
# TEST 14
# ============================================================

def test_open_gate_with_valid_evidence():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert result["gate"]["status"] == "OPEN"
    assert result["gate"]["level"] == "ALLOW"
    assert result["gate"]["decision_allowed"] is True
    assert result["gate"]["abstention_required"] is False
    assert result["gate"]["blockers"] == []


# ============================================================
# TEST 15
# ============================================================

def test_open_gate_does_not_select_maqam():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert result["decision"]["status"] == "EVIDENCE_ONLY"
    assert result["decision"]["maqam"] is None
    assert result["decision"]["jins"] is None
    assert result["decision"]["confidence"] is None

    assert (
        result["decision_safety"]["maqam_selected"]
        is False
    )


# ============================================================
# TEST 16
# ============================================================

def test_gate_never_selects_tonic():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert (
        result["decision"]["tonic_pitch_class"]
        is None
    )

    assert (
        result["decision"]["tonic_name"]
        is None
    )

    assert (
        result["decision_safety"]["tonic_selected"]
        is False
    )


# ============================================================
# TEST 17
# ============================================================

def test_gate_never_selects_jins():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert result["decision"]["jins"] is None

    assert (
        result["decision_safety"]["jins_selected"]
        is False
    )


# ============================================================
# TEST 18
# ============================================================

def test_candidate_tonic_mismatch_closes_candidate():

    e = MaqamDecisionGate()

    candidate = e._extract_candidate(
        ready_readiness()[
            "readiness"
        ]["candidates"][0]
    )

    tonic = {
        "status": "DECIDED",
        "tonic_pitch_class": 7,
        "tonic_name": "G",
    }

    result = e._candidate_gate(
        candidate,
        tonic,
    )

    assert result["status"] == "CLOSED"
    assert result["decision_allowed"] is False

    assert (
        "TONIC_MISMATCH"
        in result["blockers"]
    )


# ============================================================
# TEST 19
# ============================================================

def test_candidate_with_opposition_closed():

    e = MaqamDecisionGate()

    candidate_data = (
        ready_readiness()[
            "readiness"
        ]["candidates"][0].copy()
    )

    candidate_data[
        "meaningful_opposing_components"
    ] = 1

    candidate = e._extract_candidate(
        candidate_data
    )

    result = e._candidate_gate(
        candidate,
        e._extract_tonic_decision(
            decided_tonic()
        ),
    )

    assert result["status"] == "CLOSED"

    assert (
        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
        in result["blockers"]
    )


# ============================================================
# TEST 20
# ============================================================

def test_candidate_support_margin_required():

    e = MaqamDecisionGate()

    candidate_data = (
        ready_readiness()[
            "readiness"
        ]["candidates"][0].copy()
    )

    candidate_data[
        "support_margin"
    ] = 0.02

    candidate = e._extract_candidate(
        candidate_data
    )

    result = e._candidate_gate(
        candidate,
        e._extract_tonic_decision(
            decided_tonic()
        ),
    )

    assert result["status"] == "CLOSED"

    assert (
        "SUPPORT_MARGIN_TOO_SMALL"
        in result["blockers"]
    )


# ============================================================
# TEST 21
# ============================================================

def test_candidate_support_share_required():

    e = MaqamDecisionGate()

    candidate_data = (
        ready_readiness()[
            "readiness"
        ]["candidates"][0].copy()
    )

    candidate_data[
        "support_share"
    ] = 0.30

    candidate = e._extract_candidate(
        candidate_data
    )

    result = e._candidate_gate(
        candidate,
        e._extract_tonic_decision(
            decided_tonic()
        ),
    )

    assert result["status"] == "CLOSED"

    assert (
        "SUPPORT_SHARE_TOO_SMALL"
        in result["blockers"]
    )


# ============================================================
# TEST 22
# ============================================================

def test_protection():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
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


# ============================================================
# TEST 23
# ============================================================

def test_gate_never_overrides_closed_gate():

    e = MaqamDecisionGate()

    result = e.analyze(
        not_ready_readiness(),
        bad_reliability(),
        bad_consensus(),
        bad_conflict(),
        abstained_tonic(),
    )

    assert result["gate"]["status"] == "CLOSED"
    assert result["gate"]["decision_allowed"] is False
    assert result["gate"]["abstention_required"] is True

    assert (
        result["protection"][
            "original_decision_overridden"
        ]
        is False
    )


# ============================================================
# TEST 24
# ============================================================

def test_decision_safety():

    e = MaqamDecisionGate()

    result = e.analyze(
        not_ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    safety = result[
        "decision_safety"
    ]

    assert safety[
        "gate_open"
    ] is False

    assert safety[
        "gate_closed"
    ] is True

    assert safety[
        "decision_allowed"
    ] is False

    assert safety[
        "maqam_selected"
    ] is False


# ============================================================
# TEST 25
# ============================================================

def test_score_ranges():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert (
        0.0
        <= result["gate"]["passed_checks"]
        <= result["gate"]["total_checks"]
    )

    assert (
        0.0
        <= result["checks"]["readiness_score"]
        <= 1.0
        or isinstance(
            result["checks"]["readiness_score"],
            bool,
        )
    )


# ============================================================
# TEST 26
# ============================================================

def test_thresholds_present():

    e = MaqamDecisionGate()

    thresholds = [
        e.MIN_READINESS_SCORE,
        e.MIN_OVERALL_RELIABILITY,
        e.MIN_CONSENSUS_QUALITY,
        e.MIN_AGREEMENT_SCORE,
        e.MAX_CONFLICT_SCORE,
        e.MAX_CONFLICT_SEVERITY,
        e.MIN_SUPPORT_MARGIN,
        e.MIN_SUPPORT_SHARE,
    ]

    for value in thresholds:
        assert isinstance(
            value,
            (int, float),
        )


# ============================================================
# TEST 27
# ============================================================

def test_gate_has_no_selection_method():

    e = MaqamDecisionGate()

    public_methods = [
        name
        for name in dir(e)
        if not name.startswith("_")
    ]

    assert (
        "select_maqam"
        not in public_methods
    )

    assert (
        "select_jins"
        not in public_methods
    )

    assert (
        "select_tonic"
        not in public_methods
    )


# ============================================================
# TEST 28
# ============================================================

def test_gate_protection_on_open():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert (
        result["protection"][
            "gate_selected_maqam"
        ]
        is False
    )

    assert (
        result["protection"][
            "gate_selected_jins"
        ]
        is False
    )

    assert (
        result["protection"][
            "gate_selected_tonic"
        ]
        is False
    )

    assert (
        result["protection"][
            "gate_modified_source"
        ]
        is False
    )


# ============================================================
# TEST 29
# ============================================================

def test_abstained_tonic_is_hard_block():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        abstained_tonic(),
    )

    assert (
        result["tonic_dependency"][
            "decision_available"
        ]
        is False
    )

    assert (
        result["gate"]["status"]
        == "CLOSED"
    )

    assert (
        result["gate"][
            "decision_allowed"
        ]
        is False
    )


# ============================================================
# TEST 30
# ============================================================

def test_valid_open_gate_keeps_evidence_only():

    e = MaqamDecisionGate()

    result = e.analyze(
        ready_readiness(),
        good_reliability(),
        good_consensus(),
        good_conflict(),
        decided_tonic(),
    )

    assert (
        result["gate"]["status"]
        == "OPEN"
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


# ============================================================
# RUNNER
# ============================================================

def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Maqam Decision Gate V1.0"
    )

    print(
        "=" * 60
    )

    tests = [
        test_build,
        test_readiness_extraction,
        test_reliability_extraction,
        test_consensus_extraction,
        test_conflict_extraction,
        test_tonic_extraction,
        test_candidate_gate_ready,
        test_candidate_gate_not_ready,
        test_closed_readiness_closes_gate,
        test_low_reliability_closes_gate,
        test_low_consensus_closes_gate,
        test_high_conflict_closes_gate,
        test_abstained_tonic_closes_gate,
        test_open_gate_with_valid_evidence,
        test_open_gate_does_not_select_maqam,
        test_gate_never_selects_tonic,
        test_gate_never_selects_jins,
        test_candidate_tonic_mismatch_closes_candidate,
        test_candidate_with_opposition_closed,
        test_candidate_support_margin_required,
        test_candidate_support_share_required,
        test_protection,
        test_gate_never_overrides_closed_gate,
        test_decision_safety,
        test_score_ranges,
        test_thresholds_present,
        test_gate_has_no_selection_method,
        test_gate_protection_on_open,
        test_abstained_tonic_is_hard_block,
        test_valid_open_gate_keeps_evidence_only,
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

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":
    run()