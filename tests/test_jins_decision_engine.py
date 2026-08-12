from src.maqam.jins_decision_engine import (
    JinsDecisionEngine
)


def gate_open():

    return {
        "gate": {
            "status": "OPEN",
            "decision_allowed": True,
        }
    }


def gate_closed():

    return {
        "gate": {
            "status": "CLOSED",
            "decision_allowed": False,
        }
    }


def readiness():

    return {
        "readiness": {
            "candidates": [
                {
                    "jins_name": "RAST",
                    "status": "READY",
                    "readiness_score": 0.90,
                    "support_share": 0.80,
                    "support_margin": 0.40,
                    "blockers": [],
                }
            ]
        }
    }


def test_build():

    e = JinsDecisionEngine()

    assert e.VERSION == "1.0.0"


def test_closed_gate_abstains():

    e = JinsDecisionEngine()

    r = e.analyze(
        gate_closed(),
        readiness()
    )

    assert (
        r["decision"]["status"]
        == "ABSTAIN"
    )


def test_open_gate_selects_candidate():

    e = JinsDecisionEngine()

    r = e.analyze(
        gate_open(),
        readiness()
    )

    assert (
        r["decision"]["status"]
        == "DECIDED"
    )


def run():

    tests = [
        obj
        for name, obj
        in globals().items()
        if name.startswith("test_")
    ]

    print("PhoenixVoiceEngine")
    print("Jins Decision Engine V1.0")
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