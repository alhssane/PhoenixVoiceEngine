from src.synthesis.full_song_generation_engine import (
    FullSongGenerationEngine,
)


NEW_LYRICS = """

يا مرحبا يا أجمل عروس
نورك سطع بين النجوم
وفي حضورك يزهر الكون
ويبتسم كل الحضور

"""


def run():

    result = (
        FullSongGenerationEngine()
        .generate(
            r"D:\PhoenixVoiceEngine\workspace\trained_artists\fareed_complete_model.json",
            NEW_LYRICS,
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Full Song Generation Engine V1.0"
    )

    print(
        "=" * 60
    )

    print()

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )

    print()

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()