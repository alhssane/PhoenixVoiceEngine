from src.lyrics.lyric_melody_binding_engine import (
    LyricMelodyBindingEngine,
)


def build_melody():

    engine = LyricMelodyBindingEngine()

    return [
        engine.build_note(
            "C4",
            0.0,
            0.5,
        ),
        engine.build_note(
            "D4",
            0.5,
            1.0,
        ),
    ]


def test_build():

    engine = LyricMelodyBindingEngine()

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_note_creation():

    engine = LyricMelodyBindingEngine()

    note = engine.build_note(
        "E4",
        1.0,
        2.0,
    )

    assert (
        note["duration"]
        == 1.0
    )


def test_binding():

    engine = LyricMelodyBindingEngine()

    result = engine.bind(
        [
            "يا",
            "قلبي",
        ],
        build_melody(),
    )

    assert len(result) == 2


def test_pitch_preserved():

    engine = LyricMelodyBindingEngine()

    result = engine.bind(
        [
            "يا",
            "روحي",
        ],
        build_melody(),
    )

    assert (
        result[1]["pitch"]
        == "D4"
    )


def test_analysis():

    engine = LyricMelodyBindingEngine()

    result = engine.analyze(
        [
            "يا",
            "روحي",
        ],
        build_melody(),
    )

    assert (
        result["status"]
        == "READY"
    )


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith(
            "test_"
        )
    ]

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Lyric Melody Binding Engine V1.0"
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