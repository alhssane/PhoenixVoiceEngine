"""
PhoenixVoiceEngine
Maqam Candidate Contract V1.0
"""

from src.maqam.maqam_candidate_contract import (
    MaqamCandidateContract,
)


# ============================================================
# Fixtures
# ============================================================

def rast_c_candidate():
    return {
        "maqam": "rast",
        "tonic_pitch_class": 0,
        "tonic_name": "C",
        "readiness_score": 0.92,
        "candidate_support": 0.88,
        "support_share": 0.72,
        "support_margin": 0.30,
        "support_rank": 1,
        "supporting_components": [
            "maqam_structure",
            "jins_compatibility",
            "intervallic_pattern",
        ],
        "strong_candidate_components": 2,
        "opposing_components": [],
        "meaningful_opposing_components": 0,
        "blockers": [],
        "status": "READY",
    }


def bayati_g_candidate():
    return {
        "maqam": "bayati",
        "tonic_pitch_class": 7,
        "tonic_name": "G",
        "readiness_score": 0.41,
        "candidate_support": 0.30,
        "support_share": 0.28,
        "support_margin": -0.30,
        "support_rank": 2,
        "supporting_components": [
            "maqam_structure",
        ],
        "strong_candidate_components": 0,
        "opposing_components": [
            "tonic_mismatch",
        ],
        "meaningful_opposing_components": 1,
        "blockers": [
            "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT",
        ],
        "status": "NOT_READY",
    }


def decided_c_tonic():
    return {
        "status": "DECIDED",
        "tonic_pitch_class": 0,
        "tonic_name": "C",
        "confidence": 0.91,
    }


def abstained_tonic():
    return {
        "status": "ABSTAIN",
        "tonic_pitch_class": None,
        "tonic_name": None,
        "confidence": None,
    }


# ============================================================
# TEST 1
# ============================================================

def test_build():

    contract = MaqamCandidateContract()

    assert contract.VERSION == "1.0.0"
    assert contract.FEATURE_VERSION == "1.0.0"
    assert contract.PATCH_VERSION == "1.0.0"


# ============================================================
# TEST 2
# ============================================================

def test_pitch_class_normalization():

    assert (
        MaqamCandidateContract.normalize_pitch_class(0)
        == 0
    )

    assert (
        MaqamCandidateContract.normalize_pitch_class(12)
        == 0
    )

    assert (
        MaqamCandidateContract.normalize_pitch_class(7)
        == 7
    )

    assert (
        MaqamCandidateContract.normalize_pitch_class(-1)
        == 11
    )


# ============================================================
# TEST 3
# ============================================================

def test_pitch_class_names():

    assert (
        MaqamCandidateContract.pitch_class_name(0)
        == "C"
    )

    assert (
        MaqamCandidateContract.pitch_class_name(7)
        == "G"
    )

    assert (
        MaqamCandidateContract.pitch_class_name(12)
        == "C"
    )


# ============================================================
# TEST 4
# ============================================================

def test_tonic_normalization():

    assert (
        MaqamCandidateContract.normalize_tonic("C")
        == "C"
    )

    assert (
        MaqamCandidateContract.normalize_tonic("g")
        == "G"
    )

    assert (
        MaqamCandidateContract.normalize_tonic("do")
        == "C"
    )

    assert (
        MaqamCandidateContract.normalize_tonic("sol")
        == "G"
    )


# ============================================================
# TEST 5
# ============================================================

def test_maqam_normalization():

    assert (
        MaqamCandidateContract.normalize_maqam(
            "rast"
        )
        == "Rast"
    )

    assert (
        MaqamCandidateContract.normalize_maqam(
            "Rast"
        )
        == "Rast"
    )

    assert (
        MaqamCandidateContract.normalize_maqam(
            "bayati"
        )
        == "Bayati"
    )

    assert (
        MaqamCandidateContract.normalize_maqam(
            "segah"
        )
        == "Sikah"
    )


# ============================================================
# TEST 6
# ============================================================

def test_status_normalization():

    assert (
        MaqamCandidateContract.normalize_status(
            "ready"
        )
        == "READY"
    )

    assert (
        MaqamCandidateContract.normalize_status(
            "open"
        )
        == "READY"
    )

    assert (
        MaqamCandidateContract.normalize_status(
            "not_ready"
        )
        == "NOT_READY"
    )

    assert (
        MaqamCandidateContract.normalize_status(
            "blocked"
        )
        == "BLOCKED"
    )


