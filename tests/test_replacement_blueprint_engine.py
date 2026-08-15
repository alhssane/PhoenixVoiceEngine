import json
from pathlib import Path

from src.synthesis.replacement_blueprint_engine import (
    ReplacementBlueprintEngine,
)


PROFILE = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\artist_profiles\fareed_profile.json"
)


def run():

    blueprint = (
        ReplacementBlueprintEngine()
        .build(
            PROFILE,
            "سعادة",
            "فرح",
            5.76,
            6.72,
        )
    )

    output = Path(
        r"D:\PhoenixVoiceEngine\workspace"
        r"\replacement_segments"
        r"\replacement_blueprint.json"
    )

    output.write_text(
        json.dumps(
            blueprint,
            ensure_ascii=False,
            indent=4,
        ),
        encoding="utf-8",
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Replacement Blueprint V1.0"
    )

    print(
        "=" * 60
    )

    print(
        json.dumps(
            blueprint,
            ensure_ascii=False,
            indent=4,
        )
    )

    print()

    print(
        f"Saved: {output}"
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()