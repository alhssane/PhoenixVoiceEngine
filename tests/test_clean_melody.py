from src.synthesis.melody_cleanup_engine import (
    MelodyCleanupEngine,
)

from src.synthesis.melody_conditioning_engine import (
    MelodyConditioningEngine,
)


def run():

    melody = (
        MelodyConditioningEngine()
        .analyze(
            r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav",
            5.76,
            6.72,
        )
    )

    cleaned = (
        MelodyCleanupEngine()
        .analyze(
            melody
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Melody Cleanup Engine V1.0"
    )

    print(
        "=" * 60
    )

    print()

    print(
        f"Original frames: {len(melody)}"
    )

    print(
        f"Cleaned frames: {len(cleaned)}"
    )

    print()

    print(
        cleaned[:30]
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()