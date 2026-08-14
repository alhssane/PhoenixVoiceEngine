from src.analysis.real_pitch_analyzer import (
    RealPitchAnalyzer,
)


AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    analyzer = (
        RealPitchAnalyzer()
    )

    assert (
        analyzer.VERSION
        == "1.0.0"
    )


def test_pitch_analysis():

    analyzer = (
        RealPitchAnalyzer()
    )

    result = analyzer.analyze(
        AUDIO_FILE
    )

    print()

    print(
        "Pitch Analysis Results"
    )

    print(
        f"Status: "
        f"{result['status']}"
    )

    print(
        f"Minimum Pitch: "
        f"{result['minimum_pitch_hz']} Hz"
    )

    print(
        f"Maximum Pitch: "
        f"{result['maximum_pitch_hz']} Hz"
    )

    print(
        f"Average Pitch: "
        f"{result['average_pitch_hz']} Hz"
    )

    print(
        f"Pitch Samples: "
        f"{result['pitch_samples']}"
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
        "Real Pitch Analyzer V1.0"
    )

    print("=" * 60)

    test_build()

    print(
        "TEST 1: test_build - PASS"
    )

    test_pitch_analysis()

    print()

    print(
        "TEST 2: test_pitch_analysis - PASS"
    )

    print("=" * 60)

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()