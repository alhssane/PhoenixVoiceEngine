from src.training.vocal_dataset_builder import (
    VocalDatasetBuilder,
)


def run():

    result = (
        VocalDatasetBuilder()
        .analyze(
            r"F:\مجلد جديد (3)\صولو فريد الجود كلمات بان نور.wav"
        )
    )

    print()

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Vocal Dataset Builder V1.0"
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