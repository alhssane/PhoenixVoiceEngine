from src.trainer.full_vocal_segment_engine import (
    FullVocalSegmentEngine,
)


def run():

    result = (
        FullVocalSegmentEngine()
        .build(
            r"F:\مجلد جديد (3)\صولو فريد الجود كلمات بان نور.wav"
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Full Vocal Segment Database V2"
    )

    print(
        "=" * 60
    )

    print()

    print(
        result
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()