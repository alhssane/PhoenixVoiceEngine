from src.analysis.real_segment_quarter_tone_analyzer import (
    RealSegmentQuarterToneAnalyzer,
)


SEGMENTS_DIRECTORY = (
    r"D:\PhoenixVoiceEngine\segments"
)


def test_build():

    analyzer = (
        RealSegmentQuarterToneAnalyzer()
    )

    assert (
        analyzer.VERSION
        == "1.0.0"
    )


def test_analysis():

    analyzer = (
        RealSegmentQuarterToneAnalyzer()
    )

    results = analyzer.analyze(
        SEGMENTS_DIRECTORY
    )

    print()

    print(
        "Segment Quarter-Tone Analysis"
    )

    print(
        "=" * 40
    )

    for result in results:

        print(
            f"{result['file']} | "
            f"{result['quarter_tones']} "
            f"quarter tones | "
            f"{result['percentage']}%"
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
        "Real Segment Quarter-Tone Analyzer V1.0"
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