from src.analysis.real_tonic_analyzer import (
    RealTonicAnalyzer,
)


AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    analyzer = (
        RealTonicAnalyzer()
    )

    assert (
        analyzer.VERSION
        == "1.0.0"
    )


def test_tonic_analysis():

    analyzer = (
        RealTonicAnalyzer()
    )

    result = analyzer.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "Tonic Analysis Results"
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )

    assert (
        result["status"]
        == "SUCCESS"
    )


def run():

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Real Tonic Analyzer V1.0"
    )

    print("=" * 60)

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_tonic_analysis()

    print()

    print(
        "TEST 2: test_tonic_analysis - PASS"
    )

    print("=" * 60)

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()