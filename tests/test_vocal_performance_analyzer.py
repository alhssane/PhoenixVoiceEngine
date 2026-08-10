"""
Phoenix Voice Studio
Vocal Performance Analyzer Test
"""

from pathlib import Path

from src.analyzer.vocal_performance_analyzer import (
    VocalPerformanceAnalyzer,
)


# ============================================================
# TEST AUDIO
# ============================================================

SOURCE = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)


# ============================================================
# TEST
# ============================================================

def test_vocal_performance_analyzer():

    # --------------------------------------------------------
    # Verify source audio
    # --------------------------------------------------------

    assert SOURCE.exists(), (
        f"Audio file not found:\n{SOURCE}"
    )

    assert SOURCE.is_file(), (
        f"Audio path is not a file:\n{SOURCE}"
    )

    # --------------------------------------------------------
    # Create analyzer
    # --------------------------------------------------------

    analyzer = (
        VocalPerformanceAnalyzer()
    )

    # --------------------------------------------------------
    # Analyze audio
    # --------------------------------------------------------

    report = analyzer.analyze(
        str(SOURCE)
    )

    # ========================================================
    # BASIC REPORT VALIDATION
    # ========================================================

    assert report.file_name == SOURCE.name

    assert report.duration > 0

    assert (
        report.voiced_duration >= 0
    )

    assert (
        report.voiced_duration
        <= report.duration
    )

    assert (
        0
        <= report.voiced_coverage
        <= 100
    )

    # ========================================================
    # PITCH VALIDATION
    # ========================================================

    assert (
        report.pitch_center_hz
        >= 0
    )

    assert (
        report.pitch_center_midi
        >= 0
    )

    assert (
        report.pitch_min_hz
        >= 0
    )

    assert (
        report.pitch_max_hz
        >= 0
    )

    assert (
        report.pitch_max_hz
        >= report.pitch_min_hz
    )

    assert (
        report.pitch_range_semitones
        >= 0
    )

    assert (
        0
        <= report.pitch_stability
        <= 100
    )

    assert (
        0
        <= report.average_confidence
        <= 100
    )

    # ========================================================
    # MOVEMENT VALIDATION
    # ========================================================

    assert (
        report.pitch_movement_count
        >= 0
    )

    assert (
        report.upward_movements
        >= 0
    )

    assert (
        report.downward_movements
        >= 0
    )

    assert (
        report.upward_movements
        + report.downward_movements
        == report.pitch_movement_count
    )

    # ========================================================
    # TRANSITION VALIDATION
    # ========================================================

    for transition in report.transitions:

        assert (
            transition.start_time
            >= 0
        )

        assert (
            transition.end_time
            >= transition.start_time
        )

        assert (
            transition.duration
            >= 0
        )

        assert (
            transition.start_f0
            > 0
        )

        assert (
            transition.end_f0
            > 0
        )

        assert (
            abs(
                transition.semitone_change
            )
            >= 0
        )

        assert transition.direction in {
            "UP",
            "DOWN",
        }

        assert (
            0
            <= transition.confidence
            <= 100
        )

    # ========================================================
    # STABLE REGION VALIDATION
    # ========================================================

    assert isinstance(
        report.stable_regions,
        list,
    )

    for region in report.stable_regions:

        assert (
            region.start_time
            >= 0
        )

        assert (
            region.end_time
            >= region.start_time
        )

        assert (
            region.duration
            >= 0
        )

        assert (
            region.mean_f0
            > 0
        )

        assert (
            region.median_f0
            > 0
        )

        assert (
            region.min_f0
            > 0
        )

        assert (
            region.max_f0
            >= region.min_f0
        )

        assert (
            region.variation_semitones
            >= 0
        )

        assert (
            0
            <= region.confidence
            <= 100
        )

    # ========================================================
    # VIBRATO VALIDATION
    # ========================================================

    vibrato = report.vibrato

    assert isinstance(
        vibrato.detected,
        bool,
    )

    assert (
        vibrato.rate_hz
        >= 0
    )

    assert (
        vibrato.depth_semitones
        >= 0
    )

    assert (
        vibrato.duration
        >= 0
    )

    assert (
        0
        <= vibrato.coverage
        <= 100
    )

    assert (
        0
        <= vibrato.confidence
        <= 100
    )

    # --------------------------------------------------------
    # Important consistency rule:
    #
    # If vibrato is NOT detected, the confidence must be zero.
    # --------------------------------------------------------

    if not vibrato.detected:

        assert (
            vibrato.rate_hz
            == 0
        )

        assert (
            vibrato.depth_semitones
            == 0
        )

        assert (
            vibrato.duration
            == 0
        )

        assert (
            vibrato.coverage
            == 0
        )

        assert (
            vibrato.confidence
            == 0
        )

    else:

        assert (
            vibrato.rate_hz
            > 0
        )

        assert (
            vibrato.depth_semitones
            > 0
        )

        assert (
            vibrato.duration
            > 0
        )

        assert (
            vibrato.coverage
            > 0
        )

        assert (
            vibrato.confidence
            > 0
        )

    # ========================================================
    # PERFORMANCE SCORE
    # ========================================================

    assert (
        0
        <= report.performance_score
        <= 100
    )

    assert report.status in {
        "EXCELLENT",
        "GOOD",
        "ACCEPTABLE",
        "NEEDS_REVIEW",
    }

    return report


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("Phoenix Vocal Performance Analyzer")
    print("=" * 70)

    print()
    print("Loading audio...")

    report = (
        test_vocal_performance_analyzer()
    )

    print()
    print("## Analysis completed.")

    print()
    print("=" * 70)
    print("General")
    print("=" * 70)

    print(
        f"File                  : "
        f"{report.file_name}"
    )

    print(
        f"Duration              : "
        f"{report.duration} sec"
    )

    print(
        f"Voiced Duration       : "
        f"{report.voiced_duration} sec"
    )

    print(
        f"Voiced Coverage       : "
        f"{report.voiced_coverage}%"
    )

    # ========================================================
    # PITCH
    # ========================================================

    print()
    print("=" * 70)
    print("Pitch")
    print("=" * 70)

    print(
        f"Pitch Center           : "
        f"{report.pitch_center_hz} Hz"
    )

    print(
        f"Pitch Center           : "
        f"{report.pitch_center_midi} MIDI"
    )

    print(
        f"Pitch Minimum          : "
        f"{report.pitch_min_hz} Hz"
    )

    print(
        f"Pitch Maximum          : "
        f"{report.pitch_max_hz} Hz"
    )

    print(
        f"Pitch Range            : "
        f"{report.pitch_range_semitones} semitones"
    )

    print(
        f"Pitch Stability        : "
        f"{report.pitch_stability}/100"
    )

    print(
        f"Average Confidence     : "
        f"{report.average_confidence}%"
    )

    # ========================================================
    # PITCH MOVEMENTS
    # ========================================================

    print()
    print("=" * 70)
    print("Pitch Movement")
    print("=" * 70)

    print(
        f"Total Movements        : "
        f"{report.pitch_movement_count}"
    )

    print(
        f"Upward Movements       : "
        f"{report.upward_movements}"
    )

    print(
        f"Downward Movements     : "
        f"{report.downward_movements}"
    )

    # ========================================================
    # TRANSITIONS
    # ========================================================

    print()
    print("## Confirmed Pitch Transitions")
    print("-" * 70)

    if report.transitions:

        for transition in report.transitions[:20]:

            print(
                f"{transition.start_time:8.3f}s -> "
                f"{transition.end_time:8.3f}s  "
                f"{transition.start_f0:7.2f} Hz -> "
                f"{transition.end_f0:7.2f} Hz  "
                f"{transition.semitone_change:+6.2f} st  "
                f"{transition.direction:<5}  "
                f"Confidence: "
                f"{transition.confidence:5.1f}%"
            )

    else:

        print(
            "No confirmed pitch transitions."
        )

    # ========================================================
    # STABLE PITCH REGIONS
    # ========================================================

    print()
    print("## Stable Pitch Regions")
    print("-" * 70)

    print(
        f"Stable Regions         : "
        f"{len(report.stable_regions)}"
    )

    for region in report.stable_regions[:20]:

        print(
            f"{region.start_time:8.3f}s -> "
            f"{region.end_time:8.3f}s  "
            f"Duration: "
            f"{region.duration:6.3f}s  "
            f"Pitch: "
            f"{region.median_f0:7.2f} Hz  "
            f"Variation: "
            f"{region.variation_semitones:5.2f} st  "
            f"Confidence: "
            f"{region.confidence:5.1f}%"
        )

    # ========================================================
    # VIBRATO
    # ========================================================

    print()
    print("=" * 70)
    print("Vibrato")
    print("=" * 70)

    print(
        f"Detected               : "
        f"{report.vibrato.detected}"
    )

    print(
        f"Rate                   : "
        f"{report.vibrato.rate_hz} Hz"
    )

    print(
        f"Depth                  : "
        f"{report.vibrato.depth_semitones} semitones"
    )

    print(
        f"Duration               : "
        f"{report.vibrato.duration} sec"
    )

    print(
        f"Coverage               : "
        f"{report.vibrato.coverage}%"
    )

    print(
        f"Confidence             : "
        f"{report.vibrato.confidence}%"
    )

    # ========================================================
    # PERFORMANCE
    # ========================================================

    print()
    print("=" * 70)
    print("Performance Analysis")
    print("=" * 70)

    print(
        f"Performance Score      : "
        f"{report.performance_score}/100"
    )

    print(
        f"Status                 : "
        f"{report.status}"
    )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 70)
    print("STATUS: PASS")
    print("=" * 70)