# ============================================================
# TEST 7
# ============================================================

def test_build_rast_candidate():

    result = (
        MaqamCandidateContract.build(
            rast_c_candidate()
        )
    )

    assert result["maqam"] == "Rast"
    assert result["tonic_pitch_class"] == 0
    assert result["tonic_name"] == "C"

    assert (
        result["readiness_score"]
        == 0.92
    )

    assert (
        result["candidate_support"]
        == 0.88
    )

    assert (
        result["support_share"]
        == 0.72
    )

    assert (
        result["support_rank"]
        == 1
    )

    assert result["status"] == "READY"


# ============================================================
# TEST 8
# ============================================================

def test_build_bayati_candidate():

    result = (
        MaqamCandidateContract.build(
            bayati_g_candidate()
        )
    )

    assert result["maqam"] == "Bayati"
    assert result["tonic_pitch_class"] == 7
    assert result["tonic_name"] == "G"

    assert (
        result["readiness_score"]
        == 0.41
    )

    assert (
        result["support_rank"]
        == 2
    )

    assert (
        result["status"]
        == "NOT_READY"
    )


# ============================================================
# TEST 9
# ============================================================

def test_tonic_generated_from_pitch_class():

    candidate = {
        "maqam": "rast",
        "tonic_pitch_class": 0,
        "readiness_score": 0.90,
        "candidate_support": 0.80,
        "support_share": 0.70,
        "support_margin": 0.20,
        "support_rank": 1,
        "supporting_components": [
            "maqam_structure",
        ],
        "strong_candidate_components": 1,
        "opposing_components": [],
        "meaningful_opposing_components": 0,
        "blockers": [],
        "status": "READY",
    }

    result = (
        MaqamCandidateContract.build(
            candidate
        )
    )

    assert result["maqam"] == "Rast"
    assert result["tonic_name"] == "C"
    assert result["tonic_pitch_class"] == 0


# ============================================================
# TEST 10
# ============================================================

def test_required_fields_present():

    result = (
        MaqamCandidateContract.build(
            rast_c_candidate()
        )
    )

    for field in (
        MaqamCandidateContract.REQUIRED_FIELDS
    ):
        assert field in result


# ============================================================
# TEST 11
# ============================================================

def test_validation_valid_candidate():

    result = (
        MaqamCandidateContract.build(
            rast_c_candidate()
        )
    )

    validation = (
        MaqamCandidateContract.validate(
            result
        )
    )

    assert validation["valid"] is True
    assert validation["errors"] == []


# ============================================================
# TEST 12
# ============================================================

def test_validation_missing_maqam():

    candidate = rast_c_candidate()

    del candidate["maqam"]

    validation = (
        MaqamCandidateContract.validate(
            candidate
        )
    )

    assert validation["valid"] is False

    assert (
        "MISSING_FIELD:maqam"
        in validation["errors"]
    )

    assert (
        "MAQAM_MISSING"
        in validation["errors"]
    )


# ============================================================
# TEST 13
# ============================================================

def test_validation_invalid_pitch_class():

    candidate = (
        rast_c_candidate()
    )

    candidate[
        "tonic_pitch_class"
    ] = "invalid"

    validation = (
        MaqamCandidateContract.validate(
            candidate
        )
    )

    assert validation["valid"] is False

    assert (
        "INVALID_TONIC_PITCH_CLASS"
        in validation["errors"]
    )


# ============================================================
# TEST 14
# ============================================================

def test_score_ranges():

    result = (
        MaqamCandidateContract.build(
            rast_c_candidate()
        )
    )

    assert (
        0.0
        <= result["readiness_score"]
        <= 1.0
    )

    assert (
        0.0
        <= result["support_share"]
        <= 1.0
    )

    assert (
        result["candidate_support"]
        >= 0.0
    )


# ============================================================
# TEST 15
# ============================================================

def test_decision_eligible_ready_candidate():

    result = (
        MaqamCandidateContract.build(
            rast_c_candidate()
        )
    )

    assert (
        MaqamCandidateContract.is_decision_eligible(
            result
        )
        is True
    )


# ============================================================
# TEST 16
# ============================================================

def test_not_ready_candidate_not_eligible():

    result = (
        MaqamCandidateContract.build(
            bayati_g_candidate()
        )
    )

    assert (
        MaqamCandidateContract.is_decision_eligible(
            result
        )
        is False
    )


# ============================================================
# TEST 17
# ============================================================

