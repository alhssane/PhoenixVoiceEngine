from src.training.singing_style_trainer_v2 import (
    SingingStyleTrainerV2,
)


def run():

    result = (
        SingingStyleTrainerV2()
        .analyze(
            r"F:\مجلد جديد (3)\صولو فريد الجود كلمات بان نور.wav"
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Singing Style Trainer V2"
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