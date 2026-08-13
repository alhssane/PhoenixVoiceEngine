from src.lyrics.lyrics_replacement_engine import (
    LyricsReplacementEngine,
)


def test_build():

    engine = LyricsReplacementEngine()

    assert engine.VERSION == "1.0.0"


def test_tokenization():

    engine = LyricsReplacementEngine()

    tokens = engine.tokenize(
        "يا ليل يا عين"
    )

    assert len(tokens) == 4


def test_mapping_generation():

    engine = LyricsReplacementEngine()

    mapping = engine.build_mapping(
        "يا ليل يا عين",
        "يا قلبي يا روحي",
    )

    assert len(mapping) == 4


def test_original_word():

    engine = LyricsReplacementEngine()

    mapping = engine.build_mapping(
        "يا ليل",
        "يا قلبي",
    )

    assert (
        mapping[1]["original"]
        == "ليل"
    )


def test_replacement_word():

    engine = LyricsReplacementEngine()

    mapping = engine.build_mapping(
        "يا ليل",
        "يا قلبي",
    )

    assert (
        mapping[1]["replacement"]
        == "قلبي"
    )


def test_analysis():

    engine = LyricsReplacementEngine()

    result = engine.analyze(
        "يا ليل يا عين",
        "يا قلبي يا روحي",
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
        "Lyrics Replacement Engine V1.0"
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