from src.synthesis.artist_phoneme_bank import (
    ArtistPhonemeBank,
)


def run():

    print()

    print("PhoenixVoiceEngine")

    print(
        "Artist Phoneme Bank Engine V1.0"
    )

    print("=" * 60)

    engine = ArtistPhonemeBank()

    bank = engine.build_bank(
        "samples/fareed_aljood.wav"
    )

    print()

    print("Detected Voice Regions")

    print("=" * 40)

    for region in bank[:20]:

        print(
            f"{region['start']}s"
            f" -> "
            f"{region['end']}s"
            f" | "
            f"{region['duration']}s"
        )

    print()

    print(
        f"Total regions: {len(bank)}"
    )

    print()

    print("STATUS: PASS")


if __name__ == "__main__":

    run()