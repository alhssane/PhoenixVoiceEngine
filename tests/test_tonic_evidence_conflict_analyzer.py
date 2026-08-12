"""
PhoenixVoiceEngine
Tonic Evidence Conflict Analyzer V1.0 Tests
"""

from src.maqam.tonic_evidence_conflict_analyzer import (
    TonicEvidenceConflictAnalyzer,
)


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
    }


def test_build():
    e = TonicEvidenceConflictAnalyzer()

    assert e.VERSION == "1.0.0"
    assert e.FEATURE_VERSION == "1.0.0"
    assert e.PATCH_VERSION == "1.0.0"


def test_preference_extraction():
    e = TonicEvidenceConflictAnalyzer()

    result = e._extract_preferences(
        consensus_fixture(),
        reliability_fixture(),
    )

    assert result["functional"] == "G"
    assert result["cadential"] == "G"
    assert result["stable_center"] == "C"
    assert result["intervallic_relationship"] == "C"
    assert result["microtonal"] == "TIE"
    assert result["tonic_relative"] == "TIE"


def test_group_generation():
    e = TonicEvidenceConflictAnalyzer()

    preferences = e._extract_preferences(
        consensus_fixture(),
        reliability_fixture(),
    )

    groups = e._build_groups(
        preferences
    )

    assert groups["G"] == [
        "functional",
        "cadential",
    ]

    assert groups["C"] == [
        "stable_center",
        "intervallic_relationship",
    ]

    assert groups["TIE"] == [
        "microtonal",
        "tonic_relative",
    ]


def test_component_conflict_rows():
    e = TonicEvidenceConflictAnalyzer()

    preferences = e._extract_preferences(
        consensus_fixture(),
        reliability_fixture(),
    )

    reliability = e._extract_reliability(
        reliability_fixture()
    )

    rows = e._component_conflict_rows(
        preferences,
        reliability,
    )

    assert len(rows) == 6

    functional = next(
        x for x in rows
        if x["component"] == "functional"
    )

    assert functional[
        "evidence_group"
    ] == "G"

    stable = next(
        x for x in rows
        if x["component"] == "stable_center"
    )

    assert stable[
        "evidence_group"
    ] == "C"


def test_conflict_balance():
    e = TonicEvidenceConflictAnalyzer()

    preferences = e._extract_preferences(
        consensus_fixture(),
        reliability_fixture(),
    )

    reliability = e._extract_reliability(
        reliability_fixture()
    )

    rows = e._component_conflict_rows(
        preferences,
        reliability,
    )

    result = e._conflict_balance(
        rows
    )

    assert result["G"]["support"] >= 0.0
    assert result["C"]["support"] >= 0.0

    assert (
        0.0
        <= result["balance"]
        <= 1.0
    )

    assert result[
        "weighted_preference"
    ] in ("G", "C", "TIE")


def test_effective_weight():
    e = TonicEvidenceConflictAnalyzer()

    row = {
        "reliability": 0.8,
        "availability": 1.0,
        "strength": 0.8,
        "separation": 0.10,
    }

    result = e._effective_weight(
        row
    )

    assert 0.0 <= result <= 1.0
    assert result > 0.0


def test_no_separation_no_effective_conflict_weight():
    e = TonicEvidenceConflictAnalyzer()

    row = {
        "reliability": 0.9,
        "availability": 1.0,
        "strength": 0.9,
        "separation": 0.0,
    }

    result = e._effective_weight(
        row
    )

    assert result == 0.0


def test_conflict_severity():
    e = TonicEvidenceConflictAnalyzer()

    preferences = e._extract_preferences(
        consensus_fixture(),
        reliability_fixture(),
    )

    reliability = e._extract_reliability(
        reliability_fixture()
    )

    rows = e._component_conflict_rows(
        preferences,
        reliability,
    )

    balance = e._conflict_balance(
        rows
    )

    consensus = e._extract_consensus(
        consensus_fixture()
    )

    result = e._conflict_severity(
        balance,
        consensus,
        rows,
    )

    assert (
        0.0
        <= result["score"]
        <= 1.0
    )

    assert result["label"] in (
        "MINIMAL",
        "LOW",
        "MODERATE",
        "HIGH",
    )

    assert (
        result["meaningful_G_components"]
        >= 0
    )

    assert (
        result["meaningful_C_components"]
        >= 0
    )


def test_strongest_by_group():
    e = TonicEvidenceConflictAnalyzer()

    preferences = e._extract_preferences(
        consensus_fixture(),
        reliability_fixture(),
    )

    reliability = e._extract_reliability(
        reliability_fixture()
    )

    rows = e._component_conflict_rows(
        preferences,
        reliability,
    )

    result = e._strongest_by_group(
        rows
    )

    assert result["G"] is not None
    assert result["C"] is not None

    assert result["G"][
        "component"
    ] in (
        "functional",
        "cadential",
    )

    assert result["C"][
        "component"
    ] in (
        "stable_center",
        "intervallic_relationship",
    )


def test_decision_safety():
    e = TonicEvidenceConflictAnalyzer()

    result = e._decision_safety(
        severity={
            "score": 0.60
        },
        balance={
            "balance": 0.80
        },
        consensus={
            "support_margin": 0.08
        },
    )

    assert result[
        "tonic_decision_safe"
    ] is False

    assert result[
        "conflict_requires_abstention"
    ] is True

    assert result["level"] == "UNSAFE"


def test_full_analysis():
    e = TonicEvidenceConflictAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
    )

    assert (
        result["version"]
        == "1.0.0"
    )

    assert (
        "conflict"
        in result
    )

    assert (
        "balance"
        in result["conflict"]
    )

    assert (
        "severity"
        in result["conflict"]
    )

    assert (
        "strongest_by_group"
        in result["conflict"]
    )

    assert (
        "decision_safety"
        in result
    )


def test_conflict_remains_visible():
    e = TonicEvidenceConflictAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
    )

    groups = result[
        "evidence_groups"
    ]

    assert groups["G"] == [
        "functional",
        "cadential",
    ]

    assert groups["C"] == [
        "stable_center",
        "intervallic_relationship",
    ]

    assert result[
        "protection"
    ]["evidence_conflict_hidden"] is False


def test_evidence_only():
    e = TonicEvidenceConflictAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
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


def test_protection():
    e = TonicEvidenceConflictAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
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


def test_conflicting_evidence_detected():
    e = TonicEvidenceConflictAnalyzer()

    result = e.analyze(
        consensus_data=consensus_fixture(),
        reliability_data=reliability_fixture(),
    )

    severity = result[
        "conflict"
    ]["severity"]

    assert (
        severity["meaningful_G_components"]
        >= 1
    )

    assert (
        severity["meaningful_C_components"]
        >= 1
    )

    assert (
        severity["score"]
        > 0.0
    )


def run():
    print("PhoenixVoiceEngine")
    print(
        "Tonic Evidence Conflict Analyzer V1.0"
    )
    print("=" * 60)

    tests = [
        test_build,
        test_preference_extraction,
        test_group_generation,
        test_component_conflict_rows,
        test_conflict_balance,
        test_effective_weight,
        test_no_separation_no_effective_conflict_weight,
        test_conflict_severity,
        test_strongest_by_group,
        test_decision_safety,
        test_full_analysis,
        test_conflict_remains_visible,
        test_evidence_only,
        test_protection,
        test_conflicting_evidence_detected,
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