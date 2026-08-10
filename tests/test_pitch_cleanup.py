"""
Phoenix Voice Studio
Pitch Cleanup Engine Test Suite

Tests:

1. Real audio
2. Synthetic single-frame octave error
3. Synthetic consecutive octave errors
4. Synthetic pitch spike
5. Synthetic unstable excursion
"""

from dataclasses import dataclass
from pathlib import Path

from src.analyzer.pitch_analyzer import (
    PitchAnalyzer,
)

from src.analyzer.pitch_cleanup import (
    PitchCleanup,
)


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)


# ============================================================
# MOCK DATA
# ============================================================


@dataclass
class MockPitchFrame:

    time: float
    f0: float
    confidence: float
    voiced: bool = True


@dataclass
class MockPitchReport:

    file_name: str
    duration: float
    frames: list


# ============================================================
# HELPERS
# ============================================================


def build_mock_report(
    values,
    file_name,
):

    frames = []

    for index, value in enumerate(
        values
    ):

        frames.append(
            MockPitchFrame(
                time=index * 0.025,
                f0=float(value),
                confidence=0.95,
                voiced=True,
            )
        )

    return MockPitchReport(
        file_name=file_name,
        duration=(
            len(frames)
            * 0.025
        ),
        frames=frames,
    )


def print_corrections(
    report,
):

    corrected = [
        frame
        for frame in report.frames
        if frame.corrected
    ]

    if not corrected:

        print(
            "No corrections."
        )

        return

    for frame in corrected:

        print(
            f"{frame.time:7.3f}s  "
            f"F0: {frame.f0:8.2f} Hz  "
            f"Confidence: "
            f"{frame.confidence:.2f}  "
            f"{frame.correction_type}"
        )


# ============================================================
# TEST 1
# REAL AUDIO
# ============================================================


def test_real_audio():

    assert SOURCE.exists(), (
        f"Audio file not found:\n{SOURCE}"
    )

    analyzer = PitchAnalyzer()

    pitch_report = analyzer.analyze(
        str(SOURCE)
    )

    assert (
        pitch_report.duration
        > 0
    )

    cleaner = PitchCleanup()

    report = cleaner.clean(
        pitch_report
    )

    assert (
        report.original_frames
        > 0
    )

    assert (
        report.cleaned_frames
        == report.original_frames
    )

    assert (
        report.original_voiced_frames
        >= 0
    )

    assert (
        report.cleaned_voiced_frames
        >= 0
    )

    assert (
        report.corrected_frames
        >= 0
    )

    assert (
        0
        <= report.correction_ratio
        <= 100
    )

    return report


# ============================================================
# TEST 2
# SINGLE OCTAVE ERROR
# ============================================================


def create_single_octave_test():

    values = [

        # Stable pitch before error.
        198.0,
        199.0,
        200.0,
        201.0,
        200.0,
        199.0,

        # Artificial octave error.
        400.0,

        # Stable pitch after error.
        201.0,
        200.0,
        199.0,
        200.0,
        201.0,
        200.0,
    ]

    return build_mock_report(
        values,
        "synthetic_single_octave.wav",
    )


def test_single_octave():

    pitch_report = (
        create_single_octave_test()
    )

    cleaner = PitchCleanup(
        context_radius=4,
        minimum_octave_support=3,
    )

    report = cleaner.clean(
        pitch_report
    )

    print()
    print(
        "Single Octave Result"
    )

    print(
        f"Corrected Frames : "
        f"{report.corrected_frames}"
    )

    print(
        f"Octave Corrections : "
        f"{report.octave_corrections}"
    )

    print_corrections(
        report
    )

    assert (
        report.corrected_frames
        > 0
    ), (
        "Single octave error "
        "was not detected."
    )

    assert (
        report.octave_corrections
        > 0
    ), (
        "No octave correction "
        "was detected."
    )

    corrected = [
        frame
        for frame in report.frames
        if frame.corrected
    ]

    assert corrected

    for frame in corrected:

        assert (
            170.0
            <= frame.f0
            <= 230.0
        )

    return report


# ============================================================
# TEST 3
# CONSECUTIVE OCTAVE ERRORS
# ============================================================


def create_consecutive_octave_test():

    values = [

        # Clean region.
        198.0,
        199.0,
        200.0,
        201.0,
        200.0,
        199.0,
        200.0,

        # Artificial octave region.
        400.0,
        402.0,
        398.0,

        # Clean region.
        201.0,
        200.0,
        199.0,
        200.0,
        201.0,
        200.0,
        199.0,
    ]

    return build_mock_report(
        values,
        "synthetic_consecutive_octave.wav",
    )


def test_consecutive_octave():

    pitch_report = (
        create_consecutive_octave_test()
    )

    cleaner = PitchCleanup(
        context_radius=4,
        minimum_octave_support=3,
    )

    report = cleaner.clean(
        pitch_report
    )

    print()
    print(
        "Consecutive Octave Result"
    )

    print(
        f"Corrected Frames : "
        f"{report.corrected_frames}"
    )

    print(
        f"Octave Corrections : "
        f"{report.octave_corrections}"
    )

    print_corrections(
        report
    )

    assert (
        report.corrected_frames
        > 0
    ), (
        "Consecutive octave "
        "errors were not detected."
    )

    assert (
        report.octave_corrections
        > 0
    ), (
        "No consecutive octave "
        "corrections detected."
    )

    corrected = [
        frame
        for frame in report.frames
        if frame.corrected
    ]

    assert corrected

    # At least one of the three
    # erroneous frames must be corrected.
    assert (
        len(corrected)
        >= 1
    )

    for frame in corrected:

        assert (
            170.0
            <= frame.f0
            <= 230.0
        )

    return report


