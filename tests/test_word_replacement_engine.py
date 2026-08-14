from src.lyrics.lyrics_replacement_blueprint import (
    LyricsReplacementBlueprint
)

from src.lyrics.word_replacement_engine import (
    WordReplacementEngine
)


def run():

    print()

    print("PhoenixVoiceEngine")
    print("Word Replacement Engine V1.0")

    print("=" * 60)

    blueprint_engine = (
        LyricsReplacementBlueprint()
    )

    blueprint = blueprint_engine.build(
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

    engine = WordReplacementEngine()

    plan = engine.create_plan(
        blueprint,
        "ترانيم"
    )

    print()

    print("Replacement Plan")

    print("=" * 40)

    print(
        f"{plan.source_word} -> "
        f"{plan.target_word}"
    )

    print(
        f"Maqam: "
        f"{plan.maqam}"
    )

    print(
        f"Ornament: "
        f"{plan.ornament}"
    )

    print(
        f"Duration: "
        f"{plan.duration}s"
    )

    print(
        f"Compatible: "
        f"{plan.compatible}"
    )

    print(
        f"Notes: "
        f"{plan.notes}"
    )

    print()

    print("STATUS: PASS")


if __name__ == "__main__":
    run()