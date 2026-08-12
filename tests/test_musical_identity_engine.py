from src.maqam.musical_identity_engine import (
    MusicalIdentityEngine,
)


def tonic():

    return {
        "decision": {
            "status": "DECIDED",
            "tonic_name": "C",
            "confidence": 0.90,
        }
    }


def maqam():

    return {
        "decision": {
            "status": "DECIDED",
            "maqam": "RAST",
            "confidence": 0.88,
        }
    }


def jins():

    return {
        "decision": {
            "status": "DECIDED",
            "jins": "RAST",
            "confidence": 0.86,
        }
    }


def abstain():

    return {
        "decision": {
            "status": "ABSTAIN",
            "confidence": None,
        }
    }


def test_build():

    engine = MusicalIdentityEngine()

    assert engine.VERSION == "1.0.0"


def test_complete_identity():

    engine = MusicalIdentityEngine()

    result = engine.analyze(
        tonic(),
        maqam(),
        jins(),
    )

    assert (
        result["musical_identity"]["status"]
        == "DECIDED"
    )


def test_partial_identity():

    engine = MusicalIdentityEngine()

    result = engine.analyze(
        tonic(),
        maqam(),
        abstain(),
    )

    assert (
        result["musical_identity"]["status"]
        == "PARTIAL"
    )


def test_abstained_identity():

    engine = MusicalIdentityEngine()

    result = engine.analyze(
        abstain(),
        abstain(),
        abstain(),
    )

    assert (
        result["musical_identity"]["status"]
        == "ABSTAIN"
    )


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith("test_")
    ]

    print("PhoenixVoiceEngine")
    print("Musical Identity Engine V1.0")
    print("=" * 60)

    for index, test in enumerate(tests, 1):

        test()

        print(
            f"TEST {index}: "
            f"{test.__name__} - PASS"
        )

    print("=" * 60)

    print("STATUS: PASS")


if __name__ == "__main__":

    run()