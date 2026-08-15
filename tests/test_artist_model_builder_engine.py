import json
from pathlib import Path

from src.trainer.artist_model_builder_engine import (
    ArtistModelBuilderEngine,
)

from src.trainer.artist_pronunciation_learning_engine import (
    ArtistPronunciationLearningEngine,
)

from src.trainer.artist_melody_learning_engine import (
    ArtistMelodyLearningEngine,
)

from src.trainer.artist_ornament_learning_engine import (
    ArtistOrnamentLearningEngine,
)


PROFILE_FILE = (
    r"D:\PhoenixVoiceEngine\workspace\artist_profiles\fareed_profile.json"
)

EMBEDDING_FILE = (
    r"D:\PhoenixVoiceEngine\workspace\artist_profiles\fareed_voice_embedding.json"
)

WORDS_FILE = (
    r"D:\PhoenixVoiceEngine\outputs\lyrics\fareed_words.json"
)

OUTPUT_FILE = (
    r"D:\PhoenixVoiceEngine\workspace\trained_artists\fareed_complete_model.json"
)


def run():

    pronunciation = (
        ArtistPronunciationLearningEngine()
        .analyze(
            WORDS_FILE
        )
    )

    melody = (
        ArtistMelodyLearningEngine()
        .analyze(
            PROFILE_FILE
        )
    )

    ornament = (
        ArtistOrnamentLearningEngine()
        .analyze(
            PROFILE_FILE
        )
    )

    model = (
        ArtistModelBuilderEngine()
        .analyze(
            PROFILE_FILE,
            EMBEDDING_FILE,
            pronunciation,
            melody,
            ornament,
        )
    )

    Path(
        OUTPUT_FILE
    ).write_text(
        json.dumps(
            model,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Artist Model Builder V1.0"
    )

    print(
        "=" * 60
    )

    print()

    print(
        f"Artist: {model['artist']}"
    )

    print(
        f"Maqam: {model['maqam']}"
    )

    print(
        f"Words: {model['word_count']}"
    )

    print(
        f"Syllables: {model['syllable_count']}"
    )

    print()

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()