from src.lyrics.lyrics_replacement_blueprint import (
    LyricsReplacementBlueprint
)

from src.lyrics.word_replacement_engine import (
    WordReplacementEngine
)

from src.generation.lyric_melody_generator import (
    LyricMelodyGenerator
)

from src.lyrics.lyrics_timing_preservation_engine import (
    LyricsTimingPreservationEngine
)


def run():

    print()

    print("PhoenixVoiceEngine")
    print("End-to-End Lyrics Replacement Test V2.0")
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

        notes=[
            "B",
            "E",
            "F",
            "G",
            "C",
            "F#"
        ],

        syllables=3
    )

    replacement_engine = (
        WordReplacementEngine()
    )

    replacement = (
        replacement_engine.create_plan(
            blueprint,
            "ترانيم"
        )
    )

    melody_generator = (
        LyricMelodyGenerator()
    )

    generated = (
        melody_generator.generate(
            word=replacement.target_word,
            maqam=replacement.maqam,
            ornament=replacement.ornament,
            duration=replacement.duration,
            notes=replacement.notes
        )
    )

    timing_engine = (
        LyricsTimingPreservationEngine()
    )

    timeline = timing_engine.analyze(

        original_timeline=[
            timing_engine.build_word_timing(
                "فريدة",
                0.14,
                0.46
            )
        ],

        replacement_words=[
            "ترانيم"
        ]
    )

    print()

    print("Replacement")
    print("=" * 40)

    print(
        f"{replacement.source_word}"
        f" -> "
        f"{replacement.target_word}"
    )

    print()

    print("Generated Melody")
    print("=" * 40)

    for item in generated.structure:

        print(
            f"{item['syllable']} "
            f"-> "
            f"{item['notes']}"
        )

    print()

    print("Timing")
    print("=" * 40)

    for item in timeline["timeline"]:

        print(
            f"{item['replacement_word']} "
            f"| "
            f"{item['start_time']}s "
            f"-> "
            f"{item['end_time']}s"
        )

    print()

    print("STATUS: PASS")


if __name__ == "__main__":

    run()