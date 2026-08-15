from src.synthesis.lyric_to_phoneme_engine import (
    LyricToPhonemeEngine,
)

from src.synthesis.phoneme_duration_engine import (
    PhonemeDurationEngine,
)

from src.synthesis.melody_conditioning_engine import (
    MelodyConditioningEngine,
)


def run():

    phonemes = (
        LyricToPhonemeEngine()
        .analyze(
            "فرح"
        )
    )

    timeline = (
        PhonemeDurationEngine()
        .analyze(
            phonemes,
            0.96,
        )
    )

    melody = (
        MelodyConditioningEngine()
        .analyze(
            r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav",
            5.76,
            6.72,
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Real Phrase Generator V1.0"
    )

    print(
        "=" * 60
    )

    print()

    print(
        "Phonemes:"
    )

    print(
        phonemes
    )

    print()

    print(
        "Timeline:"
    )

    for item in timeline:

        print(item)

    print()

    print(
        f"Melody frames: {len(melody)}"
    )

    print()

    print(
        melody[:20]
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()