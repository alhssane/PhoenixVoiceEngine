from src.analysis.melisma_detection_engine import (
    MelismaDetectionEngine,
)

from src.analysis.ornament_classification_engine import (
    OrnamentClassificationEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        OrnamentClassificationEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    melismas = (
        MelismaDetectionEngine()
        .analyze(AUDIO_FILE)
    )

    classifier = (
        OrnamentClassificationEngine()
    )

    print()

    print(
        "Ornament Analysis"
    )

    print(
        "=" * 40
    )

    for index, melisma in enumerate(
        melismas[:15]
    ):

        notes = [
            item["note"]
            for item in melisma
        ]

        start = round(
            melisma[0]["time"],
            2,
        )

        end = round(
            melisma[-1]["time"],
            2,
        )

        ornament = (
            classifier.classify(
                notes
            )
        )

        print(
            f"{start}s -> {end}s | "
            f"{ornament} | "
            f"{notes}"
        )

    assert (
        len(melismas)
        > 0
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Ornament Classification Engine V1.0"
    )

    print(
        "=" * 60
    )

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_analysis()

    print(
        "TEST 2: test_analysis - PASS"
    )

    print(
        "=" * 60
    )

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()