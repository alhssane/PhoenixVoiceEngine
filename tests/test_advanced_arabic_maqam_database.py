from src.maqam.advanced_arabic_maqam_database import (
    AdvancedArabicMaqamDatabase,
)


def test_build():

    database = (
        AdvancedArabicMaqamDatabase()
    )

    assert (
        database.VERSION
        == "2.0.0"
    )


def test_count():

    database = (
        AdvancedArabicMaqamDatabase()
    )

    maqamat = (
        database.get_maqamat()
    )

    print()

    print(
        "Arabic Maqam Database"
    )

    print(
        "=" * 40
    )

    for maqam in maqamat:

        print(maqam)

    assert (
        len(maqamat)
        >= 10
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Advanced Arabic Maqam Database V2.0"
    )

    print("=" * 60)

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_count()

    print(
        "TEST 2: test_count - PASS"
    )

    print("=" * 60)

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()