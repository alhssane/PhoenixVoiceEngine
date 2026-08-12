"""
PhoenixVoiceEngine
Tonic Decision Engine V1.0
"""

from src.maqam.tonic_decision_engine import TonicDecisionEngine


def gate_closed_fixture():
    return {
        "gate": {
            "status": "CLOSED",
            "level": "ABSTAIN",
            "decision_allowed": False,
            "abstention_required": True,
            "passed_checks": 2,
            "total_checks": 7,
            "blockers": [
                "OVERALL_RELIABILITY_BELOW_THRESHOLD",
                "MEANINGFUL_G_C_CONFLICT",
            ],
        }
    }


def gate_open_fixture():
    return {
        "gate": {
            "status": "OPEN",
            "level": "ALLOW",
            "decision_allowed": True,
            "abstention_required": False,
            "passed_checks": 7,
            "total_checks": 7,
            "blockers": [],
        }
    }


def readiness_not_ready_fixture():
    return {
        "readiness": {
            "global": {
                "status": "NOT_READY",
                "readiness_score": 0.374311,
                "top_candidate": "C",
                "top_readiness": 0.374311,
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
                    "tonic_pitch_class": 0,
                    "status": "NOT_READY",
                    "readiness_score": 0.374311,
                    "candidate_support": 0.181994,
                    "supporting_components": [
                        "stable_center",
                        "intervallic_relationship",
                    ],
                    "opposing_components": [
                        "functional",
                        "cadential",
                    ],
                    "blockers": [
                        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT",
                    ],
                },
                {
                    "tonic": "G",
                    "tonic_pitch_class": 7,
                    "status": "NOT_READY",
                    "readiness_score": 0.30,
                    "candidate_support": 0.101172,
                    "supporting_components": [
                        "functional",
                        "cadential",
                    ],
                    "opposing_components": [
                        "stable_center",
                        "intervallic_relationship",
                    ],
                    "blockers": [
                        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT",
                    ],
                },
            ],
        }
    }


def readiness_ready_c_fixture():
    return {
        "readiness": {
            "global": {
                "status": "READY",
                "readiness_score": 0.92,
                "top_candidate": "C",
                "top_readiness": 0.92,
                "second_candidate": "G",
                "second_readiness": 0.45,
                "global_blockers": [],
            },
            "candidates": [
                {
                    "tonic": "C",
                    "tonic_pitch_class": 0,
                    "status": "READY",
                    "readiness_score": 0.92,
                    "candidate_support": 0.88,
                    "supporting_components": [
                        "stable_center",
                        "intervallic_relationship",
                        "functional",
                    ],
                    "opposing_components": [],
                    "blockers": [],
                },
                {
                    "tonic": "G",
                    "tonic_pitch_class": 7,
                    "status": "NOT_READY",
                    "readiness_score": 0.45,
                    "candidate_support": 0.30,
                    "supporting_components": [
                        "cadential",
                    ],
                    "opposing_components": [
                        "stable_center",
                    ],
                    "blockers": [
                        "LOW_READINESS",
                    ],
                },
            ],
        }
    }


def readiness_tie_fixture():
    return {
        "readiness": {
            "global": {
                "status": "READY",
                "readiness_score": 0.90,
                "top_candidate": "C",
                "top_readiness": 0.90,
                "second_candidate": "G",
                "second_readiness": 0.89,
                "global_blockers": [],
            },
            "candidates": [
                {
                    "tonic": "C",
                    "tonic_pitch_class": 0,
                    "status": "READY",
                    "readiness_score": 0.90,
                    "candidate_support": 0.80,
                    "supporting_components": [
                        "stable_center",
                    ],
                    "opposing_components": [],
                    "blockers": [],
                },
                {
                    "tonic": "G",
                    "tonic_pitch_class": 7,
                    "status": "READY",
                    "readiness_score": 0.89,
                    "candidate_support": 0.79,
                    "supporting_components": [
                        "cadential",
                    ],
                    "opposing_components": [],
                    "blockers": [],
                },
            ],
        }
    }


# ============================================================
# TEST 1
# ============================================================

