"""
PhoenixVoiceEngine
Maqam Decision Engine V1.0
Test Suite
"""

from src.maqam.maqam_decision_engine import (
    MaqamDecisionEngine,
)


# ============================================================
# Test Fixtures
# ============================================================

def gate_open():
    return {
        "gate": {
            "status": "OPEN",
            "level": "ALLOW",
            "decision_allowed": True,
            "abstention_required": False,
            "blockers": [],
        }
    }


def gate_closed():
    return {
        "gate": {
            "status": "CLOSED",
            "level": "ABSTAIN",
            "decision_allowed": False,
            "abstention_required": True,
            "blockers": [
                "READINESS_STATUS_NOT_READY",
            ],
        }
    }


def readiness_ready():
    return {
        "readiness": {
            "global": {
                "status": "READY",
                "readiness_score": 0.90,
                "top_candidate": "Rast",
                "top_readiness": 0.90,
                "second_candidate": "Bayati",
                "second_readiness": 0.30,
                "global_blockers": [],
            },
            "candidates": [
                {
                    "maqam": "Rast",
                    "tonic_pitch_class": 0,
                    "tonic_name": "C",
                    "readiness_score": 0.90,
                    "candidate_support": 0.90,
                    "support_share": 0.80,
                    "support_margin": 0.60,
                    "status": "READY",
                    "blockers": [],
                    "supporting_components": [
                        "maqam_structure",
                        "jins_compatibility",
                    ],
                    "opposing_components": [],
                    "meaningful_opposing_components": 0,
                },
                {
                    "maqam": "Bayati",
                    "tonic_pitch_class": 0,
                    "tonic_name": "C",
                    "readiness_score": 0.30,
                    "candidate_support": 0.30,
                    "support_share": 0.20,
                    "support_margin": 0.00,
                    "status": "NOT_READY",
                    "blockers": [
                        "READINESS_SCORE_TOO_LOW",
                    ],
                    "supporting_components": [],
                    "opposing_components": [],
                    "meaningful_opposing_components": 1,
                },
            ],
        }
    }


def readiness_not_ready():
    return {
        "readiness": {
            "global": {
                "status": "NOT_READY",
                "readiness_score": 0.30,
                "top_candidate": "Rast",
                "top_readiness": 0.30,
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
                    "tonic_name": "C",
                    "readiness_score": 0.30,
                    "candidate_support": 0.30,
                    "support_share": 0.30,
                    "support_margin": 0.02,
                    "status": "NOT_READY",
                    "blockers": [
                        "OVERALL_RELIABILITY_BELOW_THRESHOLD",
                    ],
                    "supporting_components": [],
                    "opposing_components": [],
                    "meaningful_opposing_components": 1,
                }
            ],
        }
    }


def tonic_decided_c():
    return {
        "decision": {
            "status": "DECIDED",
            "tonic_pitch_class": 0,
            "tonic_name": "C",
        }
    }


def tonic_decided_g():
    return {
        "decision": {
            "status": "DECIDED",
            "tonic_pitch_class": 7,
            "tonic_name": "G",
        }
    }


def tonic_abstained():
    return {
        "decision": {
            "status": "ABSTAIN",
            "tonic_pitch_class": None,
            "tonic_name": None,
        }
    }


def candidate_rast():
    return {
        "maqam": "Rast",
        "tonic_pitch_class": 0,
        "tonic_name": "C",
        "readiness_score": 0.90,
        "candidate_support": 0.90,
        "support_share": 0.80,
        "support_margin": 0.60,
        "status": "READY",
        "blockers": [],
        "supporting_components": [
            "maqam_structure",
            "jins_compatibility",
        ],
        "opposing_components": [],
        "meaningful_opposing_components": 0,
    }


# ============================================================
# TEST 1
# ============================================================

def test_build():

    e = MaqamDecisionEngine()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.0"


# ============================================================
# TEST 2
# ============================================================

def test_gate_extraction():

    e = MaqamDecisionEngine()

    result = e._extract_gate(
        gate_open()
    )

    assert result["status"] == "OPEN"
    assert result["level"] == "ALLOW"
    assert result["decision_allowed"] is True
    assert result["abstention_required"] is False
    assert result["blockers"] == []


# ============================================================
# TEST 3
# ============================================================

