"""
PhoenixVoiceEngine
Tonic Candidate Contract V1.0
"""

from src.maqam.tonic_candidate_contract import (
    TonicCandidateContract,
)


# ============================================================
# Fixtures
# ============================================================

def c_candidate():
    return {
        "tonic": "C",
        "tonic_pitch_class": 0,
        "readiness_score": 0.92,
        "candidate_support": 0.88,
        "support_share": 0.72,
        "support_margin": 0.30,
        "support_rank": 1,
        "supporting_components": [
            "stable_center",
            "intervallic_relationship",
            "functional",
        ],
        "strong_candidate_components": 2,
        "opposing_components": [],
        "meaningful_opposing_components": 0,
        "blockers": [],
        "status": "READY",
    }


def g_candidate():
    return {
        "tonic": "G",
        "tonic_pitch_class": 7,
        "readiness_score": 0.41,
        "candidate_support": 0.30,
        "support_share": 0.28,
        "support_margin": -0.30,
        "support_rank": 2,
        "supporting_components": [
            "cadential",
        ],
        "strong_candidate_components": 0,
        "opposing_components": [
            "stable_center",
        ],
        "meaningful_opposing_components": 1,
        "blockers": [
            "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT",
        ],
        "status": "NOT_READY",
    }


# ============================================================
# TEST 1
# ============================================================

def test_build():

    contract = TonicCandidateContract()

    assert contract.VERSION == "1.0.0"
    assert contract.FEATURE_VERSION == "1.0.0"
    assert contract.PATCH_VERSION == "1.0.0"


# ============================================================
# TEST 2
# ============================================================

def test_pitch_class_normalization():

    assert (
        TonicCandidateContract.normalize_pitch_class(0)
        == 0
    )

    assert (
        TonicCandidateContract.normalize_pitch_class(12)
        == 0
    )

    assert (
        TonicCandidateContract.normalize_pitch_class(7)
        == 7
    )

    assert (
        TonicCandidateContract.normalize_pitch_class(-1)
        == 11
    )


# ============================================================
# TEST 3
# ============================================================

def test_pitch_class_names():

    assert (
        TonicCandidateContract.pitch_class_name(0)
        == "C"
    )

    assert (
        TonicCandidateContract.pitch_class_name(7)
        == "G"
    )

    assert (
        TonicCandidateContract.pitch_class_name(12)
        == "C"
    )


# ============================================================
# TEST 4
# ============================================================

def test_tonic_normalization():

    assert (
        TonicCandidateContract.normalize_tonic("C")
        == "C"
    )

    assert (
        TonicCandidateContract.normalize_tonic("g")
        == "G"
    )

    assert (
        TonicCandidateContract.normalize_tonic("do")
        == "C"
    )

    assert (
        TonicCandidateContract.normalize_tonic("sol")
        == "G"
    )


# ============================================================
# TEST 5
# ============================================================

def test_build_c_candidate():

    result = TonicCandidateContract.build(
        c_candidate()
    )

    assert result["tonic"] == "C"
    assert result["tonic_pitch_class"] == 0
    assert result["readiness_score"] == 0.92
    assert result["candidate_support"] == 0.88
    assert result["support_share"] == 0.72
    assert result["support_rank"] == 1
    assert result["status"] == "READY"


# ============================================================
# TEST 6
# ============================================================

def test_build_g_candidate():

    result = TonicCandidateContract.build(
        g_candidate()
    )

    assert result["tonic"] == "G"
    assert result["tonic_pitch_class"] == 7
    assert result["readiness_score"] == 0.41
    assert result["support_rank"] == 2
    assert result["status"] == "NOT_READY"


# ============================================================
# TEST 7
# ============================================================

def test_tonic_generated_from_pitch_class():

    candidate = {
        "tonic_pitch_class": 0,
        "readiness_score": 0.90,
        "candidate_support": 0.80,
        "support_share": 0.70,
        "support_margin": 0.20,
        "support_rank": 1,
        "supporting_components": [
            "stable_center"
        ],
        "strong_candidate_components": 1,
        "opposing_components": [],
        "meaningful_opposing_components": 0,
        "blockers": [],
        "status": "READY",
    }

    result = TonicCandidateContract.build(
        candidate
    )

    assert result["tonic"] == "C"
    assert result["tonic_pitch_class"] == 0


# ============================================================
# TEST 8
# ============================================================

def test_required_fields_present():

    result = TonicCandidateContract.build(
        c_candidate()
    )

    for field in TonicCandidateContract.REQUIRED_FIELDS:
        assert field in result


# ============================================================
# TEST 9
# ============================================================

def test_validation_valid_candidate():

    result = TonicCandidateContract.build(
        c_candidate()
    )

    validation = TonicCandidateContract.validate(
        result
    )

    assert validation["valid"] is True
    assert validation["errors"] == []


# ============================================================
# TEST 10
# ============================================================

def test_validation_missing_field():

    candidate = c_candidate()

    del candidate["tonic"]

    validation = TonicCandidateContract.validate(
        candidate
    )

    assert validation["valid"] is False

    assert (
        "MISSING_FIELD:tonic"
        in validation["errors"]
    )

    assert (
        "TONIC_MISSING"
        in validation["errors"]
    )


# ============================================================
# TEST 11
# ============================================================