def test_build():
    e = TonicDecisionEngine()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.0"


# ============================================================
# TEST 2
# ============================================================

def test_gate_extraction():
    e = TonicDecisionEngine()

    result = e._extract_gate(
        gate_closed_fixture()
    )

    assert result["status"] == "CLOSED"
    assert result["level"] == "ABSTAIN"
    assert result["decision_allowed"] is False
    assert result["abstention_required"] is True
    assert len(result["blockers"]) == 2


# ============================================================
# TEST 3
# ============================================================

def test_readiness_extraction():
    e = TonicDecisionEngine()

    result = e._extract_readiness(
        readiness_not_ready_fixture()
    )

    assert result["status"] == "NOT_READY"
    assert result["top_candidate"] == "C"
    assert result["second_candidate"] == "G"
    assert len(result["candidates"]) == 2


# ============================================================
# TEST 4
# ============================================================

def test_candidate_extraction():
    e = TonicDecisionEngine()

    readiness = e._extract_readiness(
        readiness_ready_c_fixture()
    )

    candidates = e._extract_candidates(
        readiness,
        candidates=[0, 7],
    )

    assert len(candidates) == 2
    assert candidates[0]["tonic"] == "C"
    assert candidates[1]["tonic"] == "G"


# ============================================================
# TEST 5
# ============================================================

def test_candidate_filtering():
    e = TonicDecisionEngine()

    readiness = e._extract_readiness(
        readiness_ready_c_fixture()
    )

    candidates = e._extract_candidates(
        readiness
    )

    ranked = e._rank_candidates(
        candidates
    )

    assert ranked[0]["tonic"] == "C"
    assert ranked[0]["readiness_score"] == 0.92


# ============================================================
# TEST 6
# ============================================================

def test_closed_gate_abstains():
    e = TonicDecisionEngine()

    result = e.analyze(
        gate_data=gate_closed_fixture(),
        readiness_data=readiness_not_ready_fixture(),
        candidates=[7, 0],
    )

    decision = result["decision"]

    assert decision["status"] == "ABSTAIN"
    assert decision["tonic_pitch_class"] is None
    assert decision["tonic_name"] is None
    assert decision["confidence"] is None

    assert "GATE_CLOSED" in decision["reason"]
    assert "TONIC_DECISION_FORBIDDEN" in decision["reason"]


# ============================================================
# TEST 7
# ============================================================

def test_closed_gate_never_overridden():
    e = TonicDecisionEngine()

    result = e.analyze(
        gate_data=gate_closed_fixture(),
        readiness_data=readiness_ready_c_fixture(),
        candidates=[0, 7],
    )

    decision = result["decision"]

    assert decision["status"] == "ABSTAIN"
    assert decision["tonic_name"] is None
    assert decision["tonic_pitch_class"] is None

    assert (
        result["protection"]["gate_bypassed"]
        is False
    )

    assert (
        result["protection"]["closed_gate_overridden"]
        is False
    )


# ============================================================
# TEST 8
# ============================================================

def test_open_gate_selects_c():
    e = TonicDecisionEngine()

    result = e.analyze(
        gate_data=gate_open_fixture(),
        readiness_data=readiness_ready_c_fixture(),
        candidates=[0, 7],
    )

    decision = result["decision"]

    assert decision["status"] == "DECIDED"
    assert decision["tonic_pitch_class"] == 0
    assert decision["tonic_name"] == "C"
    assert decision["confidence"] is not None


# ============================================================
# TEST 9
# ============================================================

def test_open_gate_requires_readiness():
    e = TonicDecisionEngine()

    result = e.analyze(
        gate_data=gate_open_fixture(),
        readiness_data=readiness_not_ready_fixture(),
        candidates=[7, 0],
    )

    decision = result["decision"]

    assert decision["status"] == "ABSTAIN"
    assert decision["tonic_name"] is None

    assert (
        "READINESS_NOT_READY"
        in decision["reason"]
    )


# ============================================================
# TEST 10
# ============================================================

