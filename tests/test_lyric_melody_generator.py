from src.generation.lyric_melody_generator import (
    LyricMelodyGenerator
)


def test_build():

    generator = LyricMelodyGenerator()

    result = generator.generate(
        word="ترانيم",
        maqam="hijaz_husayni",
        ornament="COMPLEX",
        duration=0.32,
        notes=[
            "B",
            "E",
            "F",
            "G",
            "C",
            "F#"
        ]
    )

    assert len(result.structure) == 3


def run():

    print()

    print("PhoenixVoiceEngine")

    print("Lyric Melody Generator V1.0")

    print("=" * 60)

    print(
        "TEST 1: test_build - ",
        end=""
    )

    test_build()

    print("PASS")

    generator = LyricMelodyGenerator()

    result = generator.generate(

        word="ترانيم",

        maqam="hijaz_husayni",

        ornament="COMPLEX",

        duration=0.32,

        notes=[
            "B",
            "E",
            "F",
            "G",
            "C",
            "F#"
        ]

    )

    print()

    print("Generated Lyric")

    print("=" * 40)

    print(f"Word: {result.word}")

    print(f"Maqam: {result.maqam}")

    print(f"Duration: {result.duration}s")

    print()

    for item in result.structure:

        print(
            f"{item['syllable']} "
            f"-> "
            f"{item['notes']}"
        )

    print()

    print("STATUS: PASS")


if __name__ == "__main__":

    run()