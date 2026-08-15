from src.trainer.artist_style_learning_engine import (
    ArtistStyleLearningEngine,
)


PROFILE = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\artist_profiles\fareed_profile.json"
)

EMBEDDING = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\artist_profiles\fareed_voice_embedding.json"
)

OUTPUT = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\trained_artists\fareed_style.json"
)


def run():

    engine = (
        ArtistStyleLearningEngine()
    )

    style = engine.analyze(
        PROFILE,
        EMBEDDING,
    )

    engine.save(
        style,
        OUTPUT,
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Artist Style Learning Engine V1.0"
    )

    print(
        "=" * 60
    )

    for key, value in style.items():

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