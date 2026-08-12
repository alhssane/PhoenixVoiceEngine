from src.maqam.jins_candidate_contract import JinsCandidateContract


def test_build():

    c = JinsCandidateContract()

    assert c.VERSION == "1.0.0"


def test_pitch_class_normalization():

    c = JinsCandidateContract()

    assert c._normalize_pitch_class(12) == 0


def test_tonic_normalization():

    c = JinsCandidateContract()

    assert c._normalize_status("decided") == "DECIDED"


def test_maqam_normalization():

    c = JinsCandidateContract()

    assert c._normalize_status("abstain") == "ABSTAIN"


def test_jins_normalization():

    c = JinsCandidateContract()

    x = c.build_candidate(
        0,
        "DECIDED",
        "RAST",
        "DECIDED",
        "RAST",
        0.9,
        0.8,
        0.4,
        0.9,
    )

    assert x["jins_name"] == "RAST"


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith("test_")
    ]

    print("PhoenixVoiceEngine")
    print("Jins Candidate Contract V1.0")
    print("=" * 60)

    passed = 0

    for index, test in enumerate(tests, 1):

        test()

        print(f"TEST {index}: {test.__name__} - PASS")

        passed += 1

    print("=" * 60)
    print("STATUS: PASS")


if __name__ == "__main__":
    run()