# ============================================================
# TEST 4
# SYNTHETIC PITCH SPIKE
# ============================================================


def create_spike_test():

    values = [

        198.0,
        199.0,
        200.0,
        201.0,
        200.0,

        # Artificial spike.
        310.0,

        201.0,
        200.0,
        199.0,
        200.0,
        201.0,
    ]

    return build_mock_report(
        values,
        "synthetic_spike.wav",
    )


def test_synthetic_spike():

    pitch_report = (
        create_spike_test()
    )

    cleaner = PitchCleanup(
        context_radius=4,
    )

    report = cleaner.clean(
        pitch_report
    )

    print()
    print(
        "Pitch Spike Result"
    )

    print(
        f"Corrected Frames : "
        f"{report.corrected_frames}"
    )

    print(
        f"Spike Corrections : "
        f"{report.spike_corrections}"
    )

    print_corrections(
        report
    )

    assert (
        report.corrected_frames
        > 0
    ), (
        "Pitch spike was "
        "not detected."
    )

    assert (
        report.spike_corrections
        > 0
    ), (
        "No spike correction "
        "was detected."
    )

    corrected = [
        frame
        for frame in report.frames
        if frame.corrected
    ]

    assert corrected

    for frame in corrected:

        assert (
            160.0
            <= frame.f0
            <= 240.0
        )

    return report


# ============================================================
# TEST 5
# SYNTHETIC UNSTABLE EXCURSION
# ============================================================


def create_unstable_test():

    values = [

        198.0,
        199.0,
        200.0,

        # Sudden excursion.
        200.0,
        430.0,
        200.0,

        201.0,
        200.0,
        199.0,
    ]

    return build_mock_report(
        values,
        "synthetic_unstable.wav",
    )


def test_unstable_excursion():

    pitch_report = (
        create_unstable_test()
    )

    cleaner = PitchCleanup(
        context_radius=4,
    )

    report = cleaner.clean(
        pitch_report
    )

    print()
    print(
        "Unstable Excursion Result"
    )

    print(
        f"Corrected Frames : "
        f"{report.corrected_frames}"
    )

    print(
        f"Unstable Corrections : "
        f"{report.unstable_corrections}"
    )

    print_corrections(
        report
    )

    # The engine may classify this as
    # octave, spike, or unstable depending
    # on which detector has the strongest
    # evidence.

    assert (
        report.corrected_frames
        > 0
    ), (
        "Unstable pitch excursion "
        "was not detected."
    )

    corrected = [
        frame
        for frame in report.frames
        if frame.corrected
    ]

    assert corrected

    return report


# ============================================================
# MAIN
# ============================================================


if __name__ == "__main__":

    print()
    print("=" * 70)
    print(
        "Phoenix Pitch Cleanup Engine"
    )
    print("=" * 70)

    # ========================================================
    # REAL AUDIO
    # ========================================================

    print()
    print(
        "TEST 1: Real Audio"
    )
    print("-" * 70)

    real_report = (
        test_real_audio()
    )

    print(
        f"File                  : "
        f"{real_report.file_name}"
    )

    print(
        f"Original Frames       : "
        f"{real_report.original_frames}"
    )

    print(
        f"Original Voiced       : "
        f"{real_report.original_voiced_frames}"
    )

    print(
        f"Corrected Frames      : "
        f"{real_report.corrected_frames}"
    )

    print(
        f"Octave Corrections    : "
        f"{real_report.octave_corrections}"
    )

    print(
        f"Spike Corrections     : "
        f"{real_report.spike_corrections}"
    )

    print(
        f"Unstable Corrections  : "
        f"{real_report.unstable_corrections}"
    )

    print(
        f"Correction Ratio      : "
        f"{real_report.correction_ratio}%"
    )

    print(
        f"Status                : "
        f"{real_report.status}"
    )

    print()
    print(
        "Real Audio Corrections"
    )
    print("-" * 70)

    print_corrections(
        real_report
    )

    # ========================================================
    # SINGLE OCTAVE
    # ========================================================

    print()
    print("=" * 70)
    print(
        "TEST 2: Single Octave Error"
    )
    print("=" * 70)

    single_octave_report = (
        test_single_octave()
    )

    print(
        f"STATUS: "
        f"{single_octave_report.status}"
    )

    # ========================================================
    # CONSECUTIVE OCTAVE
    # ========================================================

    print()
    print("=" * 70)
    print(
        "TEST 3: Consecutive Octave Errors"
    )
    print("=" * 70)

    consecutive_report = (
        test_consecutive_octave()
    )

    print(
        f"STATUS: "
        f"{consecutive_report.status}"
    )

    # ========================================================
    # SPIKE
    # ========================================================

    print()
    print("=" * 70)
    print(
        "TEST 4: Synthetic Pitch Spike"
    )
    print("=" * 70)

    spike_report = (
        test_synthetic_spike()
    )

    print(
        f"STATUS: "
        f"{spike_report.status}"
    )

    # ========================================================
    # UNSTABLE
    # ========================================================

    print()
    print("=" * 70)
    print(
        "TEST 5: Synthetic Unstable Excursion"
    )
    print("=" * 70)

    unstable_report = (
        test_unstable_excursion()
    )

    print(
        f"STATUS: "
        f"{unstable_report.status}"
    )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 70)
    print(
        "ALL PITCH CLEANUP TESTS: PASS"
    )
    print("=" * 70)