def test_blocked_candidate_not_eligible():

    candidate = (
        rast_c_candidate()
    )

    candidate["blockers"] = [
        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
    ]

    result = (
        MaqamCandidateContract.build(
            candidate
        )
    )

    assert (
        MaqamCandidateContract.is_decision_eligible(
            result
        )
        is False
    )


# ============================================================
# TEST 18
# ============================================================

def test_tonic_binding_success():

    result = (
        MaqamCandidateContract.bind_tonic(
            rast_c_candidate(),
            decided_c_tonic(),
        )
    )

    assert (
        result[
            "tonic_binding_status"
        ]
        == "BOUND"
    )

    assert (
        result[
            "bound_tonic_pitch_class"
        ]
        == 0
    )

    assert (
        result[
            "bound_tonic_name"
        ]
        == "C"
    )


# ============================================================
# TEST 19
# ============================================================

def test_tonic_binding_mismatch():

    result = (
        MaqamCandidateContract.bind_tonic(
            rast_c_candidate(),
            {
                "status": "DECIDED",
                "tonic_pitch_class": 7,
                "tonic_name": "G",
                "confidence": 0.90,
            },
        )
    )

    assert (
        result[
            "tonic_binding_status"
        ]
        == "BLOCKED"
    )

    assert (
        "TONIC_MISMATCH"
        in result[
            "tonic_binding_reason"
        ]
    )


# ============================================================
# TEST 20
# ============================================================

def test_abstained_tonic_cannot_bind():

    result = (
        MaqamCandidateContract.bind_tonic(
            rast_c_candidate(),
            abstained_tonic(),
        )
    )

    assert (
        result[
            "tonic_binding_status"
        ]
        == "BLOCKED"
    )

    assert (
        "TONIC_DECISION_NOT_DECIDED"
        in result[
            "tonic_binding_reason"
        ]
    )


# ============================================================
# TEST 21
# ============================================================

def test_abstained_tonic_candidate_not_eligible():

    candidate = (
        MaqamCandidateContract.build(
            rast_c_candidate()
        )
    )

    assert (
        MaqamCandidateContract.is_decision_eligible(
            candidate,
            abstained_tonic(),
        )
        is False
    )


# ============================================================
# TEST 22
# ============================================================

def test_decided_tonic_candidate_eligible():

    candidate = (
        MaqamCandidateContract.build(
            rast_c_candidate()
        )
    )

    assert (
        MaqamCandidateContract.is_decision_eligible(
            candidate,
            decided_c_tonic(),
        )
        is True
    )


# ============================================================
# TEST 23
# ============================================================

def test_candidate_generation():

    candidates = [
        rast_c_candidate(),
        bayati_g_candidate(),
    ]

    result = (
        MaqamCandidateContract.build_candidates(
            candidates
        )
    )

    assert len(result) == 2

    assert (
        result[0]["maqam"]
        == "Rast"
    )

    assert (
        result[0][
            "tonic_pitch_class"
        ]
        == 0
    )

    assert (
        result[1]["maqam"]
        == "Bayati"
    )

    assert (
        result[1][
            "tonic_pitch_class"
        ]
        == 7
    )


# ============================================================
# TEST 24
# ============================================================

def test_document_generation():

    candidates = [
        rast_c_candidate(),
        bayati_g_candidate(),
    ]

    document = (
        MaqamCandidateContract.build_document(
            candidates
        )
    )

    assert (
        document["version"]
        == "1.0.0"
    )

    assert (
        document["feature_version"]
        == "1.0.0"
    )

    assert (
        document["patch_version"]
        == "1.0.0"
    )

    assert (
        document["contract"]["name"]
        == "Maqam Candidate Contract"
    )

    assert (
        document["contract"][
            "decision_making"
        ]
        is False
    )

    assert (
        document["contract"][
            "maqam_selection"
        ]
        is False
    )

    assert (
        document["contract"][
            "jins_selection"
        ]
        is False
    )

    assert len(
        document["candidates"]
    ) == 2


# ============================================================
# TEST 25
# ============================================================

def test_contract_never_makes_maqam_decision():

    document = (
        MaqamCandidateContract.build_document(
            [rast_c_candidate()]
        )
    )

    assert (
        document["protection"][
            "maqam_decision_made"
        ]
        is False
    )

    assert (
        document["protection"][
            "contract_selected_maqam"
        ]
        is False
    )


# ============================================================
# TEST 26
# ============================================================

