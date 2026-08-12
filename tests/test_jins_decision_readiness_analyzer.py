from src.maqam.jins_decision_readiness_analyzer import (
    JinsDecisionReadinessAnalyzer
)


def candidate():

    return {
        "tonic_pitch_class": 0,
        "tonic_status": "DECIDED",
        "maqam_name": "RAST",
        "maqam_status": "DECIDED",
        "jins_name": "RAST",
        "jins_support": 0.90,
        "support_share": 0.80,
        "support_margin": 0.40,
        "readiness_score": 0.90,
        "blockers": [],
    }


def test_build():

    e = JinsDecisionReadinessAnalyzer()

    assert e.VERSION == "1.0.0"


def test_candidate_extraction():

    e = JinsDecisionReadinessAnalyzer()

    r = e.analyze([candidate()])

    assert len(
        r["readiness"]["candidates"]
    ) == 1


def test_tonic_extraction():

    c = candidate()

    assert c["tonic_status"] == "DECIDED"


def test_maqam_extraction():

    c = candidate()

    assert c["maqam_status"] == "DECIDED"


def test_ready_candidate():

    e = JinsDecisionReadinessAnalyzer()

    r = e.analyze([candidate()])

    assert (
        r["readiness"]["candidates"][0]["status"]
        == "READY"
    )


def test_not_ready_candidate():

    e = JinsDecisionReadinessAnalyzer()

    c = candidate()

    c["readiness_score"] = 0.10

    r = e.analyze([c])

    assert (
        r["readiness"]["candidates"][0]["status"]
        == "NOT_READY"
    )


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith("test_")
    ]

    print("PhoenixVoiceEngine")
    print("Jins Decision Readiness Analyzer V1.0")
    print("=" * 60)

    for index, test in enumerate(
        tests,
        1
    ):

        test()

        print(
            f"TEST {index}: "
            f"{test.__name__} - PASS"
        )

    print("=" * 60)

    print("STATUS: PASS")


if __name__ == "__main__":

    run()