def test_closed_gate_extraction():

    e = MaqamDecisionEngine()

    result = e._extract_gate(
        gate_closed()
    )

    assert result["status"] == "CLOSED"
    assert result["decision_allowed"] is False
    assert result["abstention_required"] is True


# ============================================================
# TEST 4
# ============================================================

def test_readiness_extraction():

    e = MaqamDecisionEngine()

    result = e._extract_readiness(
        readiness_ready()
    )

    assert result["status"] == "READY"
    assert result["readiness_score"] == 0.90
    assert result["top_candidate"] == "Rast"
    assert result["top_readiness"] == 0.90
    assert len(result["candidates"]) == 2


# ============================================================
# TEST 5
# ============================================================

def test_tonic_extraction():

    e = MaqamDecisionEngine()

    result = e._extract_tonic(
        tonic_decided_c()
    )

    assert result["status"] == "DECIDED"
    assert result["tonic_pitch_class"] == 0
    assert result["tonic_name"] == "C"


# ============================================================
# TEST 6
# ============================================================

def test_candidate_extraction():

    e = MaqamDecisionEngine()

    result = e._extract_candidate(
        candidate_rast()
    )

    assert result["maqam"] == "Rast"
    assert result["tonic_pitch_class"] == 0
    assert result["readiness_score"] == 0.90
    assert result["support_share"] == 0.80
    assert result["status"] == "READY"


# ============================================================
# TEST 7
# ============================================================

def test_candidate_filtering_valid():

    e = MaqamDecisionEngine()

    candidate = e._extract_candidate(
        candidate_rast()
    )

    tonic = e._extract_tonic(
        tonic_decided_c()
    )

    result = e._filter_candidate(
        candidate,
        tonic,
    )

    assert result["allowed"] is True
    assert result["blockers"] == []


# ============================================================
# TEST 8
# ============================================================

def test_closed_gate_abstains():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_closed(),
        readiness_ready(),
        tonic_decided_c(),
    )

    assert result["decision"]["status"] == "ABSTAIN"
    assert result["decision"]["maqam"] is None

    assert (
        "GATE_CLOSED"
        in result["decision"]["reason"]
    )

    assert (
        "MAQAM_DECISION_FORBIDDEN"
        in result["decision"]["reason"]
    )


# ============================================================
# TEST 9
# ============================================================

def test_closed_gate_never_overridden():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_closed(),
        readiness_ready(),
        tonic_decided_c(),
    )

    assert (
        result["gate"]["decision_allowed"]
        is False
    )

    assert (
        result["protection"]["gate_bypassed"]
        is False
    )

    assert (
        result["protection"]["closed_gate_overridden"]
        is False
    )


# ============================================================
# TEST 10
# ============================================================

def test_not_ready_abstains():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_not_ready(),
        tonic_decided_c(),
    )

    assert result["decision"]["status"] == "ABSTAIN"
    assert result["decision"]["maqam"] is None

    assert (
        "READINESS_NOT_READY"
        in result["decision"]["reason"]
    )


# ============================================================
# TEST 11
# ============================================================

def test_abstained_tonic_abstains():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_abstained(),
    )

    assert result["decision"]["status"] == "ABSTAIN"
    assert result["decision"]["maqam"] is None

    assert (
        result["decision_safety"]["safe"]
        is False
    )


# ============================================================
# TEST 12
# ============================================================

def test_candidate_tonic_mismatch_rejected():

    e = MaqamDecisionEngine()

    candidate = e._extract_candidate(
        candidate_rast()
    )

    tonic = e._extract_tonic(
        tonic_decided_g()
    )

    result = e._filter_candidate(
        candidate,
        tonic,
    )

    assert result["allowed"] is False

    assert (
        "TONIC_MISMATCH"
        in result["blockers"]
    )


# ============================================================
# TEST 13
# ============================================================

def test_candidate_blocker_rejected():

    e = MaqamDecisionEngine()

    raw = candidate_rast()

    raw["blockers"] = [
        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
    ]

    candidate = e._extract_candidate(
        raw
    )

    tonic = e._extract_tonic(
        tonic_decided_c()
    )

    result = e._filter_candidate(
        candidate,
        tonic,
    )

    assert result["allowed"] is False

    assert (
        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
        in result["blockers"]
    )


