"""
Phoenix Voice Studio
Vocal Activity Analyzer Test
"""

from pathlib import Path

from src.analyzer.vocal_activity_analyzer import (
    VocalActivityAnalyzer,
)


SOURCE = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)


def test_vocal_activity_analyzer():

    assert SOURCE.exists(), (
        f"Audio file not found: {SOURCE}"
    )

    analyzer = VocalActivityAnalyzer()

    report = analyzer.analyze(
        str(SOURCE)
    )

    assert report.total_duration > 0

    assert report.active_duration >= 0

    assert report.silence_duration >= 0

    assert 0 <= report.active_coverage <= 100

    assert report.segment_count >= 0

    for segment in report.segments:

        assert segment.start >= 0

        assert segment.end > segment.start

        assert segment.duration > 0


if __name__ == "__main__":

    report = VocalActivityAnalyzer().analyze(
        str(SOURCE)
    )

    print()
    print("=" * 60)
    print("Phoenix Vocal Activity Analyzer")
    print("=" * 60)

    print(
        f"File              : "
        f"{report.file_name}"
    )

    print(
        f"Total Duration    : "
        f"{report.total_duration} sec"
    )

    print(
        f"Active Duration   : "
        f"{report.active_duration} sec"
    )

    print(
        f"Silence Duration  : "
        f"{report.silence_duration} sec"
    )

    print(
        f"Active Coverage   : "
        f"{report.active_coverage}%"
    )

    print(
        f"Segments          : "
        f"{report.segment_count}"
    )

    print()
    print("Detected Segments")
    print("-" * 60)

    for segment in report.segments:

        print(
            f"{segment.index:02d}  "
            f"{segment.start:08.3f}s -> "
            f"{segment.end:08.3f}s   "
            f"Duration: "
            f"{segment.duration:.3f}s"
        )

    print()
    print(
        f"Threshold         : "
        f"{report.threshold_dbfs} dBFS"
    )

    print(
        f"Min Segment       : "
        f"{report.minimum_segment_duration} sec"
    )

    print(
        f"Min Silence       : "
        f"{report.minimum_silence_duration} sec"
    )

    print()
    print("STATUS: PASS")
    print("=" * 60)