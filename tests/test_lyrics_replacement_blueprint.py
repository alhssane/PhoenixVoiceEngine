from src.lyrics.lyrics_replacement_blueprint import (
    LyricsReplacementBlueprint
)


def test_build():

    engine = LyricsReplacementBlueprint()

    result = engine.build(
        original_word="فريدة",
        start=0.14,
        end=0.46,
        maqam="hijaz_husayni",
        ornament="COMPLEX",
        average_pitch=550.18,
        quarter_tone=-14.63,
        notes=["B", "E", "F", "G", "C", "F#"],
        syllables=3
    )

    assert result.original_word == "فريدة"


def run():

    print()

    print("PhoenixVoiceEngine")
    print("Lyrics Replacement Blueprint Engine V1.0")
    print("=" * 60)

    print("TEST 1: test_build - ", end="")

    test_build()

    print("PASS")

    print()

    engine = LyricsReplacementBlueprint()

    result = engine.build(
        original_word="فريدة",
        start=0.14,
        end=0.46,
        maqam="hijaz_husayni",
        ornament="COMPLEX",
        average_pitch=550.18,
        quarter_tone=-14.63,
        notes=["B", "E", "F", "G", "C", "F#"],
        syllables=3
    )

    print("Blueprint")
    print("=" * 40)

    print(f"Word: {result.original_word}")
    print(f"Duration: {result.duration}s")
    print(f"Maqam: {result.maqam}")
    print(f"Ornament: {result.ornament}")
    print(f"Pitch: {result.average_pitch} Hz")
    print(f"Quarter Tone: {result.quarter_tone} cents")
    print(f"Syllables: {result.syllables}")
    print(f"Notes: {result.notes}")

    print()

    print("STATUS: PASS")


if __name__ == "__main__":
    run()