# ============================================================
# TEST 14
# ============================================================

def test_candidate_not_ready_rejected():

    e = MaqamDecisionEngine()

    raw = candidate_rast()

    raw["status"] = "NOT_READY"

    candidate = e._extract_candidate(
        raw
    )

    tonic = e._extract_tonic(
        tonic_decided_c()
    )

    result = e._filter_candidate(
        candidate,
        tonic,
    )

    assert result["allowed"] is False

    assert (
        "READINESS_NOT_READY"
        in result["blockers"]
    )


# ============================================================
# TEST 15
# ============================================================

def test_low_readiness_rejected():

    e = MaqamDecisionEngine()

    raw = candidate_rast()

    raw["readiness_score"] = 0.40

    candidate = e._extract_candidate(
        raw
    )

    tonic = e._extract_tonic(
        tonic_decided_c()
    )

    result = e._filter_candidate(
        candidate,
        tonic,
    )

    assert result["allowed"] is False

    assert (
        "READINESS_SCORE_TOO_LOW"
        in result["blockers"]
    )


# ============================================================
# TEST 16
# ============================================================

def test_low_support_share_rejected():

    e = MaqamDecisionEngine()

    raw = candidate_rast()

    raw["support_share"] = 0.30

    candidate = e._extract_candidate(
        raw
    )

    tonic = e._extract_tonic(
        tonic_decided_c()
    )

    result = e._filter_candidate(
        candidate,
        tonic,
    )

    assert result["allowed"] is False

    assert (
        "SUPPORT_SHARE_TOO_SMALL"
        in result["blockers"]
    )


# ============================================================
# TEST 17
# ============================================================

def test_low_support_margin_rejected():

    e = MaqamDecisionEngine()

    raw = candidate_rast()

    raw["support_margin"] = 0.02

    candidate = e._extract_candidate(
        raw
    )

    tonic = e._extract_tonic(
        tonic_decided_c()
    )

    result = e._filter_candidate(
        candidate,
        tonic,
    )

    assert result["allowed"] is False

    assert (
        "SUPPORT_MARGIN_TOO_SMALL"
        in result["blockers"]
    )


# ============================================================
# TEST 18
# ============================================================

def test_candidate_ranking():

    e = MaqamDecisionEngine()

    candidate_a = e._extract_candidate(
        candidate_rast()
    )

    candidate_b_raw = candidate_rast()

    candidate_b_raw["maqam"] = "Bayati"
    candidate_b_raw["readiness_score"] = 0.50
    candidate_b_raw["candidate_support"] = 0.50

    candidate_b = e._extract_candidate(
        candidate_b_raw
    )

    ranked = e._rank_candidates(
        [
            candidate_b,
            candidate_a,
        ]
    )

    assert ranked[0]["maqam"] == "Rast"
    assert ranked[1]["maqam"] == "Bayati"


# ============================================================
# TEST 19
# ============================================================

def test_open_gate_selects_valid_maqam():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_decided_c(),
    )

    assert result["decision"]["status"] == "DECIDED"
    assert result["decision"]["maqam"] == "Rast"
    assert result["decision"]["tonic_pitch_class"] == 0
    assert result["decision"]["tonic_name"] == "C"


# ============================================================
# TEST 20
# ============================================================

def test_open_gate_requires_valid_candidate():

    e = MaqamDecisionEngine()

    data = readiness_ready()

    data["readiness"]["candidates"][0][
        "status"
    ] = "NOT_READY"

    data["readiness"]["candidates"][0][
        "blockers"
    ] = [
        "READINESS_NOT_READY"
    ]

    result = e.analyze(
        gate_open(),
        data,
        tonic_decided_c(),
    )

    assert result["decision"]["status"] == "ABSTAIN"
    assert result["decision"]["maqam"] is None

    assert (
        "NO_VALID_MAQAM_CANDIDATE"
        in result["decision"]["reason"]
    )


# ============================================================
# TEST 21
# ============================================================

