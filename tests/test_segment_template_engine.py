import json
from pathlib import Path

from src.synthesis.segment_template_engine import (
    SegmentTemplateEngine,
)


AUDIO = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\replacement_segments\saadah.wav"
)

BLUEPRINT = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\replacement_segments"
    r"\replacement_blueprint.json"
)


def run():

    result = (
        SegmentTemplateEngine()
        .build(
            AUDIO,
            BLUEPRINT,
        )
    )

    output = Path(
        r"D:\PhoenixVoiceEngine\workspace"
        r"\replacement_segments"
        r"\segment_template.json"
    )

    output.write_text(
        json.dumps(
            result,
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
        "Segment Template Engine V1.0"
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
        f"Saved: {output}"
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()