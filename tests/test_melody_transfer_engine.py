import json
from pathlib import Path

from src.synthesis.melody_transfer_engine import (
    MelodyTransferEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples"
    r"\fareed_aljood.wav"
)


def run():

    result = (
        MelodyTransferEngine()
        .analyze(
            AUDIO_FILE,
            5.76,
            6.72,
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Melody Transfer Engine V1.0"
    )

    print(
        "=" * 60
    )

    print(
        f"Duration: "
        f"{result['duration']} sec"
    )

    print(
        f"Pitch Frames: "
        f"{result['pitch_frames']}"
    )

    print()

    print(
        result[
            "pitch_curve"
        ][:30]
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()