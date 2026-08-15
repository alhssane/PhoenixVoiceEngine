from src.synthesis.real_singing_synthesis_engine import (
    RealSingingSynthesisEngine,
)


def run():

    print()

    print("PhoenixVoiceEngine")
    print("Real Singing Synthesis Engine V1.0")

    print("=" * 60)

    engine = (
        RealSingingSynthesisEngine()
    )

    result = engine.synthesize(

        original_word="فريدة",

        replacement_word="ترانيم",

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
            "F#",
        ],

        syllables=3,
    )

    print()

    print("Replacement")
    print("=" * 40)

    print(
        f"{result.original_word}"
        f" -> "
        f"{result.replacement_word}"
    )

    print(
        f"Maqam: {result.maqam}"
    )

    print(
        f"Duration: {result.duration}s"
    )

    print(
        f"Notes: {result.notes}"
    )

    print()

    print("STATUS:", result.status)


if __name__ == "__main__":

    run()