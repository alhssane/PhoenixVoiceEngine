from src.generation.melody_template_engine import (
    MelodyTemplateEngine
)


def test_build():

    engine = MelodyTemplateEngine()

    result = engine.build(
        source_word="فريدة",
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

    assert result.note_count == 6


def run():

    print()

    print("PhoenixVoiceEngine")
    print("Melody Template Engine V1.0")

    print("=" * 60)

    print(
        "TEST 1: test_build - ",
        end=""
    )

    test_build()

    print("PASS")

    engine = MelodyTemplateEngine()

    template = engine.build(
        source_word="فريدة",
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

    print("Melody Template")

    print("=" * 40)

    print(
        f"Word: {template.source_word}"
    )

    print(
        f"Maqam: {template.maqam}"
    )

    print(
        f"Ornament: {template.ornament}"
    )

    print(
        f"Duration: {template.duration}s"
    )

    print(
        f"Notes: {template.notes}"
    )

    print(
        f"Note count: {template.note_count}"
    )

    print()

    print("STATUS: PASS")


if __name__ == "__main__":
    run()