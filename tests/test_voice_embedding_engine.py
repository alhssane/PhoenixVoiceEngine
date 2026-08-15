from pathlib import Path

from src.trainer.voice_embedding_engine import (
    VoiceEmbeddingEngine,
)


AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)

OUTPUT = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\artist_profiles"
    r"\fareed_voice_embedding.json"
)


def run():

    engine = (
        VoiceEmbeddingEngine()
    )

    profile = engine.analyze(
        AUDIO_FILE
    )

    engine.save(
        profile,
        OUTPUT,
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Voice Embedding Engine V1.0"
    )

    print(
        "=" * 60
    )

    for key, value in profile.items():

        print(
            f"{key}: {value}"
        )

    print()

    print(
        f"Saved: {OUTPUT}"
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()