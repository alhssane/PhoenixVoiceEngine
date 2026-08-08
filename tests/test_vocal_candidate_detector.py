"""
Phoenix Voice Studio
Vocal Candidate Detector Test
"""

from pathlib import Path

from src.analyzer.vocal_activity_analyzer import (
    VocalActivityAnalyzer,
)

from src.analyzer.vocal_candidate_detector import (
    VocalCandidateDetector,
)


# ============================================================
# Test audio
# ============================================================

SOURCE = Path(
    r"F:\من بروتوز\مجلد جديد (2)\يامسهره مقطع.wav"
)


def test_vocal_candidate_detector():

    assert SOURCE.exists(), (
        f"Audio file not found:\n{SOURCE}"
    )

    activity_analyzer = VocalActivityAnalyzer()

    activity_report = activity_analyzer.analyze(
        str(SOURCE)
    )

    detector = VocalCandidateDetector()

    report = detector.analyze(
        str(SOURCE),
        activity_report.segments,
    )

    assert report.total_duration > 0

    assert report.candidate_count >= 0

    assert report.high_confidence_duration >= 0

    assert report.medium_confidence_duration >= 0

    assert (
        0
        <= report.high_confidence_coverage
        <= 100
    )

    assert (
        0
        <= report.medium_confidence_coverage
        <= 100
    )

    for candidate in report.candidates:

        assert candidate.end > candidate.start

        assert candidate.duration > 0

        assert (
            0
            <= candidate.confidence
            <= 100
        )

        assert candidate.classification in {
            "HIGH_CONFIDENCE",
            "MEDIUM_CONFIDENCE",
            "LOW_CONFIDENCE",
        }

    return report


# ============================================================
# Direct execution
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("Phoenix Vocal Candidate Detector")
    print("=" * 70)

    print()
    print("Loading audio...")

    report = test_vocal_candidate_detector()

    print()
    print("Analysis completed.")
    print("-" * 70)

    print(
        f"File                 : "
        f"{report.file_name}"
    )

    print(
        f"Total Duration       : "
        f"{report.total_duration} sec"
    )

    print(
        f"Candidate Segments   : "
        f"{report.candidate_count}"
    )

    print(
        f"High Confidence      : "
        f"{report.high_confidence_duration} sec"
    )

    print(
        f"Medium/High Duration : "
        f"{report.medium_confidence_duration} sec"
    )

    print(
        f"High Coverage        : "
        f"{report.high_confidence_coverage}%"
    )

    print(
        f"Medium+ Coverage     : "
        f"{report.medium_confidence_coverage}%"
    )

    print()
    print("Candidate Segments")
    print("-" * 70)

    for candidate in report.candidates:

        print(
            f"{candidate.index:02d}  "
            f"{candidate.start:08.3f}s -> "
            f"{candidate.end:08.3f}s  "
            f"Duration: {candidate.duration:7.3f}s  "
            f"Confidence: "
            f"{candidate.confidence:5.1f}%  "
            f"{candidate.classification}"
        )

    print()
    print("STATUS: PASS")
    print("=" * 70)