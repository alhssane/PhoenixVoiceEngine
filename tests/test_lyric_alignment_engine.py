from src.analysis.lyric_alignment_engine import (
    LyricAlignmentEngine,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    engine = (
        LyricAlignmentEngine()
    )

    assert (
        engine.VERSION
        == "1.0.0"
    )


def test_analysis():

    results = (
        LyricAlignmentEngine()
        .analyze(AUDIO_FILE)
    )

    print()

    print(
        "Lyric Alignment"
    )

    print(
        "=" * 40
    )

    for item in results[:20]:

        print(
            f"{item['start']}s -> "
            f"{item['end']}s | "
            f"{item['maqam']} | "
            f"{len(item['notes'])} notes"
        )

    assert len(results) > 0


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Lyric Alignment Engine V1.0"
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