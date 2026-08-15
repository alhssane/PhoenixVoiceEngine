from src.synthesis.phrase_generation_engine import (
    PhraseGenerationEngine,
)

from src.synthesis.phoneme_timeline_engine import (
    PhonemeTimelineEngine,
)


BLUEPRINT = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\replacement_segments"
    r"\replacement_blueprint.json"
)


def run():

    generator = (
        PhraseGenerationEngine()
    )

    generated = (
        generator.build(
            BLUEPRINT
        )
    )

    timeline = (
        PhonemeTimelineEngine()
        .analyze(
            generated
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Phoneme Timeline Engine V1.0"
    )

    print(
        "=" * 60
    )

    for item in timeline[
        "timeline"
    ]:

        print(
            f"{item['phoneme']} | "
            f"{item['start']}s -> "
            f"{item['end']}s | "
            f"{item['duration']}s"
        )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()