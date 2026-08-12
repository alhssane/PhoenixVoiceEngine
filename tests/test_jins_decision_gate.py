from src.maqam.jins_decision_gate import (
    JinsDecisionGate
)


def readiness():

    return {
        "readiness": {
            "status": "READY",
            "candidates": [
                {
                    "jins_name": "RAST",
                    "status": "READY",
                    "readiness_score": 0.90,
                    "support_share": 0.80,
                    "support_margin": 0.40,
                }
            ]
        }
    }


def test_build():

    e = JinsDecisionGate()

    assert e.VERSION == "1.0.0"


def test_open_gate():

    e = JinsDecisionGate()

    r = e.analyze(
        readiness()
    )

    assert (
        r["gate"]["status"]
        == "OPEN"
    )


def test_closed_gate():

    e = JinsDecisionGate()

    data = readiness()

    data["readiness"][
        "candidates"
    ][0]["readiness_score"] = 0.20

    r = e.analyze(data)

    assert (
        r["gate"]["status"]
        == "CLOSED"
    )


def run():

    tests = [
        obj
        for name, obj
        in globals().items()
        if name.startswith("test_")
    ]

    print("PhoenixVoiceEngine")
    print("Jins Decision Gate V1.0")
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