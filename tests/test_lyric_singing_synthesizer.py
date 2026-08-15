from src.synthesis.lyric_singing_synthesizer import (
    LyricSingingSynthesizer
)

PROFILE = (
    r"D:\PhoenixVoiceEngine\workspace"
    r"\artist_profiles"
    r"\fareed_profile.json"
)


def run():

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Lyric Singing Synthesizer V1.0"
    )

    print(
        "=" * 60
    )

    result = (
        LyricSingingSynthesizer()
        .synthesize(
            PROFILE,
            "سعادة",
            "فرح",
            0.96,
        )
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