def test_weak_margin_abstains():

    e = MaqamDecisionEngine()

    data = readiness_ready()

    first = data[
        "readiness"
    ]["candidates"][0]

    second = {
        "maqam": "Bayati",
        "tonic_pitch_class": 0,
        "tonic_name": "C",
        "readiness_score": 0.85,
        "candidate_support": 0.80,
        "support_share": 0.70,
        "support_margin": 0.20,
        "status": "READY",
        "blockers": [],
        "supporting_components": [
            "maqam_structure"
        ],
        "opposing_components": [],
        "meaningful_opposing_components": 0,
    }

    first[
        "readiness_score"
    ] = 0.90

    first[
        "support_margin"
    ] = 0.20

    data[
        "readiness"
    ]["candidates"] = [
        first,
        second,
    ]

    result = e.analyze(
        gate_open(),
        data,
        tonic_decided_c(),
    )

    assert result["decision"]["status"] == "ABSTAIN"

    assert (
        "DECISION_MARGIN_TOO_SMALL"
        in result["decision"]["reason"]
    )


# ============================================================
# TEST 22
# ============================================================

def test_decision_never_selects_jins():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_decided_c(),
    )

    assert result["decision"]["jins"] is None

    assert (
        result["protection"]["jins_decision_made"]
        is False
    )


# ============================================================
# TEST 23
# ============================================================

def test_decision_never_changes_tonic():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_decided_c(),
    )

    assert (
        result["protection"]["tonic_decision_made"]
        is False
    )

    assert (
        result["decision"]["tonic_pitch_class"]
        == 0
    )


# ============================================================
# TEST 24
# ============================================================

def test_protection():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_decided_c(),
    )

    protection = result[
        "protection"
    ]

    assert (
        protection["source_pitch_modified"]
        is False
    )

    assert (
        protection["source_timing_modified"]
        is False
    )

    assert (
        protection["source_performance_modified"]
        is False
    )

    assert (
        protection["source_scores_modified"]
        is False
    )

    assert (
        protection["source_audio_modified"]
        is False
    )

    assert (
        protection["original_scores_preserved"]
        is True
    )


# ============================================================
# TEST 25
# ============================================================

def test_gate_never_bypassed():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_closed(),
        readiness_ready(),
        tonic_decided_c(),
    )

    assert (
        result["protection"]["gate_bypassed"]
        is False
    )

    assert (
        result["protection"]["closed_gate_overridden"]
        is False
    )


# ============================================================
# TEST 26
# ============================================================

def test_no_valid_candidate_abstains():

    e = MaqamDecisionEngine()

    data = readiness_ready()

    for candidate in data[
        "readiness"
    ]["candidates"]:

        candidate[
            "status"
        ] = "NOT_READY"

        candidate[
            "blockers"
        ] = [
            "READINESS_NOT_READY"
        ]

    result = e.analyze(
        gate_open(),
        data,
        tonic_decided_c(),
    )

    assert result["decision"]["status"] == "ABSTAIN"
    assert result["decision"]["maqam"] is None

    assert (
        "NO_VALID_MAQAM_CANDIDATE"
        in result["decision"]["reason"]
    )


# ============================================================
# TEST 27
# ============================================================

def test_decision_safety_on_abstain():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_closed(),
        readiness_ready(),
        tonic_decided_c(),
    )

    assert (
        result["decision_safety"]["safe"]
        is False
    )

    assert (
        "GATE_CLOSED"
        in result["decision_safety"]["reasons"]
    )


# ============================================================
# TEST 28
# ============================================================

def test_score_ranges():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_decided_c(),
    )

    ranking = result[
        "ranking"
    ]

    assert (
        ranking[
            "valid_candidate_count"
        ]
        >= 0
    )

    assert (
        0.0
        <= ranking[
            "decision_margin"
        ]
        <= 1.0
    )

    assert (
        result["decision"]["confidence"]
        is None
        or
        0.0
        <= result["decision"]["confidence"]
        <= 1.0
    )


# ============================================================
# TEST 29
# ============================================================

def test_thresholds_present():

    e = MaqamDecisionEngine()

    thresholds = [
        e.MIN_READINESS_SCORE,
        e.MIN_SUPPORT_SHARE,
        e.MIN_SUPPORT_MARGIN,
        e.MIN_DECISION_MARGIN,
    ]

    for value in thresholds:

        assert isinstance(
            value,
            (int, float),
        )

        assert 0.0 <= value <= 1.0


# ============================================================
# TEST 30
# ============================================================