def test_contract_never_selects_jins():

    document = (
        MaqamCandidateContract.build_document(
            [rast_c_candidate()]
        )
    )

    assert (
        document["contract"][
            "jins_selection"
        ]
        is False
    )

    assert (
        document["protection"][
            "jins_decision_made"
        ]
        is False
    )

    assert (
        document["protection"][
            "contract_selected_jins"
        ]
        is False
    )


# ============================================================
# TEST 27
# ============================================================

def test_contract_never_selects_tonic():

    document = (
        MaqamCandidateContract.build_document(
            [rast_c_candidate()]
        )
    )

    assert (
        document["contract"][
            "tonic_selection"
        ]
        is False
    )

    assert (
        document["protection"][
            "contract_selected_tonic"
        ]
        is False
    )


# ============================================================
# TEST 28
# ============================================================

def test_protection():

    document = (
        MaqamCandidateContract.build_document(
            [
                rast_c_candidate(),
                bayati_g_candidate(),
            ]
        )
    )

    protection = (
        document["protection"]
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
            "original_scores_preserved"
        ]
        is True
    )


# ============================================================
# TEST 29
# ============================================================

def test_original_candidate_information_preserved():

    original = (
        rast_c_candidate()
    )

    result = (
        MaqamCandidateContract.build(
            original
        )
    )

    assert (
        result["maqam"]
        == "Rast"
    )

    assert (
        result[
            "tonic_pitch_class"
        ]
        == original[
            "tonic_pitch_class"
        ]
    )

    assert (
        result[
            "readiness_score"
        ]
        == original[
            "readiness_score"
        ]
    )

    assert (
        result[
            "candidate_support"
        ]
        == original[
            "candidate_support"
        ]
    )

    assert (
        result[
            "support_share"
        ]
        == original[
            "support_share"
        ]
    )


# ============================================================
# TEST 30
# ============================================================

def test_candidate_contract_does_not_modify_tonic_decision():

    tonic = decided_c_tonic()

    original_status = tonic["status"]
    original_pitch = tonic[
        "tonic_pitch_class"
    ]

    result = (
        MaqamCandidateContract.bind_tonic(
            rast_c_candidate(),
            tonic,
        )
    )

    assert (
        tonic["status"]
        == original_status
    )

    assert (
        tonic[
            "tonic_pitch_class"
        ]
        == original_pitch
    )

    assert (
        result[
            "tonic_binding_status"
        ]
        == "BOUND"
    )


# ============================================================
# TEST 31
# ============================================================

def test_contract_has_no_decision_methods():

    contract = (
        MaqamCandidateContract()
    )

    assert not hasattr(
        contract,
        "decide",
    )

    assert not hasattr(
        contract,
        "select_maqam",
    )

    assert not hasattr(
        contract,
        "select_jins",
    )


# ============================================================
# TEST 32
# ============================================================

def test_abstention_protection():

    document = (
        MaqamCandidateContract.build_document(
            [rast_c_candidate()],
            tonic_decision=abstained_tonic(),
        )
    )

    assert (
        document["protection"][
            "tonic_abstention_overridden"
        ]
        is False
    )

    assert (
        document["protection"][
            "contract_selected_tonic"
        ]
        is False
    )

    assert (
        document["protection"][
            "maqam_decision_made"
        ]
        is False
    )


# ============================================================
# RUNNER
# ============================================================

def run():

    print("PhoenixVoiceEngine")
    print(
        "Maqam Candidate Contract V1.0"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_pitch_class_normalization,
        test_pitch_class_names,
        test_tonic_normalization,
        test_maqam_normalization,
        test_status_normalization,
        test_build_rast_candidate,
        test_build_bayati_candidate,
        test_tonic_generated_from_pitch_class,
        test_required_fields_present,
        test_validation_valid_candidate,
        test_validation_missing_maqam,
        test_validation_invalid_pitch_class,
        test_score_ranges,
        test_decision_eligible_ready_candidate,
        test_not_ready_candidate_not_eligible,
        test_blocked_candidate_not_eligible,
        test_tonic_binding_success,
        test_tonic_binding_mismatch,
        test_abstained_tonic_cannot_bind,
        test_abstained_tonic_candidate_not_eligible,
        test_decided_tonic_candidate_eligible,
        test_candidate_generation,
        test_document_generation,
        test_contract_never_makes_maqam_decision,
        test_contract_never_selects_jins,
        test_contract_never_selects_tonic,
        test_protection,
        test_original_candidate_information_preserved,
        test_candidate_contract_does_not_modify_tonic_decision,
        test_contract_has_no_decision_methods,
        test_abstention_protection,
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