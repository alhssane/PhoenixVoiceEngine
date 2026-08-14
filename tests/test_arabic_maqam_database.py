from src.maqam.arabic_maqam_database import (
    ArabicMaqamDatabase,
)


def test_build():

    database = (
        ArabicMaqamDatabase()
    )

    assert (
        database.VERSION
        == "1.0.0"
    )


def test_count():

    database = (
        ArabicMaqamDatabase()
    )

    assert (
        database.count()
        >= 10
    )


def test_sikah():

    database = (
        ArabicMaqamDatabase()
    )

    details = (
        database.get_details(
            "sikah"
        )
    )

    assert (
        details[
            "microtones"
        ]
        is True
    )


def run():

    tests = [
        obj
        for name, obj
        in globals().items()
        if name.startswith(
            "test_"
        )
    ]

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Arabic Maqam Database V1.0"
    )

    print("=" * 60)

    for index, test in enumerate(
        tests,
        1,
    ):

        test()

        print(
            f"TEST {index}: "
            f"{test.__name__} - PASS"
        )

    print("=" * 60)

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()