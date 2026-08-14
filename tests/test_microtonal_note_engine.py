from src.maqam.microtonal_note_engine import (
    MicrotonalNoteEngine,
)


def test_build():

    engine = (
        MicrotonalNoteEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_note_count():

    engine = (
        MicrotonalNoteEngine()
    )

    assert (
        engine.note_count()
        == 24
    )


def test_microtones_exist():

    engine = (
        MicrotonalNoteEngine()
    )

    assert (
        engine.has_microtones()
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
        "Microtonal Note Engine V1.0"
    )

    print(
        "=" * 60
    )

    for index, test in enumerate(
        tests,
        1,
    ):

        test()

        print(
            f"TEST {index}: "
            f"{test.__name__} - PASS"
        )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()