def test_score_ranges():

    result = TonicCandidateContract.build(
        c_candidate()
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
# TEST 12
# ============================================================

def test_decision_eligible_ready_candidate():

    result = TonicCandidateContract.build(
        c_candidate()
    )

    assert (
        TonicCandidateContract.is_decision_eligible(
            result
        )
        is True
    )


# ============================================================
# TEST 13
# ============================================================

def test_not_ready_candidate_not_eligible():

    result = TonicCandidateContract.build(
        g_candidate()
    )

    assert (
        TonicCandidateContract.is_decision_eligible(
            result
        )
        is False
    )


# ============================================================
# TEST 14
# ============================================================

def test_blocked_candidate_not_eligible():

    candidate = c_candidate()

    candidate["blockers"] = [
        "MEANINGFUL_OPPOSING_EVIDENCE_PRESENT"
    ]

    result = TonicCandidateContract.build(
        candidate
    )

    assert (
        TonicCandidateContract.is_decision_eligible(
            result
        )
        is False
    )


# ============================================================
# TEST 15
# ============================================================

def test_missing_pitch_class_warning():

    candidate = c_candidate()

    del candidate["tonic_pitch_class"]

    result = TonicCandidateContract.build(
        candidate
    )

    validation = TonicCandidateContract.validate(
        result
    )

    assert validation["valid"] is True

    assert (
        "TONIC_PITCH_CLASS_MISSING"
        in validation["warnings"]
    )


# ============================================================
# TEST 16
# ============================================================

def test_candidate_generation():

    candidates = [
        c_candidate(),
        g_candidate(),
    ]

    result = (
        TonicCandidateContract.build_candidates(
            candidates
        )
    )

    assert len(result) == 2

    assert result[0]["tonic"] == "C"
    assert result[0]["tonic_pitch_class"] == 0

    assert result[1]["tonic"] == "G"
    assert result[1]["tonic_pitch_class"] == 7


# ============================================================
# TEST 17
# ============================================================

def test_document_generation():

    candidates = [
        c_candidate(),
        g_candidate(),
    ]

    document = (
        TonicCandidateContract.build_document(
            candidates
        )
    )

    assert document["version"] == "1.0.0"

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
        == "Tonic Candidate Contract"
    )

    assert (
        document["contract"]["decision_making"]
        is False
    )

    assert (
        document["contract"]["source_modification"]
        is False
    )

    assert len(
        document["candidates"]
    ) == 2


# ============================================================
# TEST 18
# ============================================================

def test_contract_never_makes_tonic_decision():

    document = (
        TonicCandidateContract.build_document(
            [c_candidate()]
        )
    )

    assert (
        document["protection"][
            "tonic_decision_made"
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
# TEST 19
# ============================================================

def test_contract_never_selects_maqam_or_jins():

    document = (
        TonicCandidateContract.build_document(
            [c_candidate()]
        )
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

    assert (
        document["protection"][
            "maqam_decision_made"
        ]
        is False
    )

    assert (
        document["protection"][
            "jins_decision_made"
        ]
        is False
    )


# ============================================================
# TEST 20
# ============================================================

def test_protection():

    document = (
        TonicCandidateContract.build_document(
            [
                c_candidate(),
                g_candidate(),
            ]
        )
    )

    protection = document["protection"]

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


# ============================================================
# TEST 21
# ============================================================

def test_original_candidate_information_preserved():

    original = c_candidate()

    result = TonicCandidateContract.build(
        original
    )

    assert (
        result["tonic"]
        == original["tonic"]
    )

    assert (
        result["tonic_pitch_class"]
        == original["tonic_pitch_class"]
    )

    assert (
        result["readiness_score"]
        == original["readiness_score"]
    )

    assert (
        result["candidate_support"]
        == original["candidate_support"]
    )

    assert (
        result["support_share"]
        == original["support_share"]
    )


# ============================================================
# TEST 22
# ============================================================

def test_status_normalization():

    candidate = c_candidate()

    candidate["status"] = "ready"

    result = TonicCandidateContract.build(
        candidate
    )

    assert result["status"] == "READY"


# ============================================================
# TEST 23
# ============================================================

def test_c_and_g_are_distinct():

    c = TonicCandidateContract.build(
        c_candidate()
    )

    g = TonicCandidateContract.build(
        g_candidate()
    )

    assert (
        c["tonic_pitch_class"]
        != g["tonic_pitch_class"]
    )

    assert (
        c["tonic"]
        != g["tonic"]
    )


# ============================================================
# TEST 24
# ============================================================

def test_contract_has_no_decision_method():

    contract = TonicCandidateContract()

    assert not hasattr(
        contract,
        "decide"
    )

    assert not hasattr(
        contract,
        "select_tonic"
    )


# ============================================================
# RUNNER
# ============================================================

def run():

    print("PhoenixVoiceEngine")
    print(
        "Tonic Candidate Contract V1.0"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_pitch_class_normalization,
        test_pitch_class_names,
        test_tonic_normalization,
        test_build_c_candidate,
        test_build_g_candidate,
        test_tonic_generated_from_pitch_class,
        test_required_fields_present,
        test_validation_valid_candidate,
        test_validation_missing_field,
        test_score_ranges,
        test_decision_eligible_ready_candidate,
        test_not_ready_candidate_not_eligible,
        test_blocked_candidate_not_eligible,
        test_missing_pitch_class_warning,
        test_candidate_generation,
        test_document_generation,
        test_contract_never_makes_tonic_decision,
        test_contract_never_selects_maqam_or_jins,
        test_protection,
        test_original_candidate_information_preserved,
        test_status_normalization,
        test_c_and_g_are_distinct,
        test_contract_has_no_decision_method,
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