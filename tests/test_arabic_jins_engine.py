from src.maqam.arabic_jins_engine import (
    ArabicJinsEngine,
)


def test_build():

    engine = (
        ArabicJinsEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_count():

    engine = (
        ArabicJinsEngine()
    )

    ajnas = (
        engine.get_jins_names()
    )

    print()

    print(
        "Arabic Jins Database"
    )

    print(
        "=" * 40
    )

    for jins in ajnas:

        print(jins)

    assert (
        len(ajnas)
        >= 5
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Arabic Jins Engine V1.0"
    )

    print(
        "=" * 60
    )

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_count()

    print(
        "TEST 2: test_count - PASS"
    )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()