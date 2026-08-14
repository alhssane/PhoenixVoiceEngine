from src.analysis.real_segment_pitch_analyzer import (
    RealSegmentPitchAnalyzer,
)

SEGMENTS_DIRECTORY = (
    r"D:\PhoenixVoiceEngine\segments"
)


def test_build():

    analyzer = (
        RealSegmentPitchAnalyzer()
    )

    assert (
        analyzer.VERSION
        == "1.0.0"
    )


def test_analysis():

    analyzer = (
        RealSegmentPitchAnalyzer()
    )

    results = analyzer.analyze(
        SEGMENTS_DIRECTORY
    )

    print()

    print(
        "Segment Pitch Analysis"
    )

    print(
        "=" * 40
    )

    for result in results:

        print(
            f"{result['file']}"
            f" | "
            f"{result['average_pitch']} Hz"
            f" | "
            f"{result['samples']} samples"
        )

    assert (
        len(results)
        > 0
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Real Segment Pitch Analyzer V1.0"
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