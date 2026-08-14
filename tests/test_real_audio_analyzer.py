from src.analysis.real_audio_analyzer import (
    RealAudioAnalyzer,
)


AUDIO_FILE = (
    r"D:\PhoenixVoiceEngine\samples\fareed_aljood.wav"
)


def test_build():

    analyzer = (
        RealAudioAnalyzer()
    )

    assert (
        analyzer.VERSION
        == "1.0.0"
    )


def test_file_analysis():

    analyzer = (
        RealAudioAnalyzer()
    )

    result = analyzer.analyze(
        AUDIO_FILE
    )

    assert (
        result[
            "sample_rate"
        ]
        > 0
    )


def test_duration():

    analyzer = (
        RealAudioAnalyzer()
    )

    result = analyzer.analyze(
        AUDIO_FILE
    )

    assert (
        result[
            "duration_seconds"
        ]
        > 0
    )


def run():

    tests = [
        obj
        for name, obj in globals().items()
        if name.startswith(
            "test_"
        )
    ]

    print(
        "PhoenixVoiceEngine"
    )

    print(
        "Real Audio Analyzer V1.0"
    )

    print("=" * 60)

    for index, test in enumerate(
        tests,
        1,
    ):

        test()

        print(
            f"TEST {index}: "
            f"{test.__name__} - PASS"
        )

    print("=" * 60)

    print(
        "STATUS: PASS"
    )


if __name__ == "__main__":

    run()