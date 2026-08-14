from src.lyrics.word_duration_mapper import (
    WordDurationMapper
)


def test_build():

    mapper = WordDurationMapper()

    result = mapper.map(
        source_word="فريدة",
        target_word="ترانيم",
        source_duration=0.32
    )

    assert result.target_duration > 0


def run():

    print()

    print("PhoenixVoiceEngine")
    print("Word Duration Mapper V1.0")

    print("=" * 60)

    print(
        "TEST 1: test_build - ",
        end=""
    )

    test_build()

    print("PASS")

    mapper = WordDurationMapper()

    result = mapper.map(
        source_word="فريدة",
        target_word="ترانيم",
        source_duration=0.32
    )

    print()

    print("Duration Mapping")

    print("=" * 40)

    print(
        f"Source word: "
        f"{result.source_word}"
    )

    print(
        f"Target word: "
        f"{result.target_word}"
    )

    print(
        f"Original duration: "
        f"{result.source_duration}s"
    )

    print(
        f"Estimated duration: "
        f"{result.target_duration}s"
    )

    print(
        f"Ratio: "
        f"{result.ratio}"
    )

    print(
        f"Compatible: "
        f"{result.compatible}"
    )

    print()

    print("STATUS: PASS")


if __name__ == "__main__":
    run()