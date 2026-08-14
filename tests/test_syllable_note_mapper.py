from src.generation.syllable_note_mapper import (
    SyllableNoteMapper
)


def test_build():

    mapper = SyllableNoteMapper()

    results = mapper.map(

        "ترانيم",

        [
            "B",
            "E",
            "F",
            "G",
            "C",
            "F#"
        ]

    )

    assert len(results) == 3


def run():

    print()

    print("PhoenixVoiceEngine")

    print(
        "Syllable-to-Note Mapper V1.0"
    )

    print("=" * 60)

    print(
        "TEST 1: test_build - ",
        end=""
    )

    test_build()

    print("PASS")

    mapper = SyllableNoteMapper()

    results = mapper.map(

        "ترانيم",

        [
            "B",
            "E",
            "F",
            "G",
            "C",
            "F#"
        ]

    )

    print()

    print("Syllable Mapping")

    print("=" * 40)

    for item in results:

        print(

            f"{item.syllable}"
            f" -> "
            f"{item.notes}"

        )

    print()

    print("STATUS: PASS")


if __name__ == "__main__":

    run()