def test_weak_margin_abstains():
    e = TonicDecisionEngine()

    result = e.analyze(
        gate_data=gate_open_fixture(),
        readiness_data=readiness_tie_fixture(),
        candidates=[0, 7],
    )

    decision = result["decision"]

    assert decision["status"] == "ABSTAIN"
    assert decision["tonic_name"] is None

    assert (
        "TONIC_MARGIN_TOO_SMALL"
        in decision["reason"]
    )


# ============================================================
# TEST 11
# ============================================================

def test_candidate_with_blocker_rejected():
    e = TonicDecisionEngine()

    candidate = {
        "tonic": "C",
        "tonic_pitch_class": 0,
        "readiness_score": 0.95,
        "candidate_support": 0.90,
        "status": "READY",
        "blockers": [
            "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
        ],
    }

    normalized = e._normalize_candidate(
        candidate
    )

    assert (
        e._candidate_is_valid(
            normalized
        )
        is False
    )


# ============================================================
# TEST 12
# ============================================================

def test_candidate_generation():
    e = TonicDecisionEngine()

    readiness = e._extract_readiness(
        readiness_ready_c_fixture()
    )

    candidates = e._extract_candidates(
        readiness,
        candidates=[0],
    )

    assert len(candidates) == 1
    assert candidates[0]["tonic"] == "C"
    assert candidates[0]["tonic_pitch_class"] == 0


# ============================================================
# TEST 13
# ============================================================

def test_decision_never_selects_maqam():
    e = TonicDecisionEngine()

    result = e.analyze(
        gate_data=gate_open_fixture(),
        readiness_data=readiness_ready_c_fixture(),
        candidates=[0, 7],
    )

    decision = result["decision"]

    assert "maqam" not in decision
    assert "jins" not in decision

    assert (
        result["protection"]["maqam_decision_made"]
        is False
    )

    assert (
        result["protection"]["jins_decision_made"]
        is False
    )


# ============================================================
# TEST 14
# ============================================================

def test_protection():
    e = TonicDecisionEngine()

    result = e.analyze(
        gate_data=gate_open_fixture(),
        readiness_data=readiness_ready_c_fixture(),
        candidates=[0, 7],
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
        protection["original_scores_preserved"]
        is True
    )

    assert (
        protection["original_decision_overridden"]
        is False
    )

    assert (
        protection["source_audio_modified"]
        is False
    )


# ============================================================
# TEST 15
# ============================================================

def test_score_ranges():
    e = TonicDecisionEngine()

    result = e.analyze(
        gate_data=gate_open_fixture(),
        readiness_data=readiness_ready_c_fixture(),
        candidates=[0, 7],
    )

    decision = result[
        "decision"
    ]

    assert (
        0.0
        <= decision["confidence"]
        <= 1.0
    )

    for candidate in result[
        "ranking"
    ]["candidates"]:

        assert (
            0.0
            <= candidate["readiness_score"]
            <= 1.0
        )


# ============================================================
# TEST 16
# ============================================================

def test_bender_must_abstain():
    e = TonicDecisionEngine()

    result = e.analyze(
        gate_data=gate_closed_fixture(),
        readiness_data=readiness_not_ready_fixture(),
        candidates=[7, 0],
    )

    assert (
        result["decision"]["status"]
        == "ABSTAIN"
    )

    assert (
        result["decision"]["tonic_name"]
        is None
    )

    assert (
        result["decision"]["tonic_pitch_class"]
        is None
    )

    assert (
        result["protection"]["closed_gate_overridden"]
        is False
    )


# ============================================================
# RUNNER
# ============================================================

def run():

    print("PhoenixVoiceEngine")
    print("Tonic Decision Engine V1.0")
    print("=" * 60)

    tests = [
        test_build,
        test_gate_extraction,
        test_readiness_extraction,
        test_candidate_extraction,
        test_candidate_filtering,
        test_closed_gate_abstains,
        test_closed_gate_never_overridden,
        test_open_gate_selects_c,
        test_open_gate_requires_readiness,
        test_weak_margin_abstains,
        test_candidate_with_blocker_rejected,
        test_candidate_generation,
        test_decision_never_selects_maqam,
        test_protection,
        test_score_ranges,
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