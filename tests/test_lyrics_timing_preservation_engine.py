from src.lyrics.lyrics_timing_preservation_engine import (
    LyricsTimingPreservationEngine,
)


def build_sample():

    engine = LyricsTimingPreservationEngine()

    return [
        engine.build_word_timing(
            "يا",
            0.0,
            0.5,
        ),
        engine.build_word_timing(
            "ليل",
            0.5,
            1.5,
        ),
    ]


def test_build():

    engine = LyricsTimingPreservationEngine()

    assert engine.VERSION == "1.0.0"


def test_word_timing():

    engine = LyricsTimingPreservationEngine()

    result = engine.build_word_timing(
        "عين",
        1.0,
        2.0,
    )

    assert result["duration"] == 1.0


def test_preserve_timing():

    engine = LyricsTimingPreservationEngine()

    result = engine.preserve_timing(
        build_sample(),
        [
            "يا",
            "قلبي",
        ],
    )

    assert len(result) == 2


def test_original_preserved():

    engine = LyricsTimingPreservationEngine()

    result = engine.preserve_timing(
        build_sample(),
        [
            "يا",
            "قلبي",
        ],
    )

    assert (
        result[1]["start_time"]
        == 0.5
    )


def test_replacement_inserted():

    engine = LyricsTimingPreservationEngine()

    result = engine.preserve_timing(
        build_sample(),
        [
            "يا",
            "روحي",
        ],
    )

    assert (
        result[1]["replacement_word"]
        == "روحي"
    )


def test_analysis():

    engine = LyricsTimingPreservationEngine()

    result = engine.analyze(
        build_sample(),
        [
            "يا",
            "قلبي",
        ],
    )

    assert result["status"] == "READY"


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith("test_")
    ]

    print("PhoenixVoiceEngine")
    print(
        "Lyrics Timing Preservation Engine V1.0"
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

    print("STATUS: PASS")


if __name__ == "__main__":

    run()