def test_engine_has_no_jins_selection_method():

    e = MaqamDecisionEngine()

    public_methods = [
        name
        for name in dir(e)
        if not name.startswith("_")
    ]

    assert (
        "select_jins"
        not in public_methods
    )

    assert (
        "decide_jins"
        not in public_methods
    )


# ============================================================
# TEST 31
# ============================================================

def test_engine_has_no_tonic_selection_method():

    e = MaqamDecisionEngine()

    public_methods = [
        name
        for name in dir(e)
        if not name.startswith("_")
    ]

    assert (
        "select_tonic"
        not in public_methods
    )

    assert (
        "decide_tonic"
        not in public_methods
    )


# ============================================================
# TEST 32
# ============================================================

def test_abstained_tonic_hard_block():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_abstained(),
    )

    assert (
        result["tonic_dependency"][
            "decision_available"
        ]
        is False
    )

    assert (
        result["decision"]["status"]
        == "ABSTAIN"
    )

    assert (
        result["decision"]["maqam"]
        is None
    )


# ============================================================
# TEST 33
# ============================================================

def test_decided_tonic_required_for_decision():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_decided_c(),
    )

    assert (
        result["tonic_dependency"][
            "decision_available"
        ]
        is True
    )

    assert (
        result["decision"]["status"]
        == "DECIDED"
    )


# ============================================================
# TEST 34
# ============================================================

def test_valid_candidate_preserves_information():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_decided_c(),
    )

    ranked = result[
        "ranking"
    ]["candidates"]

    assert len(ranked) >= 1

    top = ranked[0]

    assert top[
        "maqam"
    ] == "Rast"

    assert top[
        "tonic_pitch_class"
    ] == 0

    assert top[
        "readiness_score"
    ] == 0.90


# ============================================================
# TEST 35
# ============================================================

def test_decision_reason_present():

    e = MaqamDecisionEngine()

    result = e.analyze(
        gate_open(),
        readiness_ready(),
        tonic_decided_c(),
    )

    assert isinstance(
        result["decision"]["reason"],
        list,
    )

    assert (
        len(
            result["decision"]["reason"]
        )
        > 0
    )


# ============================================================
# TEST 36
# ============================================================

def test_bender_style_abstention():

    e = MaqamDecisionEngine()

    # Simulates the conservative Bender situation:
    # gate closed + readiness not ready + tonic abstained.

    result = e.analyze(
        gate_closed(),
        readiness_not_ready(),
        tonic_abstained(),
    )

    assert (
        result["decision"]["status"]
        == "ABSTAIN"
    )

    assert (
        result["decision"]["maqam"]
        is None
    )

    assert (
        result["decision"]["jins"]
        is None
    )

    assert (
        result["protection"][
            "gate_bypassed"
        ]
        is False
    )

    assert (
        result["protection"][
            "closed_gate_overridden"
        ]
        is False
    )


# ============================================================
# TEST RUNNER
# ============================================================

def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Maqam Decision Engine V1.0"
    )

    print(
        "=" * 60
    )

    tests = [
        test_build,
        test_gate_extraction,
        test_closed_gate_extraction,
        test_readiness_extraction,
        test_tonic_extraction,
        test_candidate_extraction,
        test_candidate_filtering_valid,
        test_closed_gate_abstains,
        test_closed_gate_never_overridden,
        test_not_ready_abstains,
        test_abstained_tonic_abstains,
        test_candidate_tonic_mismatch_rejected,
        test_candidate_blocker_rejected,
        test_candidate_not_ready_rejected,
        test_low_readiness_rejected,
        test_low_support_share_rejected,
        test_low_support_margin_rejected,
        test_candidate_ranking,
        test_open_gate_selects_valid_maqam,
        test_open_gate_requires_valid_candidate,
        test_weak_margin_abstains,
        test_decision_never_selects_jins,
        test_decision_never_changes_tonic,
        test_protection,
        test_gate_never_bypassed,
        test_no_valid_candidate_abstains,
        test_decision_safety_on_abstain,
        test_score_ranges,
        test_thresholds_present,
        test_engine_has_no_jins_selection_method,
        test_engine_has_no_tonic_selection_method,
        test_abstained_tonic_hard_block,
        test_decided_tonic_required_for_decision,
        test_valid_candidate_preserves_information,
        test_decision_reason_present,
        test_bender_style_abstention,
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