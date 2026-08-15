import json
from pathlib import Path

from src.synthesis.phrase_generation_engine import (
    PhraseGenerationEngine,
)

BLUEPRINT = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\replacement_segments"
    r"\replacement_blueprint.json"
)


def run():

    engine = (
        PhraseGenerationEngine()
    )

    result = engine.build(
        BLUEPRINT
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Phrase Generation Engine V1.0"
    )

    print(
        "=" * 60
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=4,
        )
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()