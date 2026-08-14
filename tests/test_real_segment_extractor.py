from pathlib import Path

from src.analysis.real_segment_extractor import (
    RealSegmentExtractor,
)

AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)

OUTPUT_DIRECTORY = (
    r"D:\PhoenixVoiceEngine\segments"
)


def test_build():

    extractor = (
        RealSegmentExtractor()
    )

    assert (
        extractor.VERSION
        == "1.0.0"
    )


def test_extraction():

    extractor = (
        RealSegmentExtractor()
    )

    segments = (
        extractor.extract(
            AUDIO_FILE,
            OUTPUT_DIRECTORY,
        )
    )

    print()

    print(
        "Segment Extraction"
    )

    print(
        "=" * 40
    )

    print(
        f"Total segments: "
        f"{len(segments)}"
    )

    print()

    for segment in segments:

        print(
            f"{segment['start']}s"
            f" -> "
            f"{segment['end']}s"
            f" | "
            f"{Path(segment['file']).name}"
        )

    assert (
        len(segments)
        > 0
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Real Segment Extractor V1.0"
    )

    print("=" * 60)

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_extraction()

    print(
        "TEST 2: test_extraction - PASS"
    )

    print("=" * 60)

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()