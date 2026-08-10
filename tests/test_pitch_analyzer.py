"""
Phoenix Voice Studio
Pitch Analyzer Test
"""

from pathlib import Path

from src.analyzer.pitch_analyzer import (
    PitchAnalyzer,
)


# ============================================================
# Test Audio
# ============================================================

SOURCE = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)


# ============================================================
# Test
# ============================================================

def test_pitch_analyzer():

    assert SOURCE.exists(), (
        f"Audio file not found:\n{SOURCE}"
    )

    analyzer = PitchAnalyzer()

    report = analyzer.analyze(
        str(SOURCE)
    )

    assert report.duration > 0

    assert report.frame_count > 0

    assert report.voiced_frame_count >= 0

    assert (
        0
        <= report.voiced_coverage
        <= 100
    )

    assert report.min_f0 >= 0

    assert report.max_f0 >= 0

    assert report.mean_f0 >= 0

    assert report.median_f0 >= 0

    assert (
        report.pitch_range_semitones
        >= 0
    )

    assert (
        0
        <= report.pitch_stability
        <= 100
    )

    for frame in report.frames:

        assert frame.time >= 0

        assert frame.f0 >= 0

        assert (
            0
            <= frame.confidence
            <= 1
        )

        assert isinstance(
            frame.voiced,
            bool,
        )

    return report


# ============================================================
# Direct Execution
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("Phoenix Pitch Analyzer")
    print("=" * 70)

    print()
    print("Loading audio...")

    report = test_pitch_analyzer()

    print()
    print("Analysis completed.")
    print("-" * 70)

    print(
        f"File                 : "
        f"{report.file_name}"
    )

    print(
        f"Duration             : "
        f"{report.duration} sec"
    )

    print(
        f"Total Frames         : "
        f"{report.frame_count}"
    )

    print(
        f"Voiced Frames        : "
        f"{report.voiced_frame_count}"
    )

    print(
        f"Voiced Duration      : "
        f"{report.voiced_duration} sec"
    )

    print(
        f"Unvoiced Duration    : "
        f"{report.unvoiced_duration} sec"
    )

    print(
        f"Voiced Coverage      : "
        f"{report.voiced_coverage}%"
    )

    print()

    print("F0 Analysis")
    print("-" * 70)

    print(
        f"Minimum F0           : "
        f"{report.min_f0} Hz"
    )

    print(
        f"Maximum F0           : "
        f"{report.max_f0} Hz"
    )

    print(
        f"Mean F0              : "
        f"{report.mean_f0} Hz"
    )

    print(
        f"Median F0            : "
        f"{report.median_f0} Hz"
    )

    print(
        f"Pitch Range          : "
        f"{report.pitch_range_semitones} semitones"
    )

    print(
        f"Pitch Stability      : "
        f"{report.pitch_stability}/100"
    )

    print()

    print("Sample Pitch Frames")
    print("-" * 70)

    # Show only a limited number of frames.
    # The complete contour remains available in report.frames.

    displayed = 0

    for frame in report.frames:

        if displayed >= 20:
            break

        print(
            f"{frame.time:8.3f}s  "
            f"F0: {frame.f0:8.2f} Hz  "
            f"Confidence: "
            f"{frame.confidence:5.3f}  "
            f"Voiced: "
            f"{frame.voiced}"
        )

        displayed += 1

    print()

    print("STATUS: PASS")

    print("=" * 70)